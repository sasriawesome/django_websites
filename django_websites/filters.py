from django_filters.filterset import FilterSet, ALL_FIELDS

def custom_filterset_factory(model, fields=ALL_FIELDS):
    meta_fields = {'model': model, 'fields': fields}
    meta = type(str('Meta'), (object,), meta_fields)
    filterset = type(
        str('%sFilterSet' % model._meta.object_name),
        (FilterSet,),
        {'Meta': meta}
    )
    return filterset