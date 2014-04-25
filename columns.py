import django_tables2 as tables
from django.utils.safestring import mark_safe

class BooleanColumn(tables.Column):
    def render(self, value):
        if value:
            return mark_safe('<span class="glyphicon glyphicon glyphicon-ok"></span>')
        else:
            return mark_safe('<span class="glyphicon glyphicon glyphicon-remove"></span>')
    
class SterlingPriceColumn(tables.Column):
    def render(self, value):
        if value>1000:
            return '{:,}'.format(value)
        elif value>10:
            return '%0.2f' % value
        else:
            string = '%0.3f' % value
            if string.endswith('0'):
                return string[:-1]
            return string
        
class ShowlinkMixin(object):
    def __init__(self, *args, **kw):
        self.show_link = kw.pop('show_link', None)
        super(ShowlinkMixin, self).__init__(*args, **kw)
        
class RenderMixin(object):
    def render(self, value, **kw):
        table = kw['table']
        show = not (self.show_link and not self.show_link(table.request))
        if show:
            return super(RenderMixin, self).render(value, kw['record'], kw['bound_column'])
        else:
            return value
        
class LinkColumn(RenderMixin, ShowlinkMixin, tables.LinkColumn):
    pass
        
class SelfRenderMixin(object):    
    def render(self, value, **kw):
        record = kw['record']
        table = kw['table']
        if None in (table.viewname, table.reverse_args_base):
            return value
        else:
            disp_model_name = table.Meta.display_model_name
            url = table._url_base.replace('__mod_name__', disp_model_name).replace('1234567', str(record.id))
            return mark_safe('<a href="%s">%s</a>' % (url, value))    
    
class SelfLinkColumn(RenderMixin, SelfRenderMixin, ShowlinkMixin, tables.Column):
    pass