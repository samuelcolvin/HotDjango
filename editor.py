from django.shortcuts import redirect
from django.core.urlresolvers import reverse
import views_base as viewb
import django.views.generic.edit as generic_editor
import django.forms.models as form_models
import settings

class HotEdit(viewb.TemplateBase):
    template_name = 'hot/hot_edit.html'
    side_menu = False
    
    def setup_context(self, **kw):
        if 'view_settings' in self.request.session:
            self.view_settings = viewb.HOT_VIEW_SETTINGS.copy()
            if hasattr(settings, 'HOT_VIEW_SETTINGS'):
                self.view_settings.update(settings.HOT_VIEW_SETTINGS)
            self.view_settings.update(self.request.session['view_settings'])
        super(HotEdit, self).setup_context(**kw)
        if 'extra_context' in self.request.session:
            self._context.update(self.request.session['extra_context'])

    def get_context_data(self, **kw):
        self.set_crums(add = [{'url': '', 'name': 'Mass Edit'}])
#         self._context['title'] = 'Mass Editor'
        self._menu_active = 'display_index'
        self._context['app_name'] = self._app_name
        self._context['model_name'] = self._model_name
        return self._context

class AddEditItem(viewb.ViewBase, generic_editor.TemplateResponseMixin, generic_editor.ModelFormMixin, generic_editor.ProcessFormView): 
    template_name = 'hot/add_edit.html'
    action = 'Add'
    
    def _editing_self(self):
        if self._item_id is None:
            return False
        return self._model_name == 'User' and self._item_id is not None and self.request.user.id == int(self._item_id)
    
    @property
    def allowed(self):
        if self._editing_self():
            return True
        return super(AddEditItem, self).allowed
        
    def setup_context(self, **kw):
        if 'view_settings' in self.request.session:
            self.view_settings = viewb.HOT_VIEW_SETTINGS.copy()
            if hasattr(settings, 'HOT_VIEW_SETTINGS'):
                self.view_settings.update(settings.HOT_VIEW_SETTINGS)
            self.view_settings.update(self.request.session['view_settings'])
        super(AddEditItem, self).setup_context(**kw)
        if 'extra_context' in self.request.session:
            self._context.update(self.request.session['extra_context'])
        self.object = None
        if self._item_id is not None:
            self.object = self._item
            self.action = 'Edit'
        self.set_crums(add = [{'url': '', 'name': self.action}])
        if self._disp_model.form is not None:
            self.form_class = self._disp_model.form
        else:
            self.form_class = form_models.modelform_factory(self._disp_model.model)
    
    def post(self, request, *args, **kw):
        self.setup_context(**kw)
        if not self.allowed:
            return redirect(reverse('permission_denied'))
        return super(AddEditItem, self).post(request, *args, **kw)
    
    def form_valid(self, form):
        context = self.get_context_data()
        if self._disp_model.formset_model is not None:
            formset = context['formset']
            if formset.is_valid():
                form.request = self.request
                self.object = form.save()
                formset.instance = self.object
                formset.save()
            else:
                self.error_log('Form not Valid')
                return self.render_to_response(self.get_context_data(form=form))
        else:
            form.request = self.request
            form.save()
        self.success_log('%s saved' % self._disp_model.model_name)
        if self._editing_self():
            return redirect(reverse('user_profile'))
        if self._item_id is not None:
            return redirect(reverse(self.viewname, args=self.args_base(model=self._model_name) + [self._item_id]))
        else:
            return redirect(reverse(self.viewname, args=self.args_base(model=self._model_name)))

    def form_invalid(self, form):
        self.error_log('Form not Valid')
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kw):
        self._context.update(super(AddEditItem, self).get_context_data(**kw))
        self._context['title'] = '%s %s' % (self.action, self._disp_model.model_name)
        
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
    
    def success_log(self, line):
        if not 'success' in self.request.session:
            self.request.session['success'] = []
        self.request.session['success'].append(line)
     
    def error_log(self, line):
        if not 'errors' in self.request.session:
            self.request.session['errors'] = []
        self.request.session['errors'].append(line)
        

class DeleteItem(viewb.TemplateBase):
    def get(self, request, *args, **kw):
        self.setup_context(**kw)
        self.request.session['success'] = ['%s deleted' % self._item]
        self._item.delete()
        return redirect(reverse(self.viewname, args=self.args_base(model=self._model_name)))