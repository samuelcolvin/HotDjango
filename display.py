import django_tables2 as tables
from django_tables2.utils import A
import SkeletalDisplay
from django.contrib.auth.models import User, Group
import django.forms as forms

AppName = 'HotDisplay'

class User(SkeletalDisplay.ModelDisplay):
    model = User
    display = False
    exclude=['password']
    addable = False
    editable = True
    deletable = False
    attached_tables = [{'name':'Group', 'populate':'groups', 'title':'Groups'}]
    show_crums = False
    
    class form(forms.ModelForm):
        class Meta:
            model = User
            fields = ('first_name', 'last_name', 'email')

class Group(SkeletalDisplay.ModelDisplay):
    model = Group
    display = False
    
    class DjangoTable(SkeletalDisplay.Table):
        name = tables.Column()
        class Meta(SkeletalDisplay.ModelDisplayMeta):
            pass