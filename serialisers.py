import settings
from rest_framework import serializers

HOT_ID_IN_MODEL_STR = False
if hasattr(settings, 'HOT_ID_IN_MODEL_STR'):
    HOT_ID_IN_MODEL_STR = settings.HOT_ID_IN_MODEL_STR

class IDNameSerialiser(serializers.RelatedField):
    read_only = False
    def __init__(self, model, *args, **kw):
        self._model = model
        super(IDNameSerialiser, self).__init__(*args, **kw)
        
    def to_native(self, item):
        if hasattr(item, 'hot_name'):
            name = item.hot_name()
        else:
            name = str(item)
        if HOT_ID_IN_MODEL_STR:
            return name
        else:
            return '%d: %s' % (item.id, name)
    
    def from_native(self, item):
        try:
            dj_id = int(item)
        except:
            dj_id = int(item[:item.index(':')])
        return self._model.objects.get(id = dj_id)

class ChoiceSerialiser(serializers.Serializer):
    read_only = False
    def __init__(self, choices, *args, **kwargs):
        self._choices = choices
        super(ChoiceSerialiser, self).__init__(*args, **kwargs)
        
    def to_native(self, item):
        return next(choice[1] for choice in self._choices if choice[0] == item)
    
    def from_native(self, item):
        return next(choice[0] for choice in self._choices if choice[1] == item)
    
class ModelSerialiser(serializers.ModelSerializer):
    def save(self, *args, **kwargs):
        if hasattr(self.object, 'hotsave_enabled') and self.object.hotsave_enabled:
            kwargs['hotsave'] = True
        super(ModelSerialiser, self).save(*args, **kwargs)
            
    def get_fields(self):
        if hasattr(self.__class__, 'custom_fields'):
            self.opts.fields = self.__class__.custom_fields(self.request)
        return super(ModelSerialiser, self).get_fields()