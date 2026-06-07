from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Department(models.Model):
    name = models.CharField('Название отдела', max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Отдел')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    email = models.EmailField('Рабочий email')
    is_manager = models.BooleanField('Руководитель', default=False)
    def __str__(self):
        return self.user.get_full_name() or self.user.username

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

class Notification(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст уведомления')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    department_target = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Отдел-получатель (пусто - всем)')
    is_urgent = models.BooleanField('Срочное', default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

class NotificationLog(models.Model):
    STATUS_CHOICES = (
        ('sent', 'Отправлено'),
        ('read', 'Прочитано'),
    )
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, verbose_name='Уведомление')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Сотрудник')
    status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='sent')
    sent_at = models.DateTimeField('Время отправки', auto_now_add=True)
    read_at = models.DateTimeField('Время прочтения', null=True, blank=True)

    def __str__(self):
        return f'{self.notification.title} -> {self.employee.user.username} ({self.status})'

    class Meta:
        verbose_name = 'Журнал уведомлений'
        verbose_name_plural = 'Журналы уведомлений'




#@receiver(post_save, sender=User)
#def create_employee_for_new_user(sender, instance, created, **kwargs):
#    if created:
#        Employee.objects.get_or_create(
#            user=instance,
#            defaults={
#                'email': instance.email,
#                'phone': '',
#                'is_manager': False,
 #               'department': None
#       
 #           }
#        )