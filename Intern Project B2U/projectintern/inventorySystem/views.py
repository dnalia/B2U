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
from .models import User, TechRefresh, TechRefreshRequest,Inventory,Request,Notification


# ==============================
# 🔐 LOGIN & LOGOUT
# ==============================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        selected_role = request.POST.get("role")

        user = authenticate(request, username=username, password=password)

        if user:
            if user.role == selected_role:
                login(request, user)
                if user.role == "TeamLead":
                    return redirect("teamlead_dashboard")
                elif user.role == "SystemEngineer":
                    return redirect("systemengineer_dashboard")
            else:
                messages.error(request, "Role does not match your account.")
                logout(request)
                return redirect("login")  # ✅ pastikan ni
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")  # ✅ pastikan ni juga

    return render(request, "login.html")



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
@login_required(login_url='login')
def teamlead_dashboard(request):
    if request.user.role != 'TeamLead':
        messages.error(request, "Access denied. You are not a Team Lead.")
        return redirect('login')

    context = {
        'total_engineers': User.objects.filter(role='SystemEngineer').count(),
        'total_tasks': TechRefresh.objects.count(),
        'pending_tasks': TechRefresh.objects.filter(status='Pending').count(),
        'completed_tasks': TechRefresh.objects.filter(status='Completed').count(),
    }
    return render(request, 'teamlead_dashboard.html', context)


# ----------------------------
# 🧑‍🔧 System Engineer Dashboard
# ----------------------------
@login_required(login_url='login')
def systemengineer_dashboard(request):
    user = request.user
    my_requests = TechRefreshRequest.objects.filter(engineer=user)
    assigned_items = Inventory.objects.filter(added_by=user)  # boleh tukar ikut logic assigned items

    context = {
        'pending_count': my_requests.filter(status='Pending').count(),
        'approved_count': my_requests.filter(status='Approved').count(),
        'rejected_count': my_requests.filter(status='Rejected').count(),
        'my_requests': my_requests,
        'assigned_items': assigned_items
    }
    return render(request, 'systemengineer_dashboard.html', context)


# ----------------------------
# 📄 Create Task
# ----------------------------
@login_required(login_url='login')
def create_task(request):
    # Ambil semua Team Lead untuk pilih approver
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
        remarks = request.POST.get('remarks')
        approver_id = request.POST.get('assigned_approver')
        proof = request.FILES.get('proof')

        assigned_approver = None
        if approver_id:
            assigned_approver = User.objects.get(id=approver_id)

        # Buat Request baru
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
            remarks=remarks,
            proof=proof,
            assigned_approver=assigned_approver
        )

        messages.success(request, "Task submitted successfully!")
        return redirect('systemengineer_dashboard')

    context = {
        'teamleads': teamleads
    }
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

    # Generate PDF guna reportlab
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
# 👥 MANAGE ENGINEERS
# ==============================
@login_required(login_url='login')
def manage_engineers(request):
    if request.user.role != 'TeamLead':
        return redirect('systemengineer_dashboard')

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            role='SystemEngineer'
        )
        return redirect('manage_engineers')

    engineers = User.objects.filter(role='SystemEngineer')
    return render(request, "manage_engineers.html", {"engineers": engineers})


@login_required(login_url='login')
def edit_engineer(request, engineer_id):
    engineer = get_object_or_404(User, id=engineer_id, role='SystemEngineer')
    if request.method == 'POST':
        engineer.username = request.POST.get('username')
        engineer.email = request.POST.get('email')
        password = request.POST.get('password')
        if password:
            engineer.set_password(password)
        engineer.save()
        messages.success(request, 'Engineer updated successfully!')
        return redirect('manage_engineers')
    return render(request, 'edit_engineer.html', {'engineer': engineer})


