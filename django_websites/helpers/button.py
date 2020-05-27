from django.contrib.admin.utils import quote
from django.utils.encoding import force_str
from django.utils.translation import ugettext as _


class ButtonHelper:
    default_button_classnames = ['btn']
    add_button_classnames = ['btn-success', 'mdi', 'mdi-plus']
    inspect_button_classnames = ['btn-info']
    edit_button_classnames = ['btn-primary']
    delete_button_classnames = ['btn-danger']

    def __init__(self, view, request):
        self.view = view
        self.request = request
        self.model = view.model
        self.opts = view.model._meta
        self.verbose_name = force_str(self.opts.verbose_name)
        self.verbose_name_plural = force_str(self.opts.verbose_name_plural)
        self.permission_helper = view.permission_helper
        self.url_helper = view.url_helper

    def finalise_classname(self, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        combined = self.default_button_classnames + classnames_add
        finalised = [cn for cn in combined if cn not in classnames_exclude]
        return ' '.join(finalised)

    def add_button(self, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.add_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.create_url,
            'label': _('Add %s') % self.verbose_name,
            'classname': cn,
            'title': _('Add a new %s') % self.verbose_name,
        }

    def inspect_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.inspect_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_url('inspect', True, quote(pk)),
            'label': _('Inspect'),
            'classname': cn,
            'title': _('Inspect this %s') % self.verbose_name,
        }

    def edit_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_url('edit', True, quote(pk)),
            'label': _('Edit'),
            'classname': cn,
            'title': _('Edit this %s') % self.verbose_name,
        }

    def delete_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.delete_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_url('delete', True, quote(pk)),
            'label': _('Delete'),
            'classname': cn,
            'title': _('Delete this %s') % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None, classnames_exclude=None):
        if exclude is None:
            exclude = []
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        ph = self.permission_helper
        usr = self.request.user
        pk = getattr(obj, self.opts.pk.attname)
        btns = []

        inspect_enabled = self.view.modelsite.inspect_view_enabled
        inspect_excluded = 'inspect' in exclude
        user_can_inspect = ph.user_can_inspect_obj(usr, obj)
        if inspect_enabled and not inspect_excluded and user_can_inspect:
            btns.append(
                self.inspect_button(pk, classnames_add, classnames_exclude)
            )

        edit_enabled = self.view.modelsite.edit_view_enabled
        edit_excluded = 'edit' in exclude
        user_can_edit = ph.user_can_edit_obj(usr, obj)
        if edit_enabled and not edit_excluded and user_can_edit:
            btns.append(
                self.edit_button(pk, classnames_add, classnames_exclude)
            )

        delete_enabled = self.view.modelsite.delete_view_enabled
        delete_excluded = 'delete' in exclude
        user_can_delete = ph.user_can_delete_obj(usr, obj)
        if delete_enabled and delete_excluded and user_can_delete:
            btns.append(
                self.delete_button(pk, classnames_add, classnames_exclude)
            )
        return btns
