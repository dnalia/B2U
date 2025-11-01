from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, FileResponse
from django.utils import timezone
from django.db.models import Q
from io import BytesIO
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .models import (
    User, TechRefresh, TechRefreshRequest, Inventory, Request,
    Notification, AssignedTask, Engineer, Submission
)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .models import AssignedTask, TaskHistory
from django.core import serializers
from django.contrib.auth.decorators import login_required
from .models import Submission, Request, Notification
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

@login_required(login_url='login')
def manage_requests(request):
    # Ambil query parameter dari form search dan filter status
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')

    # Ambil data daripada kedua-dua model
    requests_qs = Request.objects.all()
    tech_qs = TechRefresh.objects.all()

    # Filter berdasarkan carian (nama engineer / lokasi / user)
    if search_query:
        requests_qs = requests_qs.filter(
Q(engineer__username__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(user__icontains=search_query)
        )
        tech_qs = tech_qs.filter(
            Q(engineer_name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(user_name__icontains=search_query)
        )

    # Filter berdasarkan status
    if status_filter and status_filter != 'all':
        requests_qs = requests_qs.filter(status=status_filter)
        tech_qs = tech_qs.filter(status=status_filter)

    # Gabungkan data jadi satu senarai (normalize supaya template boleh baca seragam)
    combined_requests = []

    for r in requests_qs:
        combined_requests.append({
            'id': r.id,
            'type': r.type,
            'engineer': r.engineer.username if r.engineer else 'N/A',
            'user': r.user or 'N/A',
            'location': r.location or 'N/A',
            'status': r.status,
            'old_hostname': r.old_hostname or '-',
            'new_hostname': r.new_hostname or '-',
            'old_serial': r.old_serial or '-',
            'new_serial': r.new_serial or '-',
            'rescheduled_date': r.rescheduled_date or '-',
            'format_status': r.format_status or '-',
            'reason_not_formatted': r.reason_not_formatted or '-',
            'upload_status': r.upload_status or '-',
            'reason_not_uploaded': r.reason_not_uploaded or '-',
            'remarks': r.remarks or '-',
            'proof': r.proof.url if r.proof else None,
            'created_at': r.created_at,
        })

    for t in tech_qs:
        combined_requests.append({
            'id': t.id,
            'type': 'Tech Refresh',
            'engineer': t.engineer_name or 'N/A',
            'user': t.user_name or 'N/A',
            'location': t.location or 'N/A',
            'status': t.status,
            'old_hostname': t.old_hostname or '-',
            'new_hostname': t.new_hostname or '-',
            'old_serial': t.old_serial_number or '-',
            'new_serial': t.new_serial_number or '-',
            'rescheduled_date': t.date_if_rescheduled or '-',
            'format_status': t.format_status or '-',
            'reason_not_formatted': t.reason_not_formatted or '-',
            'upload_status': t.upload_status or '-',
            'reason_not_uploaded': t.reason_not_uploaded or '-',
            'remarks': t.remarks or '-',
            'proof': None,  # Tiada proof field untuk model ni
            'created_at': t.created_at,
        })

    # Susun ikut tarikh paling baru
    combined_requests.sort(key=lambda x: x['created_at'], reverse=True)

    context = {
        'requests': combined_requests,
        'search_query': search_query,
        'status_filter': status_filter,
    }

    return render(request, 'manage_requests.html', context)

@login_required
def submit_task(request, task_id):
    task = get_object_or_404(AssignedTask, id=task_id, engineer=request.user)

    if request.method == 'POST':
        # Create submission
        Submission.objects.create(
            engineer=request.user,
            task=task,
            status="Pending Verification"
        )

        # Update task status
        task.status = "Done"
        task.save()

        # Create corresponding Request for Team Lead to verify
        Request.objects.create(
            engineer=request.user,
            type="Tech Refresh",  # or pull from task.replacement_type if you have it
            location=task.location,
            user=task.username,
            old_barcode=task.barcode,
            new_barcode=task.serial_number,
            status="Pending",
            assigned_approver=User.objects.filter(role='TeamLead').first(),
        )

        # Notify Team Lead
        Notification.objects.create(
            user=User.objects.filter(role='TeamLead').first(),
            message=f"New request submitted by {request.user.username} for {task.username}"
        )

        messages.success(request, "Task submitted successfully!")
        return redirect('my_submission')

    return render(request, 'my_submissions.html', {'task': task})

@login_required
def systemengineer_tasks(request):
    assigned_tasks = AssignedTask.objects.filter(engineer=request.user)
    tasks_json = serializers.serialize('json', assigned_tasks)
    return render(request, 'create_tasks.html', {
        'assigned_tasks': assigned_tasks,
        'tasks_json': tasks_json
    })


@login_required
def engineer_tasks(request):
    # Filter ikut siapa login
    tasks = AssignedTask.objects.filter(engineer=request.user).order_by('-assigned_date')

    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        task = get_object_or_404(AssignedTask, id=task_id)

        # Update info yang System Engineer isi
        task.status = request.POST.get('status')
        task.remarks = request.POST.get('remarks')
        if 'proof' in request.FILES:
            task.proof = request.FILES['proof']
        task.updated_at = timezone.now()
        task.save()

        # Simpan ke TaskHistory (optional)
        TaskHistory.objects.create(
            engineer=request.user,
            task=task,
            status=task.status,
            remarks=task.remarks,
            updated_at=timezone.now(),
        )

        messages.success(request, f'Task "{task.username}" updated successfully.')
        return redirect('engineer_tasks')

    return render(request, 'create_task.html', {'tasks': tasks})

# ✅ Assign Task page
@login_required
def assign_task(request):
    engineers = User.objects.filter(role='SystemEngineer')  # filter ikut role
    if request.method == 'POST':
        engineer_name = request.POST.get('engineer')
        barcode = request.POST.get('barcode')
        serial_number = request.POST.get('serial_number')
        username = request.POST.get('username')
        phone_number = request.POST.get('phone_number')
        lan_id = request.POST.get('lan_id')
        location = request.POST.get('location')
        os = request.POST.get('os')
        replacement_type = request.POST.get('replacement_type')

        # cari engineer berdasarkan nama
        engineer = get_object_or_404(User, username=engineer_name)

        # simpan dalam model
        assigned_task = AssignedTask.objects.create(
            engineer=engineer,
            barcode=barcode,
            serial_number=serial_number,
            username=username,
            phone_number=phone_number,
            lan_id=lan_id,
            location=location,
            os=os,
            replacement_type=replacement_type,
            assigned_date=timezone.now(),
        )

        # ✅ Tambah notification untuk System Engineer
        Notification.objects.create(
            user=engineer,
            message=f"You have been assigned a new task: {replacement_type} for user {username} by Team Lead {request.user.username}."
        )

        messages.success(request, f'Task successfully assigned to {engineer.username} and notification sent.')
        return redirect('assign_task')

    return render(request, 'assign_task.html', {'engineers': engineers})

@login_required

def engineer_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})

