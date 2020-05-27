from functools import wraps
from django.core.exceptions import ValidationError
from django.shortcuts import reverse, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect


def prevent_recursion(func):
    """ Decorator, Prevent Recursion inside Post Save Signal """

    @wraps(func)
    def no_recursion(sender, instance=None, **kwargs):
        if not instance:
            return
        # if there is _dirty, return
        if hasattr(instance, '_dirty'):
            return
        func(sender, instance=instance, **kwargs)
        try:
            # there is dirty, lets save
            instance._dirty = True
            instance.save()
        finally:
            del instance._dirty

    return no_recursion


method_csrf_protect = method_decorator(csrf_protect)


def need_object_permission(fn):
    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        request = args[0]
        object_id = kwargs.get('object_id', None)
        try:
            return fn(self, request, object_id, **kwargs)
        except ValidationError as err:
            self.message_user(request, err[0], level=messages.ERROR)
            return redirect(reverse('simpeladmin:%s_%s_changelist' % self.get_model_info()))
        except self.model.DoesNotExist as err:
            self.message_user(request, err, level=messages.ERROR)
            return redirect(reverse('simpeladmin:%s_%s_changelist' % self.get_model_info()))

    return wrapped


from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test


def student_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    '''
    Decorator for views that checks that the logged in user is a student,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_student,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def teacher_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    '''
    Decorator for views that checks that the logged in user is a teacher,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_teacher,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def employee_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    '''
    Decorator for views that checks that the logged in user is a employee,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_employee,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator