import csv
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.http import HttpResponse
from .models import Department, Employee, Notification, NotificationLog
from .forms import NotificationForm, EmployeeImportForm

def is_manager(user):
    return user.employee.is_manager

def is_admin(user):
    return user.is_superuser

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('staff:dashboard')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'staff/login.html')

def logout_view(request):
    logout(request)
    return redirect('staff:login')

@login_required
def dashboard(request):
    emp = request.user.employee
    unread = NotificationLog.objects.filter(
        employee=emp, status='sent'
    ).select_related('notification')
    recent = NotificationLog.objects.filter(
        employee=emp
    ).order_by('-sent_at')[:10]
    return render(request, 'staff/dashboard.html', {
        'unread': unread,
        'recent': recent
    })

@login_required
def my_notifications(request):
    emp = request.user.employee
    logs = NotificationLog.objects.filter(
        employee=emp
    ).select_related('notification').order_by('-sent_at')
    return render(request, 'staff/my_notifications.html', {'logs': logs})

@login_required
def mark_as_read(request, log_id):
    log = get_object_or_404(
        NotificationLog, id=log_id, employee=request.user.employee
    )
    if log.status == 'sent':
        log.status = 'read'
        log.read_at = timezone.now()
        log.save()
        messages.success(request, 'Уведомление отмечено как прочитанное.')
    return redirect('staff:my_notifications')

def notification_detail(request, log_id):
    log = get_object_or_404(
        NotificationLog, id=log_id, employee=request.user.employee
    )
    return render(request, 'staff/notification_detail.html', {'log': log})

@login_required
def notification_detail_author(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id)
    if notif.author != request.user.employee and not request.user.is_superuser:
        messages.error(request, 'Нет доступа к этому уведомлению')
        return redirect('staff:dashboard')
    logs = NotificationLog.objects.filter(
        notification=notif
    ).select_related('employee__user')
    return render(request, 'staff/notification_author_detail.html', {
        'notification': notif,
        'logs': logs
    })

@login_required
@user_passes_test(is_manager)
def send_notification(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            text = form.cleaned_data['text']
            dept = form.cleaned_data['department']
            urgent = form.cleaned_data['is_urgent']

            if dept:
                employees = Employee.objects.filter(department=dept)
            else:
                employees = Employee.objects.all()

            if not employees.exists():
                messages.warning(request, 'Нет сотрудников для отправки.')
                return redirect('staff:send_notification')

            notif = Notification.objects.create(
                title=title,
                text=text,
                author=request.user.employee,
                department_target=dept,
                is_urgent=urgent
            )
            for emp in employees:
                send_mail(
                    subject=title,
                    message=text,
                    from_email='system@mycompany.com',
                    recipient_list=[emp.email],
                    fail_silently=True,
                )
                NotificationLog.objects.create(
                    notification=notif,
                    employee=emp,
                    status='sent'
                )

            messages.success(
                request,
                f'Уведомление успешно отправлено {employees.count()} сотрудникам.'
            )
            return redirect('staff:dashboard')
    else:
        form = NotificationForm()
    return render(request, 'staff/send_notification.html', {'form': form})

@login_required
@user_passes_test(is_manager)
def manager_report(request):
    emp = request.user.employee
    notifications = Notification.objects.filter(
        author=emp
    ).order_by('-created_at')
    report_data = []
    for notif in notifications:
        logs = NotificationLog.objects.filter(notification=notif)
        total = logs.count()
        read = logs.filter(status='read').count()
        report_data.append({
            'notification_id': notif.id,
            'notification_title': notif.title,
            'notification_created_at': notif.created_at,
            'total': total,
            'read': read,
            'percent': round(read / total * 100, 1) if total > 0 else 0
        })
    return render(request, 'staff/manager_report.html', {
        'report_data': report_data
    })

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    employees = Employee.objects.select_related('department', 'user').all()
    departments = Department.objects.all()
    logs = NotificationLog.objects.select_related(
        'notification', 'employee'
    ).order_by('-sent_at')[:50]
    return render(request, 'staff/admin_dashboard.html', {
        'employees': employees,
        'departments': departments,
        'logs': logs
    })

@login_required
@user_passes_test(is_admin)
def import_employees(request):
    if request.method == 'POST':
        form = EmployeeImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['csv_file']
            decoded = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded)
            fieldnames = reader.fieldnames
            if not fieldnames:
                messages.error(request, 'Файл пустой или неверный формат.')
                return redirect('staff:import_employees')
            fieldnames_clean = [f.strip().lower() for f in fieldnames]
            print("Заголовки CSV:", fieldnames_clean)  # для отладки
            required = ['login', 'email']
            missing = [col for col in required if col not in fieldnames_clean]
            if missing:
                messages.error(
                    request,
                    f'Отсутствуют столбцы: {", ".join(missing)}. '
                    f'Найдены: {", ".join(fieldnames_clean)}'
                )
                return redirect('staff:import_employees')
            created = 0
            errors = 0
            for row in reader:
                row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

                try:
                    username = row.get('login', '').strip()
                    email = row.get('email', '').strip()

                    if not username or not email:
                        print(f"Пропуск строки - пустой login или email: {row}")
                        errors += 1
                        continue
                    phone = row.get('phone', '')
                    dept_id = row.get('department_id', '').strip() or None
                    is_mgr = row.get('is_manager', '0').strip() == '1'
                    user, created_user = User.objects.get_or_create(
                        username=username,
                        defaults={'email': email}
                    )
                    if created_user:
                        user.set_password('pass123')
                        user.save()
                    Employee.objects.update_or_create(
                        user=user,
                        defaults={
                            'email': email,
                            'phone': phone,
                            'department_id': dept_id,
                            'is_manager': is_mgr
                        }
                    )
                    created += 1
                except Exception as e:
                    print(f"Ошибка в строке {row}: {e}")
                    errors += 1
                    continue
            if errors > 0:
                messages.warning(
                    request,
                    f'Импортировано: {created}, пропущено с ошибками: {errors}.'
                )
            else:
                messages.success(
                    request,
                    f'Успешно импортировано {created} сотрудников.'
                )
            return redirect('staff:admin_dashboard')
    else:
        form = EmployeeImportForm()
    return render(request, 'staff/import_employees.html', {'form': form})
