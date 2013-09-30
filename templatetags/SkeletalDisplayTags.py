from django import template

register = template.Library()

@register.inclusion_tag('sk_headings.html', takes_context=True)
def sk_headings(context):
    return context
    
