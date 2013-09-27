from django.shortcuts import redirect
from django.core.urlresolvers import reverse
import SkeletalDisplay.views_base as viewb
import django.views.generic.edit as generic_editor
import django.forms.models as form_models
import settings
import SkeletalDisplay

class HotEdit(viewb.TemplateBase):
    template_name = 'sk_hot_edit.html'

    def get_context_data(self, **kw):
        self.setup_context(**kw)
        self._context['title'] = 'Mass Editor'
        self._top_active = 'display_index'
        self._context['app_name'] = self._app_name
        self._context['model_name'] = self._model_name
        return self._context

class AddEditItem(generic_editor.TemplateResponseMixin, generic_editor.ModelFormMixin, generic_editor.ProcessFormView, viewb.ViewBase): 
    template_name = 'sk_add_edit.html'
    
    def setup_context(self, **kw):
        super(AddEditItem, self).setup_context(**kw)
        if self._disp_model.form is not None:
            self.form_class = self._disp_model.form
        else:
            self.form_class = form_models.modelform_factory(self._disp_model.model)
        self.object = None
        if self._item_id is not None:
            self.object = self._item
    
    def get(self, request, *args, **kw):
        self.setup_context(**kw)
        return super(AddEditItem, self).get(request, *args, **kw)
    
    def post(self, request, *args, **kw):
        self.setup_context(**kw)
        return super(AddEditItem, self).post(request, *args, **kw)
    
    def form_valid(self, form):
        context = self.get_context_data()
        if self._disp_model.formset_model is not None:
            formset = context['formset']
            if formset.is_valid():
                self.object = form.save(self.request)
                formset.instance = self.object
                formset.save()
            else:
                self._add_line('Form not Valid')
                return self.render_to_response(self.get_context_data(form=form))
        else:
            form.save(self.request)
        self._add_line('%s saved' % self._disp_model.model_name)
        if self._item_id is not None:
            return redirect(reverse('display_item', args=[self._app_name, self._model_name, self._item_id]))
        else:
            return redirect(reverse('display_model', args=[self._app_name, self._model_name]))

    def form_invalid(self, form):
        self._add_line('Form not Valid')
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kw):
        self._context.update(super(AddEditItem, self).get_context_data(**kw))
        self._context['title'] = '%s %s' % (self.action, self._disp_model.model_name)
        
        self._context['base_template'] = 'sk_page_base.html'
        if hasattr(settings, 'PAGE_BASE'):
            self._context['base_template'] = settings.PAGE_BASE
        
        if self._disp_model.formset_model is not None:
            Formset = form_models.inlineformset_factory(self._disp_model.model, self._disp_model.formset_model, extra=2)
            if self.request.POST:
                self._context['formset'] = Formset(self.request.POST)
            else:
                instance = None
                if self._item_id is not None:
                    instance = self.object
                self._context['formset'] = Formset(instance = instance)
        return self._context
    
    def _add_line(self, line):
        if not 'success' in self._context:
            self.request.session['success'] = []
        self.request.session['success'].append(line)

class AddItem(AddEditItem):
    action = 'Add'

class EditItem(AddEditItem):
    action = 'Edit'

def delete_item(request, app_name, model_name, item_id):
    apps = SkeletalDisplay.get_display_apps()
    disp_model = apps[app_name][model_name]
    item = disp_model.model.objects.get(id=int(item_id))
    item.delete()
    return redirect(reverse('display_model', args=[app_name, model_name]))