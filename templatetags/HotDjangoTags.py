from django import template
from django.core.urlresolvers import reverse
from .. import rest_views
from .. import public
import json
from django.db import models
from rest_framework.reverse import reverse as rest_reverse

register = template.Library()

@register.tag(name='handsontable_render_full')
def handsontable_render_full(parser, token):
    try:
        _, app_name, model_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('render_table_full tag requires exactly two arguments: app_name and model_name')
    return HandsOnTableMainNode(app_name, model_name)

class HandsOnTableMainNode(template.Node):
    def __init__(self, app_name, model_name):
        self.app_name = template.Variable(app_name)
        self.model_name = template.Variable(model_name)

    def render(self, context):
        t = template.loader.get_template('hot/handsontable_main.html')
        app_name = self.app_name.resolve(context)
        model_name = self.model_name.resolve(context)
        context['main_json_url'] = reverse(rest_views.generate_reverse(app_name, model_name) + '-list')
        return t.render(template.Context(context))

@register.tag(name='handsontable_render_extra')
def handsontable_render_extra(parser, token):
    try:
        _, app_name, model_name, field_names, this_id = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('handsontable_render_extra tag requires exactly three arguments: '+ \
                                           'app_name, model_name and comma seperated list of fields')
    return HandsOnTableExtraNode(app_name, model_name, field_names, this_id)

class HandsOnTableExtraNode(template.Node):
    def __init__(self, app_name, model_name, field_names, this_id):
        self.app_name = template.Variable(app_name)
        self.model_name = template.Variable(model_name)
        self.field_names = template.Variable(field_names)
        self.id = template.Variable(this_id)

    def render(self, context):
        t = template.loader.get_template('hot/handsontable_extra.html')
        app_name = self.app_name.resolve(context)
        model_name = self.model_name.resolve(context)
        this_id = int(self.id.resolve(context))
        dm = public.get_rest_apps()[app_name][model_name]
        extra_urls = {}
        field_names = [f.strip() for f in self.field_names.resolve(context).split(',')]
        for field_name in field_names:
            dj_field = dm.model._meta.get_field_by_name(field_name)[0]
            extra_urls[field_name] = {}
            extra_urls[field_name]['heading'] = public.get_verbose_name(dm, field_name) 
            if isinstance(dj_field, models.ManyToManyField):
                other_model_name = dj_field.rel.to.__name__
                extra_urls[field_name]['field'] = field_name
                url = reverse(rest_views.generate_reverse(app_name, model_name)\
                                                         + '-getm2m',  kwargs={'pk': this_id})
                extra_urls[field_name]['update_url'] = reverse(rest_views.generate_reverse(app_name, model_name)\
                                                         + '-setm2m',  kwargs={'pk': this_id})
            else:
                other_model_name = dj_field.model.__name__
                extra_urls[field_name]['filter_on'] = dj_field.field.name
                extra_urls[field_name]['filter_value'] = this_id
                url = reverse(rest_views.generate_reverse(app_name, other_model_name) + '-list')
            extra_urls[field_name]['url'] = url
        context['extra_urls'] = json.dumps(extra_urls)
        return t.render(template.Context(context))

@register.simple_tag
def _handsontable_render_extra_modals():
    return template.loader.render_to_string('hot/handsontable_extra_modals.html')
    
@register.simple_tag
def handsontable_render_js():
    return template.loader.render_to_string('hot/handsontable_js.html')
    
@register.simple_tag
def handsontable_render_css():
    return template.loader.render_to_string('hot/handsontable_css.html')

@register.inclusion_tag('hot/headings.html', takes_context=True)
def hot_headings(context):
    return context
    