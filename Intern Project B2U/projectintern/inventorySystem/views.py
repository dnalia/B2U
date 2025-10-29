from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.http import HttpResponse
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import FileResponse
from .models import User, TechRefresh, TechRefreshRequest, Inventory, Request, Notification, AssignedTask
import io
from django.http import JsonResponse
from django.core.serializers import serialize
from django.shortcuts import render, redirect, get_object_or_404
from .models import Engineer, AssignedTask
from django.utils import timezone
from django.shortcuts import render, redirect
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import AssignedTask, Engineer  # pastikan nama model betul
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import User, AssignedTask, Notification

@login_required
def task_history(request):
    # Ambil semua assigned tasks
    tasks = AssignedTask.objects.select_related('engineer').order_by('-assigned_date')

    # Kalau nak filter ikut engineer name:
    query = request.GET.get('q')
    if query:
        tasks = tasks.filter(engineer__username__icontains=query)

    return render(request, 'task_history.html', {'tasks': tasks})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Engineer, AssignedTask
from django.utils import timezone

def assign_task(request):
    engineers = Engineer.objects.all()  # penting untuk populate table!

    if request.method == 'POST':
        engineer_name = request.POST.get('engineer')
        engineer = Engineer.objects.filter(name=engineer_name).first()
        if not engineer:
            return redirect('assign_task')

        AssignedTask.objects.create(
            engineer=engineer,
            barcode=request.POST.get('barcode'),
            serial_number=request.POST.get('serial_number'),
            username=request.POST.get('username'),
            phone_number=request.POST.get('phone_number'),
            lan_id=request.POST.get('lan_id'),
            location=request.POST.get('location'),
            os=request.POST.get('os'),
            replacement_type=request.POST.get('replacement_type'),
            assigned_date=timezone.now(),
        )
        return redirect('assign_task')

    return render(request, 'assign_task.html', {'engineers': engineers})


# -------------------------
# Helper decorator: require_role
# -------------------------
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

# ==============================
# 🔐 LOGIN & LOGOUT
# ==============================
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


# ==============================
# 🏠 HOMEPAGE
# ==============================
def homepage(request):
    return render(request, "homepage.html")


# ==============================
# 📊 DASHBOARDS
# ==============================
@require_role('TeamLead')
def teamlead_dashboard(request):
    context = {
        'total_engineers': User.objects.filter(role='SystemEngineer').count(),
        'total_tasks': TechRefresh.objects.count(),
        'pending_tasks': TechRefresh.objects.filter(status='Pending').count(),
        'completed_tasks': TechRefresh.objects.filter(status='Completed').count(),
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



# ----------------------------
# 📄 Create Task (SystemEngineer only)
# ----------------------------
@login_required(login_url='login')
def create_task(request):
    if request.user.role != 'SystemEngineer':
        messages.error(request, "Access denied. Only System Engineers can create tasks.")
        return redirect('teamlead_dashboard')

    teamleads = User.objects.filter(role='TeamLead')

    if request.method == 'POST':
        task_type = request.POST.get('task_type')
        location = request.POST.get('location')
        user_name = request.POST.get('user_name')

        old_barcode = request.POST.get('old_barcode')
        new_barcode = request.POST.get('new_barcode')
        old_serial = request.POST.get('old_serial')
        new_serial = request.POST.get('new_serial')
        old_ip = request.POST.get('old_ip')
        new_ip = request.POST.get('new_ip')
        new_mac = request.POST.get('new_mac')
        old_hostname = request.POST.get('old_hostname')
        new_hostname = request.POST.get('new_hostname')

        rescheduled_date = request.POST.get('rescheduled_date') or None
        format_status = request.POST.get('format_status')
        reason_not_formatted = request.POST.get('reason_not_formatted')
        upload_status = request.POST.get('upload_status')
        reason_not_uploaded = request.POST.get('reason_not_uploaded')
        remarks = request.POST.get('remarks')
        proof = request.FILES.get('proof')

        approver_id = request.POST.get('assigned_approver')
        assigned_approver = None
        if approver_id:
            try:
                assigned_approver = User.objects.get(id=approver_id)
            except User.DoesNotExist:
                assigned_approver = None

        Request.objects.create(
            engineer=request.user,
            type=task_type,
            location=location,
            user=user_name,
            old_barcode=old_barcode,
            new_barcode=new_barcode,
            old_serial=old_serial,
            new_serial=new_serial,
            old_ip=old_ip,
            new_ip=new_ip,
            new_mac=new_mac,
            old_hostname=old_hostname,
            new_hostname=new_hostname,
            rescheduled_date=rescheduled_date,
            format_status=format_status,
            reason_not_formatted=reason_not_formatted,
            upload_status=upload_status,
            reason_not_uploaded=reason_not_uploaded,
            remarks=remarks,
            proof=proof,
            assigned_approver=assigned_approver
        )

        messages.success(request, "Task submitted successfully!")
        return redirect('systemengineer_dashboard')

    context = {'teamleads': teamleads}
    return render(request, 'create_task.html', context)


# ----------------------------
# 📝 My Submissions
# ----------------------------
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


@login_required
def download_task_pdf(request, task_id):
    task = get_object_or_404(Request, id=task_id, engineer=request.user)

    if task.status != 'Approved':
        messages.error(request, "You can only download approved tasks.")
        return redirect('my_submissions')

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Task Report")

    p.setFont("Helvetica", 12)
    y = height - 100
    details = [
        f"Engineer: {task.engineer.username}",
        f"Task Type: {task.type}",
        f"Status: {task.status}",
        f"Location: {task.location}",
        f"Old Barcode: {task.old_barcode}",
        f"New Barcode: {task.new_barcode}",
        f"Old Serial: {task.old_serial}",
        f"New Serial: {task.new_serial}",
        f"Old IP: {task.old_ip}",
        f"New IP: {task.new_ip}",
        f"Remarks: {task.remarks or '-'}",
        f"Date Submitted: {task.created_at.strftime('%Y-%m-%d %H:%M')}",
    ]

    for line in details:
        p.drawString(80, y, line)
        y -= 20

    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"task_{task.id}.pdf")


