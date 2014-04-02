from django import template

register = template.Library()

@register.inclusion_tag('hot/headings.html', takes_context=True)
def sk_headings(context):
    return context
    
