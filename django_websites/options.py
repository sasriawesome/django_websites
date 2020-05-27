from django.db.models import Model
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.conf.urls import url, include

from .helpers import SitePermissionHelper, ButtonHelper, SiteURLHelper
from .filters import custom_filterset_factory
from .views import IndexView, CreateView, InspectView, EditView, DeleteView

WEBSITE_LIST_PER_PAGE = getattr(settings, 'WEBSITE_LIST_PER_PAGE', 15)


class ModelSite:
    model = None
    namespace = None
    menu_icon = ''
    menu_label = ''
    select_related = None

    # Index Display
    ordering = ['id']
    list_display = []
    list_per_page = None
    filterset_fields = None
    filterset_class = None

    # Form
    fields = []
    form_class = None

    # View
    index_page_title = None
    index_page_subtitle = None
    index_meta_title = None
    index_view_is_public = False
    index_view_enabled = True
    index_view_class = IndexView
    index_view_template_names = None

    inspect_page_title = None
    inspect_page_subtitle = None
    inspect_meta_title = None
    inspect_view_is_public = False
    inspect_view_enabled = False
    inspect_view_class = InspectView
    inspect_view_template_names = None

    create_page_title = None
    create_page_subtitle = None
    create_meta_title = None
    create_view_enabled = False
    create_view_class = CreateView
    create_view_template_names = None

    edit_page_title = None
    edit_page_subtitle = None
    edit_meta_title = None
    edit_view_enabled = False
    edit_view_class = EditView
    edit_view_template_names = None

    delete_page_title = None
    delete_page_subtitle = None
    delete_meta_title = None
    delete_view_enabled = False
    delete_view_class = DeleteView
    delete_view_template_names = None

    # Helper
    permission_helper_class = SitePermissionHelper
    button_helper_class = ButtonHelper
    url_helper_class = SiteURLHelper

    def __init__(self, namespace):
        # Don't allow initialisation unless self.model is set to a valid model
        if not self.model or not issubclass(self.model, Model):
            raise ImproperlyConfigured(
                u"The model attribute on your '%s' class must be set, and "
                "must be a valid Django model." % self.__class__.__name__)
        self.namespace = namespace
        self.opts = self.model._meta
        self.permission_helper = self.get_permission_helper_class()(self)
        self.url_helper = self.get_url_helper_class()(self)

    def get_queryset(self, request):
        return self.model.objects.all()

    def get_model(self):
        if not self.model:
            raise ImproperlyConfigured('Model not provided')
        return self.model

    def get_fields(self):
        return self.fields

    def get_form_class(self):
        return self.form_class

    def get_namespace(self):
        return self.namespace or self.opts.app_label

    def get_menu_label(self):
        return self.menu_label or self.opts.verbose_name_plural.title()

    def get_menu_icon(self):
        return self.menu_icon

    def get_success_url(self):
        return self.url_helper.index_url

    def get_filterset_class(self):
        if self.filterset_class:
            return self.filterset_class
        elif self.model:
            return custom_filterset_factory(
                model=self.model,
                fields=self.filterset_fields
            )
        else:
            msg = "'%s' must define 'filterset_class' or 'model'"
            raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_permission_helper_class(self):
        return self.permission_helper_class

    def get_url_helper_class(self):
        return self.url_helper_class

    def get_button_helper_class(self):
        return self.button_helper_class

    def get_template_names(self, action):
        return [
            'sites/%s_%s_%s.html' % (self.namespace, self.opts.model_name, action),
            'sites/%s_%s.html' % (self.namespace, action),

            # Deprecated respect to above naming format
            'sites/%s/%s/%s.html' % (self.namespace, self.opts.model_name, action),
            'sites/%s/%s.html' % (self.namespace, action),

            'sites/%s.html' % action,
        ]

    def get_index_template(self):
        return self.index_view_template_names or self.get_template_names('index')

    def get_inspect_template(self):
        return self.inspect_view_template_names or self.get_template_names('inspect')

    def get_create_template(self):
        return self.create_view_template_names or self.get_template_names('create')

    def get_edit_template(self):
        return self.edit_view_template_names or self.get_template_names('edit')

    def get_delete_template(self):
        return self.delete_view_template_names or self.get_template_names('delete')

    def get_urls(self):
        url_helper = self.url_helper
        urls = []
        if self.create_view_enabled:
            urls.append(
                url(
                    url_helper.get_url_pattern('create', specific=False),
                    self.create_view, name=url_helper.get_url_name('create')
                ),
            )

        if self.edit_view_enabled:
            urls.append(
                url(
                    url_helper.get_url_pattern('edit', specific=True),
                    self.edit_view, name=url_helper.get_url_name('edit')
                ),
            )

        if self.delete_view_enabled:
            urls.append(
                url(
                    url_helper.get_url_pattern('delete', specific=True),
                    self.delete_view, name=url_helper.get_url_name('delete')
                ),
            )
        if self.inspect_view_enabled:
            urls.append(
                url(
                    url_helper.get_url_pattern('inspect', specific=True),
                    self.inspect_view, name=url_helper.get_url_name('inspect')
                )
            )
        if self.index_view_enabled:
            urls.append(
                url(url_helper.get_url_pattern('index', specific=False),
                    self.index_view,
                    name=url_helper.get_url_name('index')
                    )
            )

        return urls

    def index_view(self, request):
        kwargs = {'modelsite': self}
        view_class = self.index_view_class
        return view_class.as_view(**kwargs)(request)

    def create_view(self, request):
        kwargs = {'modelsite': self}
        view_class = self.create_view_class
        return view_class.as_view(**kwargs)(request)

    def inspect_view(self, request, instance_pk):
        kwargs = {'modelsite': self, 'instance_pk': instance_pk}
        view_class = self.inspect_view_class
        return view_class.as_view(**kwargs)(request)

    def edit_view(self, request, instance_pk):
        kwargs = {'modelsite': self, 'instance_pk': instance_pk}
        view_class = self.edit_view_class
        return view_class.as_view(**kwargs)(request)

    def delete_view(self, request, instance_pk):
        kwargs = {'modelsite': self, 'instance_pk': instance_pk}
        view_class = self.delete_view_class
        return view_class.as_view(**kwargs)(request)


class ModelSiteGroup:
    items = []
    namespace = None
    menu_icon = ''
    menu_label = ''

    def get_items(self):
        return self.items

    def get_modelsite_instance(self):
        if bool(self.items):
            sites = []
            for modelsite in self.get_items():
                sites.append(modelsite(namespace=self.namespace))
            return sites
        else:
            return []

    def get_urls(self):
        urls = []
        sites = self.get_modelsite_instance()
        for site in sites:
            urls.append(
                url('', include(site.get_urls()))
            )
        return urls
