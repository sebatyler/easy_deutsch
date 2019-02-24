from django.template.defaulttags import register


@register.filter
def lookup(dictionary, key):
    return dictionary.get(key)
