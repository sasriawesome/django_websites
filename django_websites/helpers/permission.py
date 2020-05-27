from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission


class PermissionHelper:
    def __init__(self, model):
        self.model = model
        self.opts = model._meta

    def get_all_model_permissions(self):
        return Permission.objects.filter(
            content_type__app_label=self.opts.app_label,
            content_type__model=self.opts.model_name,
        )

    def get_perm_codename(self, action):
        return get_permission_codename(action, self.opts)

    def user_has_specific_permission(self, user, perm_codename):
        return user.has_perm("%s.%s" % (self.opts.app_label, perm_codename))

    def user_has_any_permissions(self, user):
        for perm in self.get_all_model_permissions().values('codename'):
            if self.user_has_specific_permission(user, perm['codename']):
                return True
        return False

    def user_can_list(self, user):
        return self.user_has_any_permissions(user)

    def user_can_create(self, user):
        perm_codename = self.get_perm_codename('add')
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_inspect_obj(self, user, obj):
        return self.user_has_any_permissions(user)

    def user_can_edit_obj(self, user, obj):
        perm_codename = self.get_perm_codename('change')
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_delete_obj(self, user, obj):
        perm_codename = self.get_perm_codename('delete')
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_unpublish_obj(self, user, obj):
        return False

    def user_can_copy_obj(self, user, obj):
        return False


class SitePermissionHelper:
    def __init__(self, modelsite):
        self.modelsite = modelsite
        self.model = modelsite.model
        self.opts = self.model._meta
        self.index_enabled = self.modelsite.index_view_enabled
        self.inspect_enabled = self.modelsite.inspect_view_enabled

    def get_all_model_permissions(self):
        return Permission.objects.filter(
            content_type__app_label=self.opts.app_label,
            content_type__model=self.opts.model_name,
        )

    def get_perm_codename(self, action):
        return get_permission_codename(action, self.opts)

    def user_has_specific_permission(self, user, perm_codename):
        return user.has_perm("%s.%s" % (self.opts.app_label, perm_codename))

    def user_has_any_permissions(self, user):
        for perm in self.get_all_model_permissions().values('codename'):
            if self.user_has_specific_permission(user, perm['codename']):
                return True
        return False

    def user_can_list(self, user):
        return self.index_enabled and self.user_has_any_permissions(user)

    def user_can_create(self, user):
        perm_codename = self.get_perm_codename('add')
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_inspect_obj(self, user, obj):
        return self.inspect_enabled and self.user_has_any_permissions(user)

    def user_can_edit_obj(self, user, obj):
        perm_codename = self.get_perm_codename('change')
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_delete_obj(self, user, obj):
        perm_codename = self.get_perm_codename('delete')
        return self.user_has_specific_permission(user, perm_codename)
