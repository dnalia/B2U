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

from .models import User, TechRefresh, TechRefreshRequest

# ==============================
# 🔐 LOGIN & LOGOUT
# ==============================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            role = user.role.lower()
            if role == "teamlead":
                return redirect("teamlead_dashboard")
            elif role == "systemengineer":
                return redirect("engineer_dashboard")
            else:
                messages.error(request, "Invalid role assigned.")
                logout(request)
        else:
            messages.error(request, "Invalid username or password.")
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
# 📊 DASHBOARDS
# ==============================
@login_required(login_url='login')
def teamlead_dashboard(request):
    if request.user.role.lower() != 'teamlead':
        return redirect('engineer_dashboard')

    context = {
        'total_engineers': User.objects.filter(role__iexact='SystemEngineer').count(),
        'total_tasks': TechRefresh.objects.count(),
        'pending_tasks': TechRefresh.objects.filter(status__iexact='Pending').count(),
        'completed_tasks': TechRefresh.objects.filter(status__iexact='Completed').count(),
    }
    return render(request, 'teamlead_dashboard.html', context)


@login_required(login_url='login')
def engineer_dashboard(request):
    if request.user.role.lower() != 'systemengineer':
        return redirect('teamlead_dashboard')

    requests_list = TechRefreshRequest.objects.filter(engineer=request.user).order_by('-submitted_at')
    return render(request, 'engineer_dashboard.html', {'requests': requests_list})


# ==============================
# 👥 MANAGE ENGINEERS
# ==============================
@login_required(login_url='login')
def manage_engineers(request):
    if request.user.role.lower() != 'teamlead':
        return redirect('engineer_dashboard')

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

    engineers = User.objects.filter(role__iexact='SystemEngineer')
    return render(request, "manage_engineers.html", {"engineers": engineers})


@login_required(login_url='login')
def edit_engineer(request, engineer_id):
    engineer = get_object_or_404(User, id=engineer_id, role__iexact='SystemEngineer')
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
    engineer = get_object_or_404(User, id=engineer_id, role__iexact='SystemEngineer')
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
        return redirect('engineer_dashboard')
    return render(request, 'create_request.html')


@login_required(login_url='login')
def manage_requests(request):
    if request.user.role.lower() != 'teamlead':
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
    if request.user.role.lower() != 'teamlead':
        messages.error(request, "You do not have permission to view this page.")
        return redirect('login')

    req = get_object_or_404(TechRefreshRequest, id=request_id)
    return render(request, 'view_request_details.html', {'req': req})


# ==============================
# 📈 REPORTS & EXPORTS
# ==============================
@login_required(login_url='login')
def reports(request):
    if request.user.role.lower() != 'teamlead':
        return redirect('engineer_dashboard')

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

# 🧑‍🔧 System Engineer Dashboard
@login_required
def systemengineer_dashboard(request):
    context = {
        'assigned_items_count': 8,
        'in_use_count': 3,
        'returned_count': 2,
        'damaged_count': 1,
    }
    return render(request, 'systemengineer_dashboard.html', context)


# 📥 View Inventory List
@login_required
def inventory_list(request):
    items = [
        {'name': 'Laptop Dell', 'status': 'Available'},
        {'name': 'Monitor Acer', 'status': 'In Use'},
        {'name': 'Keyboard Logitech', 'status': 'Returned'},
    ]
    return render(request, 'inventory_list.html', {'items': items})


# 🛠 Update Inventory Status
@login_required
def update_status(request):
    items = [
        {'name': 'Laptop A', 'status': 'In Use'},
        {'name': 'Printer B', 'status': 'Returned'},
        {'name': 'Router C', 'status': 'Damaged'},
    ]
    return render(request, 'update_status.html', {'items': items})


# 📝 Submit Maintenance Logs
@login_required
def maintenance_logs(request):
    logs = [
        {'item': 'Monitor', 'issue': 'Display flickering', 'date': '2025-10-10'},
        {'item': 'Keyboard', 'issue': 'Key stuck', 'date': '2025-10-12'},
    ]
    return render(request, 'maintenance_logs.html', {'logs': logs})


# 🔍 Track Assigned Items
@login_required
def assigned_items(request):
    items = [
        {'name': 'Laptop Dell', 'status': 'In Use'},
        {'name': 'Mouse HP', 'status': 'Returned'},
    ]
    return render(request, 'assigned_items.html', {'items': items})


# 💬 Send Feedback
@login_required
def send_feedback(request):
    return render(request, 'send_feedback.html')


