from django import forms
from django.db import models
from django.db.models.fields.related import ManyToManyField, OneToOneRel
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import TemplateView, FormView
from django.contrib.admin.utils import quote, unquote
from django.contrib.auth.decorators import login_required
from django.views.generic.list import MultipleObjectMixin, MultipleObjectTemplateResponseMixin
from django_filters.views import FilterMixin

from . import messages


class SiteBaseView(TemplateView):
    """
    Groups together common functionality for all app views.
    """
    modelsite = None
    meta_title = ''
    page_title = ''
    page_subtitle = ''

    def __init__(self, modelsite, **kwargs):
        self.modelsite = modelsite
        self.model = modelsite.model
        self.opts = self.model._meta
        self.app_label = force_str(self.opts.app_label)
        self.model_name = force_str(self.opts.model_name)
        self.verbose_name = force_str(self.opts.verbose_name)
        self.verbose_name_plural = force_str(self.opts.verbose_name_plural)
        self.pk_attname = self.opts.pk.attname
        self.permission_helper = modelsite.permission_helper
        self.url_helper = modelsite.url_helper
        super().__init__(**kwargs)

    def check_action_permitted(self, user):
        return True

    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted(request.user):
            raise PermissionDenied
        button_helper_class = self.modelsite.get_button_helper_class()
        self.button_helper = button_helper_class(self, request)
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def menu_icon(self):
        return self.modelsite.get_menu_icon()

    @cached_property
    def header_icon(self):
        return self.menu_icon

    def get_page_title(self):
        return self.page_title or capfirst(self.opts.verbose_name_plural)

    def get_page_subtitle(self):
        return self.page_subtitle

    def get_meta_title(self):
        return self.meta_title or self.get_page_title()

    @cached_property
    def index_url(self):
        return self.url_helper.index_url

    @cached_property
    def create_url(self):
        return self.url_helper.create_url

    def get_base_queryset(self, request=None):
        return self.modelsite.get_queryset(request or self.request)

    def get_context_data(self, **kwargs):
        context = {
            'view': self,
            'opts': self.opts,
            'modelsite': self.modelsite,
            'page_title': self.get_page_title(),
            'page_subtitle': self.get_page_subtitle(),
            'meta_title': self.get_meta_title(),
        }
        context.update(**kwargs)
        return super().get_context_data(**context)