# ----------------------------
# 🛠 Update Inventory Status
# ----------------------------
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


# ==============================
# 🧾 TECH REFRESH FORMS
# ==============================
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


# ==============================
# 👥 MANAGE ENGINEERS (TeamLead only)
# ==============================
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


# ==============================
# 📦 REQUEST MANAGEMENT
# ==============================
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


@require_role('TeamLead')
def approve_request(request, req_id):
    req = Request.objects.filter(id=req_id).first()
    if req:
        req.status = 'Approved'
        req.save()
        Notification.objects.create(
            user=req.engineer,
            message=f"Your submission for {req.user} has been approved by the Team Lead."
        )
        messages.success(request, f"Request for {req.user} approved and notification sent.")
        return redirect('manage_requests')

    req = TechRefreshRequest.objects.filter(id=req_id).first()
    if req:
        req.status = 'Approved'
        req.save()
        Notification.objects.create(
            user=req.engineer,
            message=f"Your Tech Refresh submission for {req.user} has been approved by the Team Lead."
        )
        messages.success(request, f"Tech Refresh request for {req.user} approved and notification sent.")
        return redirect('manage_requests')

    messages.error(request, "Request not found.")
    return redirect('manage_requests')


@require_role('TeamLead')
def reject_request(request, req_id):
    req = Request.objects.filter(id=req_id).first()
    if req:
        req.status = 'Rejected'
        req.save()
        Notification.objects.create(
            user=req.engineer,
            message=f"Your submission for {req.user} has been rejected by the Team Lead."
        )
        messages.success(request, f"Request for {req.user} rejected and notification sent.")
        return redirect('manage_requests')

    req = TechRefreshRequest.objects.filter(id=req_id).first()
    if req:
        req.status = 'Rejected'
        req.save()
        Notification.objects.create(
            user=req.engineer,
            message=f"Your Tech Refresh submission for {req.user} has been rejected by the Team Lead."
        )
        messages.success(request, f"Tech Refresh request for {req.user} rejected and notification sent.")
        return redirect('manage_requests')

    messages.error(request, "Request not found.")
    return redirect('manage_requests')


# ==============================
# 📈 REPORTS & EXPORTS (TeamLead only)
# ==============================
@require_role('TeamLead')
def reports(request):
    requests_list = TechRefreshRequest.objects.all().order_by('-submitted_at')
    context = {'requests': requests_list}
    return render(request, 'reports.html', context)





@require_role('TeamLead')
def export_requests_excel(request):
    requests_list = TechRefreshRequest.objects.all().values(
        'engineer__username', 'location', 'user', 'status', 'submitted_at'
    )
    df = pd.DataFrame(list(requests_list))
    df.rename(columns={
        'engineer__username': 'Engineer',
        'location': 'Location',
        'user': 'User',
        'status': 'Status',
        'submitted_at': 'Submitted At'
    }, inplace=True)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Requests')

    buffer.seek(0)
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="requests_report.xlsx"'
    return response


@require_role('TeamLead')
def export_requests_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="requests_report.pdf"'

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Requests Report")

    p.setFont("Helvetica", 11)
    y = height - 100
    requests_list = TechRefreshRequest.objects.all().order_by('-submitted_at')

    for req in requests_list:
        text = f"Engineer: {req.engineer.username}, Location: {req.location}, Status: {req.status}, Date: {req.submitted_at.strftime('%Y-%m-%d')}"
        p.drawString(50, y, text)
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 11)

    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


# MAINTENANCE LOGS
@login_required
def maintenance_logs(request):
    logs = [
        {'item': 'Monitor', 'issue': 'Display flickering', 'date': '2025-10-10'},
        {'item': 'Keyboard', 'issue': 'Key stuck', 'date': '2025-10-12'},
    ]
    return render(request, 'maintenance_logs.html', {'logs': logs})


# ASSIGNED ITEMS
@login_required(login_url='login')
def assigned_items(request):
    items = [
        {'name': 'Laptop Dell', 'status': 'In Use'},
        {'name': 'Mouse HP', 'status': 'Returned'},
    ]
    return render(request, 'assigned_items.html', {'items': items})


# send feedback (SystemEngineer)
@login_required(login_url='login')
def send_feedback(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        messages.success(request, "Feedback submitted successfully!")
        return redirect('systemengineer_dashboard')
    return render(request, 'send_feedback.html')


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

