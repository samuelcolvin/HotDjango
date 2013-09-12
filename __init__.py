import settings
import inspect, json
import HotDjango

class ModelDisplay(HotDjango.BaseDisplayModel):
    extra_funcs = []
    tables = []
    display = True
    
class ModelDisplayMeta:
    orderable = False
    attrs = {'class': 'table table-bordered table-condensed'}
    per_page = 100

class _AppEncode(json.JSONEncoder):
    def default(self, obj):
        if inspect.isclass(obj):
            return dir(obj)
        return json.JSONEncoder.default(self, dir(obj))
    

class Logger:
    def __init__(self):
        self._log = ''
        
    def addline(self, line):
        self._log +='<p>%s</p>\n' % line
        
    def get_log(self):
        return self._log