@login_required(login_url='login')
def delete_engineer(request, engineer_id):
    engineer = get_object_or_404(User, id=engineer_id, role='SystemEngineer')
    engineer.delete()
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
    if request.user.role != 'TeamLead':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('login')

    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')

    requests_qs = TechRefreshRequest.objects.all().order_by('-submitted_at')

    if search_query:
        requests_qs = requests_qs.filter(
            Q(engineer__username__icontains=search_query) |
            Q(user__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    if status_filter and status_filter != 'all':
        requests_qs = requests_qs.filter(status__iexact=status_filter)

    context = {
        'requests': requests_qs,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'manage_requests.html', context)


@login_required(login_url='login')
def approve_request(request, request_id):
    req = get_object_or_404(TechRefreshRequest, id=request_id)
    req.status = "Approved"
    req.save()
    messages.success(request, f"Request by {req.engineer.username} has been approved.")
    return redirect('manage_requests')


@login_required(login_url='login')
def reject_request(request, request_id):
    req = get_object_or_404(TechRefreshRequest, id=request_id)
    req.status = "Rejected"
    req.save()
    messages.warning(request, f"Request by {req.engineer.username} has been rejected.")
    return redirect('manage_requests')


@login_required(login_url='login')
def view_request_details(request, request_id):
    if request.user.role != 'TeamLead':
        messages.error(request, "You do not have permission to view this page.")
        return redirect('login')

    req = get_object_or_404(TechRefreshRequest, id=request_id)
    return render(request, 'view_request_details.html', {'req': req})


# ==============================
# 📈 REPORTS & EXPORTS
# ==============================
@login_required(login_url='login')
def reports(request):
    if request.user.role != 'TeamLead':
        return redirect('systemengineer_dashboard')

    requests_list = TechRefreshRequest.objects.all().order_by('-submitted_at')
    context = {'requests': requests_list}
    return render(request, 'reports.html', context)


@login_required(login_url='login')
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


@login_required(login_url='login')
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

#MAINTENANCE LOGS
@login_required
def maintenance_logs(request):
    logs = [
        {'item': 'Monitor', 'issue': 'Display flickering', 'date': '2025-10-10'},
        {'item': 'Keyboard', 'issue': 'Key stuck', 'date': '2025-10-12'},
    ]
    return render(request, 'maintenance_logs.html', {'logs': logs})

#ASSIGNED ITEMS
@login_required(login_url='login')
def assigned_items(request):
    # Mock data untuk test
    items = [
        {'name': 'Laptop Dell', 'status': 'In Use'},
        {'name': 'Mouse HP', 'status': 'Returned'},
    ]
    return render(request, 'assigned_items.html', {'items': items})


#send feedback
@login_required(login_url='login')
def send_feedback(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        # Simpan mesej atau hantar email / CloudDB dsb ikut keperluan
        # Buat sementara kita cuma bagi success message
        messages.success(request, "Feedback submitted successfully!")
        return redirect('systemengineer_dashboard')
    
    return render(request, 'send_feedback.html')


# ----------------------------
# 🔔 Notifications
# ----------------------------

def approve_request(request, request_id):
    req = Request.objects.get(id=request_id)
    req.status = 'Approved'
    req.save()

    # Hantar notifikasi kepada System Engineer
    Notification.objects.create(
        user=req.engineer,  # System Engineer yang buat request tu
        message=f"Your request '{req.id}' has been approved by Team Lead."
    )

    return redirect('manage_requests')


def reject_request(request, request_id):
    req = Request.objects.get(id=request_id)
    req.status = 'Rejected'
    req.save()

    # Contoh kalau Team Lead tambah komen
    comment = request.POST.get('comment', 'No comments provided.')

    # Hantar notifikasi kepada System Engineer
    Notification.objects.create(
        user=req.engineer,
        message=f"Your request '{req.id}' has been rejected by Team Lead. Comment: {comment}"
    )

    return redirect('manage_requests')

def notifications(request):
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Tandakan semua sebagai "read" bila dibuka
    user_notifications.update(is_read=True)

    return render(request, 'inventorySystem/notifications.html', {'notifications': user_notifications})
