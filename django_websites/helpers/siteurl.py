from django.urls import reverse
from django.utils.functional import cached_property


class SiteURLHelper:
    def __init__(self, modelsite):
        self.modelsite = modelsite
        self.model = modelsite.model
        self.namespace = modelsite.get_namespace()
        self.opts = modelsite.opts

    def get_url_pattern(self, action, specific=False):
        if action == 'index':
            return r'^%s/$' % self.opts.model_name
        if specific:
            return r'^%s/%s/(?P<instance_pk>[-\w]+)/$' % (self.opts.model_name, action)
        return r'^%s/%s/$' % (self.opts.model_name, action)

    def get_url_name(self, action):
        namespace = self.namespace or self.opts.app_label
        return '%s_%s_%s' % (
            namespace,
            self.opts.model_name,
            action
        )

    def get_url(self, action, specific, *args, **kwargs):
        if specific:
            url_name = self.get_url_name(action)
            return reverse(url_name, args=args, kwargs=kwargs)
        return reverse(self.get_url_name(action))

    @cached_property
    def index_url(self):
        return self.get_url('index', specific=False)

    @cached_property
    def create_url(self):
        return self.get_url('create', specific=False)

    @cached_property
    def index_url_name(self):
        return self.get_url_name('index')

    @cached_property
    def create_url_name(self):
        return self.get_url_name('create')

    @cached_property
    def inspect_url_name(self):
        return self.get_url_name('inspect')

    @cached_property
    def edit_url_name(self):
        return self.get_url_name('edit')

    @cached_property
    def delete_url_name(self):
        return self.get_url_name('delete')
