from django import forms
from .models import Department

class NotificationForm(forms.Form):
    title = forms.CharField(max_length=200, label='Заголовок', widget=forms.TextInput(attrs={'class': 'form-control'}))
    text = forms.CharField(label='Текст', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False, label='Отдел (оставьте пустым для всех)', widget=forms.Select(attrs={'class': 'form-select'}))
    is_urgent = forms.BooleanField(required=False, label='Срочное', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

class EmployeeImportForm(forms.Form):
    csv_file = forms.FileField(label='CSV файл', help_text='Формат: login,email,phone,department_id,is_manager (1/0)')