from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Department, Employee, Notification, NotificationLog
from django import forms

# форма для редактирвоания данных пользователя
class EmployeeInlineForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ('department', 'phone', 'email', 'is_manager')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['department'].required = True

class EmployeeInline(admin.StackedInline):
    model = Employee
    form = EmployeeInlineForm
    can_delete = False
    extra = 0
    min_num = 1
    verbose_name_plural = 'Сотрудник (обязательные поля: email, отдел)'

class CustomUserAdmin(UserAdmin):
    inlines = (EmployeeInline,)

# перерегистр юзера
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Регистрация остальных моделей с предварительной отменой регистрации
for model in (Department, Notification, NotificationLog):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass
    admin.site.register(model)