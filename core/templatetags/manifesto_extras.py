from django import template

register = template.Library()


@register.filter
def count_status(manifestos, status):
    if status == 'none':
        return sum(1 for m in manifestos if not m.updates.first())
    return sum(1 for m in manifestos if m.updates.first() and m.updates.first().status == status)