@login_required
@user_passes_test(is_admin)
def export_logs_csv(request):
    logs = NotificationLog.objects.select_related(
        'notification', 'employee', 'employee__user'
    ).all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="logs.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'ID уведомления', 'Заголовок', 'Сотрудник',
        'Email', 'Статус', 'Отправлено', 'Прочитано'
    ])
    for log in logs:
        writer.writerow([
            log.notification.id,
            log.notification.title,
            log.employee.user.get_full_name(),
            log.employee.email,
            log.get_status_display(),
            log.sent_at.strftime('%Y-%m-%d %H:%M'),
            log.read_at.strftime('%Y-%m-%d %H:%M') if log.read_at else ''
        ])
    return response
@login_required
@user_passes_test(lambda u: u.is_superuser or u.employee.is_manager)
def notification_recipients_detail(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if not request.user.is_superuser and notification.author != request.user.employee:
        messages.error(request, 'У вас нет прав на просмотр этого уведомления.')
        return redirect('staff:manager_report')

    logs = NotificationLog.objects.filter(
        notification=notification
    ).select_related('employee__user')
    recipients_data = []
    for log in logs:
        full_name = log.employee.user.get_full_name() or log.employee.user.username
        recipients_data.append({
            'full_name': full_name,
            'status': log.status,
            'read_at': log.read_at,
            'sent_at': log.sent_at,
            'email': log.employee.email,
        })
    context = {
        'notification': notification,
        'recipients': recipients_data,
        'total': len(recipients_data),
        'read_count': sum(1 for r in recipients_data if r['status'] == 'read'),
    }
    return render(request, 'staff/notification_recipients.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def notification_report(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id)
    logs = NotificationLog.objects.filter(
        notification=notif
    ).select_related('employee__user')
    report_data = []
    for log in logs:
        full_name = log.employee.user.get_full_name() or log.employee.user.username
        report_data.append({
            'full_name': full_name,
            'email': log.employee.email,
            'status': log.status,
            'read_at': log.read_at,
            'sent_at': log.sent_at,
        })
    return render(request, 'staff/notification_report.html', {
        'notification': notif,
        'report_data': report_data
    }) 