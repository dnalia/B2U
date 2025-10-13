from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import User, TechRefresh, TechRefreshRequest


# ==============================
# 🔐 LOGIN & LOGOUT
# ==============================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
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

    requests = TechRefreshRequest.objects.filter(engineer=request.user).order_by('-submitted_at')
    return render(request, 'engineer_dashboard.html', {'requests': requests})


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

    requests_list = TechRefreshRequest.objects.all().order_by('-submitted_at')
    return render(request, 'manage_requests.html', {'requests': requests_list})


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


# ==============================
# 📈 REPORTS / APPROVALS / RECORDS
# ==============================
@login_required(login_url='login')
def approvals(request):
    if request.user.role.lower() != 'teamlead':
        return redirect('engineer_dashboard')
    return render(request, 'approvals.html')


@login_required(login_url='login')
def all_records(request):
    if request.user.role.lower() != 'teamlead':
        return redirect('engineer_dashboard')

    records = TechRefresh.objects.all()
    return render(request, 'all_records.html', {'records': records})


@login_required(login_url='login')
def reports(request):
    if request.user.role.lower() != 'teamlead':
        return redirect('engineer_dashboard')

    total_tasks = TechRefresh.objects.count()
    context = {
        'total_tasks': total_tasks,
        'completed': TechRefresh.objects.filter(status='Completed').count(),
        'pending': TechRefresh.objects.filter(status='Pending').count(),
        'rescheduled': TechRefresh.objects.filter(status='Rescheduled').count(),
    }
    return render(request, 'reports.html', context)
