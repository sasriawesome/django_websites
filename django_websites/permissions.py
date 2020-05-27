# -*- coding: utf-8 -*-
# Custom Permission without model
# reference : https://stackoverflow.com/a/13952198
# inspired by wagtail admin migrations

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission


def create_global_permissions(name, codename):
    # Add a fake content type to hang the permission off.
    # The fact that this doesn't correspond to an actual defined model shouldn't matter, I hope...
    fake_model_content_type, created = ContentType.objects.get_or_create(
        app_label='global_permission',
        model='website'
    )

    # Create custom permission
    custom_permission, created = Permission.objects.get_or_create(
        content_type=fake_model_content_type,
        codename=codename,
        name=name
    )
    return custom_permission


def remove_global_permissions(codename):
    """Reverse the above additions of permissions."""

    fake_model_content_type = ContentType.objects.get(
        app_label='global_permission',
        model='website'
    )
    # This cascades to Group
    Permission.objects.filter(
        content_type=fake_model_content_type,
        codename=codename,
    ).delete()