from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my/', views.my_notifications, name='my_notifications'),
    path('mark-read/<int:log_id>/', views.mark_as_read, name='mark_as_read'),
    path('send/', views.send_notification, name='send_notification'),
    path('manager-report/', views.manager_report, name='manager_report'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('import/', views.import_employees, name='import_employees'),
    path('export-csv/', views.export_logs_csv, name='export_logs_csv'),
    path('notification/<int:log_id>/', views.notification_detail, name='notification_detail'),
    path('notification/<int:log_id>/', views.notification_detail, name='notification_detail'),
    path('notification-detail/<int:notification_id>/', views.notification_recipients_detail, name='notification_recipients_detail'),
    path('notification-report/<int:notification_id>/', views.notification_report, name='notification_report'),
]