class ModelFormView(SiteBaseView, FormView):

    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_fields(self):
        return (
                self.modelsite.get_fields()
                or [field.name for field in self.model._meta.get_fields()]
        )

    def get_form_class(self):
        """Return the form class to use in this view."""
        if self.form_class:
            return self.form_class
        else:
            model = self.model
            fields = self.get_fields()
            return forms.modelform_factory(model, fields=fields)

    def get_success_url(self):
        return self.modelsite.get_success_url() or self.index_url

    def get_instance(self):
        return getattr(self, 'instance', None) or self.model()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': self.get_instance()})
        return kwargs

    @property
    def media(self):
        return forms.Media(
            css={'all': self.modelsite.get_form_view_extra_css()},
            js=self.modelsite.get_form_view_extra_js()
        )

    def get_context_data(self, **kwargs):
        form = self.get_form()
        context = {
            'is_multipart': form.is_multipart(),
            'form': form,
        }
        context.update(kwargs)
        return super().get_context_data(**context)

    def get_success_message(self, instance):
        return _("%(model_name)s '%(instance)s' created.") % {
            'model_name': capfirst(self.opts.verbose_name), 'instance': instance
        }

    def get_success_message_buttons(self, instance):
        button_url = self.url_helper.get_url('edit', True, instance.pk)
        return [
            messages.button(button_url, _('Edit'))
        ]

    def get_error_message(self):
        model_name = self.verbose_name
        return _("The %s could not be created due to errors.") % model_name

    def form_valid(self, form):
        instance = form.save()
        messages.success(
            self.request, self.get_success_message(instance),
            buttons=self.get_success_message_buttons(instance)
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.validation_error(
            self.request, self.get_error_message(), form
        )
        return self.render_to_response(self.get_context_data())


class InstanceSpecificView(SiteBaseView):
    instance_pk = None
    pk_quoted = None
    instance = None

    def __init__(self, modelsite, instance_pk):
        super().__init__(modelsite)
        self.instance_pk = unquote(instance_pk)
        self.pk_quoted = quote(self.instance_pk)
        filter_kwargs = dict()
        filter_kwargs[self.pk_attname] = self.instance_pk
        object_qs = modelsite.model._default_manager.get_queryset().filter(**filter_kwargs)
        self.instance = get_object_or_404(object_qs)

    def get_page_title(self):
        return (
                self.modelsite.inspect_page_title
                or "%s %s" % (self.page_title, self.opts.verbose_name)
        )

    def get_page_subtitle(self):
        return self.instance

    @cached_property
    def edit_url(self):
        return self.url_helper.get_url('edit', True, self.pk_quoted)

    @cached_property
    def delete_url(self):
        return self.url_helper.get_url('delete', True, self.pk_quoted)

    def get_context_data(self, **kwargs):
        context = {
            'instance': self.instance
        }
        context.update(kwargs)
        return super().get_context_data(**context)


class IndexView(MultipleObjectTemplateResponseMixin, FilterMixin, MultipleObjectMixin, SiteBaseView):
    page_title = _('All')
    paginate_by = 12

    def get_queryset(self):
        if self.modelsite.get_queryset(self.request):
            return self.modelsite.get_queryset(self.request)
        return super(IndexView, self).get_queryset()

    def check_action_permitted(self, user):
        if self.modelsite.index_view_is_public:
            return True
        return self.permission_helper.user_can_list(user)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted(request.user):
            raise PermissionDenied
        self.select_related = self.modelsite.select_related
        self.filterset_fields = self.modelsite.filterset_fields
        return super().dispatch(request, *args, **kwargs)

    @property
    def media(self):
        return forms.Media(
            css={'all': self.modelsite.get_index_view_extra_css()},
            js=self.modelsite.get_index_view_extra_js()
        )

    def get_page_title(self):
        return (
                self.modelsite.create_page_title
                or "%s %s" % (self.page_title, self.opts.verbose_name_plural)
        )

    def get_buttons_for_obj(self, obj):
        return self.button_helper.get_buttons_for_obj(
            obj, classnames_add=['button-small', 'button-secondary'])

    def get_paginate_by(self, queryset):
        if self.modelsite.list_per_page:
            return self.modelsite.list_per_page
        return self.paginate_by

    def get_ordering(self):
        if self.modelsite.ordering:
            return self.modelsite.ordering
        return self.ordering

    def apply_select_related(self, qs):

        if self.select_related is True:
            qs = qs.select_related()
        if self.select_related:
            qs = qs.select_related(*self.select_related)

        return qs

    def get_context_data(self, **kwargs):
        user = self.request.user
        all_count = self.get_base_queryset().count()
        queryset = self.get_queryset()
        result_count = queryset.count()
        context = {
            'view': self,
            'all_count': all_count,
            'result_count': result_count,
            'user_can_create': self.permission_helper.user_can_create(user),
        }
        context.update(kwargs)
        return super().get_context_data(**context)

    def get_template_names(self):
        if self.template_name:
            return [self.template_name]
        return self.modelsite.get_index_template()

    def get_filterset_class(self):
        """
        Returns the filterset class to use in this view
        """
        if self.modelsite.filterset_class:
            return self.modelsite.filterset_class
        return super().get_filterset_class()

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.apply_select_related(self.filterset.qs)
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)
        return self.render_to_response(context)