# ✅ Task History page
@login_required
def task_history(request, engineer_id):
    engineer = get_object_or_404(User, id=engineer_id)
    tasks = AssignedTask.objects.filter(engineer=engineer).order_by('-assigned_date')

    # search function (optional)
    query = request.GET.get('q')
    if query:
        tasks = tasks.filter(engineer__username__icontains=query)

    return render(request, 'task_history.html', {
        'tasks': tasks,
        'engineer': engineer,
    })

def require_role(role):
    """
    Decorator to require a certain role on the request.user.
    If user doesn't have the role, redirect to their dashboard.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def _wrapped(request, *args, **kwargs):
            # If user is not authenticated, login_required will redirect.
            if not hasattr(request.user, 'role') or request.user.role != role:
                # Redirect to the appropriate dashboard for their role
                if hasattr(request.user, 'role') and request.user.role == 'SystemEngineer':
                    messages.error(request, "Access denied: Team Lead only.")
                    return redirect('systemengineer_dashboard')
                else:
                    messages.error(request, "Access denied.")
                    return redirect('login')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        selected_role = request.POST.get("role")  # 👈 ambil role dari form

        user = authenticate(request, username=username, password=password)

        if user and user.is_active:
            if user.role != selected_role:  # 👈 semak role sebenar vs role pilihan
                messages.error(request, f"Access denied: You are a {user.role}, not {selected_role}.")
                return redirect("login")

            login(request, user)

            if user.role == "TeamLead":
                return redirect("teamlead_dashboard")
            elif user.role == "SystemEngineer":
                return redirect("systemengineer_dashboard")
            else:
                messages.error(request, "Your account role is invalid.")
                logout(request)
                return redirect("login")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")

'''
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.is_active:
            login(request, user)
            # Redirect ikut role sebenar
            if user.role == "TeamLead":
                return redirect("teamlead_dashboard")
            elif user.role == "SystemEngineer":
                return redirect("systemengineer_dashboard")
            else:
                messages.error(request, "Your account role is invalid.")
                logout(request)
                return redirect("login")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")
'''
def logout_view(request):
    logout(request)
    return redirect("login")

def homepage(request):
    return render(request, "homepage.html")

@require_role('TeamLead')
def teamlead_dashboard(request):
    # Kira jumlah system engineer
    total_engineers = User.objects.filter(role='SystemEngineer').count()

    # Jumlah semua task
    total_tasks = Request.objects.count()

    # Kira pending dan completed secara case-insensitive
    pending_tasks = Request.objects.filter(status__iexact='Pending').count()
    completed_tasks = Request.objects.filter(status__iexact='Completed').count()

    context = {
        'total_engineers': total_engineers,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
    }

    return render(request, 'teamlead_dashboard.html', context)

@login_required(login_url='login')
def systemengineer_dashboard(request):
    # ✅ Pastikan hanya System Engineer boleh masuk
    if request.user.role != 'SystemEngineer':
        messages.error(request, "Access denied. You are not a System Engineer.")
        return redirect('teamlead_dashboard')

    user = request.user

    # ✅ Ambil semua task/request yang engineer ni buat
    my_requests = Request.objects.filter(engineer=user)

    # ✅ Ambil inventory yang ditambah/assigned kepada engineer ni
    assigned_items = Inventory.objects.filter(added_by=user)

    # ✅ Kira status
    pending_count = my_requests.filter(status='Pending').count()
    approved_count = my_requests.filter(status='Approved').count()
    rejected_count = my_requests.filter(status='Rejected').count()

    # ✅ Hantar semua data ke template
    context = {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'my_requests': my_requests,
        'assigned_items': assigned_items
    }

    return render(request, 'systemengineer_dashboard.html', context)
@login_required
def create_task(request):
    user = request.user

    if user.role == 'TeamLead':
        engineers = User.objects.filter(role='SystemEngineer')
        if request.method == "POST":
            engineer_id = request.POST.get('engineer_id')
            engineer = User.objects.get(id=engineer_id)
            replacement_type = request.POST.get('replacement_type')
            location = request.POST.get('location')
            user_name = request.POST.get('user_name')
            barcode = request.POST.get('barcode')
            serial_number = request.POST.get('serial_number')

            AssignedTask.objects.create(
                engineer=engineer,
                replacement_type=replacement_type,
                location=location,
                username=user_name,
                barcode=barcode,
                serial_number=serial_number
            )

            Notification.objects.create(
                user=engineer,
                message=f"You have been assigned a new task: {replacement_type} at {location}."
            )
            return redirect('create_task')

        return render(request, 'create_task.html', {'engineers': engineers, 'is_teamlead': True})

    elif user.role == 'SystemEngineer':
        selected_task = None
        task_id = request.GET.get('task_id')

        if task_id:
            selected_task = AssignedTask.objects.get(id=task_id, engineer=user)

        if request.method == "POST" and selected_task:
            status = request.POST.get('status')

            # ✅ Update status + save file uploads
            selected_task.status = status
            selected_task.remarks = request.POST.get('remarks')
            selected_task.proof = request.FILES.get('proof')
            selected_task.save()

            # ✅ If task done → move to submission + notify TL
            if status.lower() == "done":
                # Move ke MySubmissions (boleh guna model Submission)
                Submission.objects.create(
                    engineer=user,
                    task=selected_task,
                    status="Pending Verification"
                )

                # Notify team lead
                teamlead = User.objects.filter(role='TeamLead').first()
                if teamlead:
                    Notification.objects.create(
                        user=teamlead,
                        message=f"{user.username} has submitted a completed task for verification."
                    )

                # Delete/hide from AssignedTask list
                selected_task.delete()

            return redirect('my_submissions')

        assigned_tasks = AssignedTask.objects.filter(engineer=user)
        return render(request, 'create_task.html', {
            'assigned_tasks': assigned_tasks,
            'selected_task': selected_task,
            'is_teamlead': False
        })

    else:
        return redirect('dashboard')

@login_required
def my_submissions(request):
    submissions = Request.objects.filter(engineer=request.user).order_by('-created_at')
    return render(request, 'my_submissions.html', {'submissions': submissions})

@login_required
def cancel_task(request, task_id):
    task = get_object_or_404(Request, id=task_id, engineer=request.user)
    if task.status == "Pending":
        task.status = "Cancelled"
        task.save()
    return redirect('my_submissions')


@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Request, id=task_id, engineer=request.user)
    if request.method == 'POST':
        task.location = request.POST.get('location')
        task.user = request.POST.get('user')
        task.new_barcode = request.POST.get('new_barcode')
        task.new_serial = request.POST.get('new_serial')
        task.save()
        return redirect('my_submissions')
    return render(request, 'edit_task.html', {'task': task})


@require_role('TeamLead')
def export_requests_pdf(request):
    engineer_name = request.GET.get('engineer_name', '').strip()
    request_type = request.GET.get('request_type', '').strip()
    date_filter = request.GET.get('start_date', '').strip()

    # Combine data sama macam reports()
    request_list = []

    reqs = Request.objects.filter(status__in=['Approved', 'Pending', 'Rejected']).order_by('-created_at')
    for r in reqs:
        request_list.append({
            'engineer_name': r.engineer.username if r.engineer else "N/A",
            'request_type': r.type or "General Request",
            'date_submitted': r.created_at.date(),
            'status': r.status,
        })

    techs = TechRefreshRequest.objects.filter(status__in=['Approved', 'Pending', 'Rejected']).order_by('-submitted_at')
    for t in techs:
        request_list.append({
            'engineer_name': t.engineer.username if t.engineer else "N/A",
            'request_type': "Tech Refresh",
            'date_submitted': t.submitted_at.date(),
            'status': t.status,
        })

    # Apply filters
    if engineer_name:
        request_list = [r for r in request_list if engineer_name.lower() in r['engineer_name'].lower()]

    if request_type:
        request_list = [r for r in request_list if r['request_type'].lower() == request_type.lower()]

    if date_filter:
        request_list = [r for r in request_list if str(r['date_submitted']) == date_filter]

    # ===== Generate PDF =====
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, height - 40, "Requests Report")

    y = height - 80
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Engineer Filter: {engineer_name or 'All'}")
    y -= 15
    p.drawString(50, y, f"Request Type: {request_type or 'All'}")
    y -= 15
    p.drawString(50, y, f"Date: {date_filter or 'All'}")
    y -= 30

    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Engineer")
    p.drawString(180, y, "Request Type")
    p.drawString(320, y, "Date")
    p.drawString(420, y, "Status")
    y -= 15
    p.line(50, y, 550, y)
    y -= 10

    p.setFont("Helvetica", 10)
    for r in request_list:
        if y < 80:  # new page
            p.showPage()
            y = height - 80
        p.drawString(50, y, r['engineer_name'])
        p.drawString(180, y, r['request_type'])
        p.drawString(320, y, str(r['date_submitted']))
        p.drawString(420, y, r['status'])
        y -= 15

    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="filtered_report.pdf")

def download_task_pdf(request):
    return HttpResponse("Download Task PDF feature not implemented yet.")

@login_required(login_url='login')
def update_status(request, pk):
    if request.user.role != 'SystemEngineer':
        messages.error(request, "Access denied.")
        return redirect('teamlead_dashboard')

    item = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        item.condition = request.POST.get('condition')
        item.save()
        messages.success(request, f'Status for {item.item_name} updated!')
        return redirect('systemengineer_dashboard')
    return render(request, 'update_status.html', {'item': item})

@login_required(login_url='login')
def add_tech_refresh(request):
    if request.user.role != 'TeamLead':
        messages.error(request, "Access denied.")
        return redirect('systemengineer_dashboard')

    if request.method == 'POST':
        TechRefresh.objects.create(
            engineer_name=request.POST.get('engineer_name'),
            user_name=request.POST.get('user_name'),
            location=request.POST.get('location'),
            old_hostname=request.POST.get('old_hostname'),
            new_hostname=request.POST.get('new_hostname'),
            old_serial_number=request.POST.get('old_serial_number'),
            new_serial_number=request.POST.get('new_serial_number'),
            status=request.POST.get('status'),
            date_if_rescheduled=request.POST.get('date_if_rescheduled') or None,
            format_status=request.POST.get('format_status'),
            reason_not_formatted=request.POST.get('reason_not_formatted'),
            upload_status=request.POST.get('upload_status'),
            reason_not_uploaded=request.POST.get('reason_not_uploaded'),
            remarks=request.POST.get('remarks'),
        )
        return redirect('tech_refresh_list')
    return render(request, 'tech_refresh.html')

@login_required(login_url='login')
def tech_refresh_list(request):
    records = TechRefresh.objects.all()
    return render(request, 'tech_refresh_list.html', {'records': records})

@require_role('TeamLead')
def manage_engineers(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role", "SystemEngineer")
        # Ensure role is valid
        if role not in ['SystemEngineer', 'TeamLead']:
            role = 'SystemEngineer'

        # Use create_user to properly hash password
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role
        user.save()

        messages.success(request, f"{username} created.")
        return redirect('manage_engineers')

    engineers = User.objects.filter(role='SystemEngineer')
    return render(request, "manage_engineers.html", {"engineers": engineers})

@require_role('TeamLead')
def edit_engineer(request, engineer_id):
    engineer = get_object_or_404(User, id=engineer_id)
    # team lead may edit engineers but not superusers (optional)
    if request.method == 'POST':
        engineer.username = request.POST.get('username')
        engineer.email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'SystemEngineer')
        if password:
            engineer.set_password(password)
        if role in ['SystemEngineer', 'TeamLead']:
            engineer.role = role
        engineer.save()
        messages.success(request, 'Engineer updated successfully!')
        return redirect('manage_engineers')
    return render(request, 'edit_engineer.html', {'engineer': engineer})

@require_role('TeamLead')
def delete_engineer(request, engineer_id):
    engineer = get_object_or_404(User, id=engineer_id)
    # Prevent deleting yourself accidentally
    if request.user.id == engineer.id:
        messages.error(request, "You cannot delete your own account.")
        return redirect('manage_engineers')

    engineer.delete()
    messages.success(request, "Engineer deleted.")
    return redirect('manage_engineers')

@login_required(login_url='login')
def create_request(request):
    if request.method == 'POST':
        TechRefreshRequest.objects.create(
            engineer=request.user,
            location=request.POST.get('location'),
            user=request.POST.get('user'),
            old_barcode=request.POST.get('old_barcode'),
            new_barcode=request.POST.get('new_barcode'),
            status='Pending',
            remarks=request.POST.get('remarks'),
            proof=request.FILES.get('proof')
        )
        return redirect('systemengineer_dashboard')
    return render(request, 'create_request.html')

@require_role('TeamLead')
def manage_engineers(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role", "SystemEngineer")
        # Ensure role is valid
        if role not in ['SystemEngineer', 'TeamLead']:
            role = 'SystemEngineer'

        # Use create_user to properly hash password
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role
        user.save()

        messages.success(request, f"{username} created.")
        return redirect('manage_engineers')

    engineers = User.objects.filter(role='SystemEngineer')
    return render(request, "manage_engineers.html", {"engineers": engineers})

@login_required
def approve_request(request, req_id):
    submission = Submission.objects.get(id=req_id)
    submission.status = "Approved"
    submission.save()

    Notification.objects.create(
        user=submission.engineer,
        message=f"Your submitted task has been approved ✅"
    )

    return redirect('manage_requests')


@login_required
def reject_request(request, req_id):
    submission = Submission.objects.get(id=req_id)
    submission.status = "Rejected"
    submission.save()

    Notification.objects.create(
        user=submission.engineer,
        message=f"Your submitted task has been rejected ❌"
    )

    return redirect('manage_requests')

def reports(request):
    engineer_name = request.GET.get('engineer_name', '')
    request_type = request.GET.get('request_type', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    requests_qs = Request.objects.all()

    # Filter ikut nama
    if engineer_name:
        requests_qs = requests_qs.filter(engineer_name__icontains=engineer_name)

    # Filter ikut request type
    if request_type:
        requests_qs = requests_qs.filter(request_type__icontains=request_type)

    # Filter ikut date range
    if start_date and end_date:
        requests_qs = requests_qs.filter(date_submitted__range=[start_date, end_date])
    elif start_date:
        requests_qs = requests_qs.filter(date_submitted__gte=start_date)
    elif end_date:
        requests_qs = requests_qs.filter(date_submitted__lte=end_date)

    context = {
        'requests': requests_qs,
        'engineer_name': engineer_name,
        'request_type': request_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports.html', context)

@require_role('TeamLead')
def reports(request):
    """
    Show all requests (Request + TechRefreshRequest) with filters:
    - Engineer name
    - Request type
    - Date
    """
    engineer_name = request.GET.get('engineer_name', '').strip()
    request_type = request.GET.get('request_type', '').strip()
    date_filter = request.GET.get('start_date', '').strip()

    # Combine both models into a single list
    request_list = []

    # Regular requests
    reqs = Request.objects.filter(status__in=['Approved', 'Pending', 'Rejected']).order_by('-created_at')
    for r in reqs:
        request_list.append({
            'id': r.id,
            'engineer_name': r.engineer.username if r.engineer else "N/A",
            'request_type': r.type or "General Request",
            'date_submitted': r.created_at.date(),
            'status': r.status,
        })

    # Tech Refresh requests
    techs = TechRefreshRequest.objects.filter(status__in=['Approved', 'Pending', 'Rejected']).order_by('-submitted_at')
    for t in techs:
        request_list.append({
            'id': t.id,
            'engineer_name': t.engineer.username if t.engineer else "N/A",
            'request_type': "Tech Refresh",
            'date_submitted': t.submitted_at.date(),
            'status': t.status,
        })

    # Apply filters
    if engineer_name:
        request_list = [r for r in request_list if engineer_name.lower() in r['engineer_name'].lower()]

    if request_type:
        request_list = [r for r in request_list if r['request_type'].lower() == request_type.lower()]

    if date_filter:
        request_list = [r for r in request_list if str(r['date_submitted']) == date_filter]

    # Sort by latest date
    request_list.sort(key=lambda x: x['date_submitted'], reverse=True)

    context = {
        'requests': request_list,
        'engineer_name': engineer_name,
        'request_type': request_type,
        'start_date': date_filter,
    }
    return render(request, 'reports.html', context)

@require_role('TeamLead')
def export_requests_excel(request):
    """
    Export combined Request + TechRefreshRequest data into Excel.
    """
    # Combine both models
    reqs = list(Request.objects.values('engineer__username', 'type', 'status', 'created_at'))
    techs = list(TechRefreshRequest.objects.values('engineer__username', 'status', 'submitted_at'))

    # Normalize fields to be consistent
    combined_data = []
    for r in reqs:
        combined_data.append({
            'Engineer': r['engineer__username'],
            'Request Type': r['type'] or "General Request",
            'Status': r['status'],
            'Date Submitted': r['created_at'],
        })
    for t in techs:
        combined_data.append({
            'Engineer': t['engineer__username'],
            'Request Type': "Tech Refresh",
            'Status': t['status'],
            'Date Submitted': t['submitted_at'],
        })

    if not combined_data:
        messages.error(request, "No data available to export.")
        return redirect('reports')

    df = pd.DataFrame(combined_data)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Requests Report')

    buffer.seek(0)
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="requests_report.xlsx"'
    return response

'''
def export_requests_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="filtered_requests.pdf"'

    # Buat PDF canvas
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Tajuk PDF
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2 * cm, height - 2 * cm, "Filtered Requests Report")

    # Ambil data dari GET parameter
    request_type = request.GET.get('request_type', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    # Parse tarikh (kalau ada)
    try:
        if from_date:
            from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        if to_date:
            to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
    except ValueError:
        from_date = to_date = None

    # Tentukan model berdasarkan jenis request
    if request_type == "Tech Refresh":
        queryset = TechRefreshRequest.objects.all()
        date_field = "submitted_at"
    else:
        queryset = Request.objects.all()
        date_field = "created_at"

    # Apply tarikh filter
    if from_date:
        queryset = queryset.filter(**{f"{date_field}__date__gte": from_date})
    if to_date:
        queryset = queryset.filter(**{f"{date_field}__date__lte": to_date})

    # Tambah margin untuk text
    y = height - 3 * cm
    p.setFont("Helvetica", 11)

    if queryset.exists():
        for req in queryset:
            # Bezakan antara Request & TechRefreshRequest
            if request_type == "Tech Refresh":
                line = f"{req.engineer.username} | {req.user} | {req.location} | {req.status} | {req.submitted_at.strftime('%Y-%m-%d')}"
            else:
                line = f"{req.engineer.username} | {req.user} | {req.location} | {req.status} | {req.created_at.strftime('%Y-%m-%d')}"

            p.drawString(2 * cm, y, line)
            y -= 0.6 * cm
            if y < 2 * cm:
                p.showPage()
                y = height - 3 * cm
                p.setFont("Helvetica", 11)
    else:
        p.setFont("Helvetica-Oblique", 11)
        p.drawString(2 * cm, y, "No records found for the selected filters.")

    p.showPage()
    p.save()
    return response

'''
@require_role('TeamLead')
def export_requests_pdf(request):
    engineer_name = request.GET.get('engineer_name', '').strip()
    request_type = request.GET.get('request_type', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    # Ambil semua request dari 2 model
    request_list = []

    reqs = Request.objects.all().order_by('-created_at')
    techs = TechRefreshRequest.objects.all().order_by('-submitted_at')

    # Apply filters sama macam reports()
    if engineer_name:
        reqs = reqs.filter(engineer__username__icontains=engineer_name)
        techs = techs.filter(engineer__username__icontains=engineer_name)
    if request_type:
        reqs = reqs.filter(type__icontains=request_type)
        techs = techs.filter(type__icontains=request_type)
    if start_date and end_date:
        reqs = reqs.filter(created_at__range=[start_date, end_date])
        techs = techs.filter(submitted_at__range=[start_date, end_date])
    elif start_date:
        reqs = reqs.filter(created_at__gte=start_date)
        techs = techs.filter(submitted_at__gte=start_date)
    elif end_date:
        reqs = reqs.filter(created_at__lte=end_date)
        techs = techs.filter(submitted_at__lte=end_date)

    # Gabungkan ke satu senarai
    for r in reqs:
        request_list.append({
            'engineer_name': r.engineer.username if r.engineer else "N/A",
            'request_type': r.type or "General Request",
            'date_submitted': r.created_at.date(),
            'status': r.status,
        })

    for t in techs:
        request_list.append({
            'engineer_name': t.engineer.username if t.engineer else "N/A",
            'request_type': "Tech Refresh",
            'date_submitted': t.submitted_at.date(),
            'status': t.status,
        })

    # ===== Generate PDF =====
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, height - 40, "Requests Report")

    y = height - 80
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Engineer Filter: {engineer_name or 'All'}")
    y -= 15
    p.drawString(50, y, f"Request Type: {request_type or 'All'}")
    y -= 15
    p.drawString(50, y, f"Date Range: {start_date or '-'} to {end_date or '-'}")
    y -= 30

    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Engineer")
    p.drawString(180, y, "Request Type")
    p.drawString(320, y, "Date")
    p.drawString(420, y, "Status")
    y -= 15
    p.line(50, y, 550, y)
    y -= 10

    p.setFont("Helvetica", 10)
    for r in request_list:
        if y < 80:  # new page
            p.showPage()
            y = height - 80
        p.drawString(50, y, r['engineer_name'])
        p.drawString(180, y, r['request_type'])
        p.drawString(320, y, str(r['date_submitted']))
        p.drawString(420, y, r['status'])
        y -= 15

    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="filtered_report.pdf")

@login_required
@require_role('TeamLead')
def report_details(request, request_id):
    report = get_object_or_404(Request, id=request_id)
    return render(request, 'report_details.html', {'report': report})

# NOTIFICATIONS
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})


@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')

@login_required
def view_request_detail(request, req_id):
    # Try both models since TeamLead manages both
    request_obj = (
        Request.objects.filter(id=req_id).first() or
        TechRefreshRequest.objects.filter(id=req_id).first()
    )

    if not request_obj:
        messages.error(request, "Request not found.")
        return redirect('manage_requests')

    return render(request, 'view_request_detail.html', {'request_obj': request_obj})


@login_required
def view_request_details(request, req_id):
    # Try to find in Request first
    request_obj = Request.objects.filter(id=req_id).first()
    request_type = "Request"

    # If not found, try TechRefreshRequest
    if not request_obj:
        request_obj = TechRefreshRequest.objects.filter(id=req_id).first()
        request_type = "TechRefreshRequest"

    # If still not found, return error
    if not request_obj:
        messages.error(request, "Request not found.")
        return redirect('my_submissions')

    context = {
        'request_obj': request_obj,
        'request_type': request_type,
    }

    return render(request, 'view_request_details.html', context)

@login_required
def download_task_pdf(request, task_id):
    task = get_object_or_404(Request, id=task_id, engineer=request.user)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph(f"Task Submission Report", styles['Title']))
    elements.append(Spacer(1, 12))

    # Table data
    data = [
        ["Field", "Detail"],
        ["Task ID", str(task.id)],
        ["Task Type", task.type],
        ["Location", task.location],
        ["Status", task.status],
        ["Submitted At", task.created_at.strftime('%d %b %Y, %I:%M %p')],
    ]

    table = Table(data, colWidths=[120, 300])
    
    # Status warna
    status_color = colors.green if task.status=="Approved" else \
                   colors.orange if task.status=="Pending" else \
                   colors.red if task.status=="Rejected" else colors.grey

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#004aad")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BACKGROUND', (1,4), (1,4), status_color),  # highlight status
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"task_{task.id}.pdf")