class InspectView(InstanceSpecificView):
    page_title = _('Inspecting')

    def check_action_permitted(self, user):
        if self.modelsite.inspect_view_is_public:
            return True
        return self.permission_helper.user_can_inspect_obj(user, self.instance)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(InspectView, self).dispatch(request, *args, **kwargs)

    @property
    def media(self):
        return forms.Media(
            css={'all': self.modelsite.get_inspect_view_extra_css()},
            js=self.modelsite.get_inspect_view_extra_js()
        )

    def get_context_data(self, **kwargs):
        context = {
            'buttons': self.button_helper.get_buttons_for_obj(
                self.instance, exclude=['inspect']),
        }
        context.update(kwargs)
        return super().get_context_data(**context)

    def get_page_title(self):
        return "{} {}".format(self.page_title, self.instance)

    def get_template_names(self):
        if self.template_name:
            return [self.template_name]
        return self.modelsite.get_inspect_template()


class CreateView(ModelFormView):
    page_title = _('New')

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_create(user)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_meta_title(self):
        return _('Create new %s') % self.verbose_name

    def get_page_title(self):
        return "{} {}".format(self.page_title, self.opts.verbose_name)

    def get_page_subtitle(self):
        return capfirst(self.verbose_name)

    def get_template_names(self):
        if self.template_name:
            return [self.template_name]
        return self.modelsite.get_create_template()


class EditView(ModelFormView, InstanceSpecificView):
    page_title = _('Editing')

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_edit_obj(user, self.instance)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_page_title(self):
        return "{} {}".format(self.page_title, self.opts.verbose_name)

    def get_meta_title(self):
        return _('Editing %s') % self.verbose_name

    def get_success_message(self, instance):
        return _("%(model_name)s '%(instance)s' updated.") % {
            'model_name': capfirst(self.verbose_name), 'instance': instance
        }

    def get_context_data(self, **kwargs):
        context = {
            'user_can_edit': self.permission_helper.user_can_edit_obj(
                self.request.user, self.instance)
        }
        context.update(kwargs)
        return super().get_context_data(**context)

    def get_error_message(self):
        name = self.verbose_name
        return _("The %s could not be saved due to errors.") % name

    def get_template_names(self):
        if self.template_name:
            return [self.template_name]
        return self.modelsite.get_edit_template()


class DeleteView(InstanceSpecificView):
    page_title = _('Delete')

    def get_success_url(self):
        return self.modelsite.get_success_url() or self.index_url

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_delete_obj(user, self.instance)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_meta_title(self):
        return _('Confirm deletion of %s') % self.verbose_name

    def confirmation_message(self):
        return _(
            "Are you sure you want to delete this %s? If other things in your "
            "site are related to it, they may also be affected."
        ) % self.verbose_name

    def delete_instance(self):
        self.instance.delete()

    def post(self, request, *args, **kwargs):
        try:
            msg = _("%(model_name)s '%(instance)s' deleted.") % {
                'model_name': self.verbose_name, 'instance': self.instance
            }
            self.delete_instance()
            messages.success(request, msg.title())
            return redirect(self.get_success_url())
        except models.ProtectedError:
            linked_objects = []
            fields = self.model._meta.fields_map.values()
            fields = (obj for obj in fields if not isinstance(
                obj.field, ManyToManyField))
            for rel in fields:
                if rel.on_delete == models.PROTECT:
                    if isinstance(rel, OneToOneRel):
                        try:
                            obj = getattr(self.instance, rel.get_accessor_name())
                        except ObjectDoesNotExist:
                            pass
                        else:
                            linked_objects.append(obj)
                    else:
                        qs = getattr(self.instance, rel.get_accessor_name())
                        for obj in qs.all():
                            linked_objects.append(obj)
            context = self.get_context_data(
                protected_error=True,
                linked_objects=linked_objects
            )
            return self.render_to_response(context)

    def get_template_names(self):
        if self.template_name:
            return [self.template_name]
        return self.modelsite.get_delete_template()


def handler403(request):
    return render(request, '403.html', status=403)
