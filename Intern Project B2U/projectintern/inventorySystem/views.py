from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, TechRefresh


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

            # Normalize role matching (case-insensitive)
            role = user.role.lower()

            if role == "teamlead":
                return redirect("teamlead_dashboard")
            elif role == "systemengineer":
                return redirect("engineer_dashboard")
            else:
                messages.error(request, "Invalid role assigned to this account.")
                logout(request)
                return redirect("login")
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
        return redirect('tech-refresh-list')

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
    # Restrict access: Only Team Leads can access this page
    if request.user.role.lower() != 'teamlead':
        return redirect('engineer_dashboard')

    total_engineers = User.objects.filter(role__iexact='SystemEngineer').count()
    total_tasks = TechRefresh.objects.count()
    pending_tasks = TechRefresh.objects.filter(status__iexact='Pending').count()
    completed_tasks = TechRefresh.objects.filter(status__iexact='Completed').count()

    context = {
        'total_engineers': total_engineers,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
    }
    return render(request, 'teamlead_dashboard.html', context)


@login_required(login_url='login')
def engineer_dashboard(request):
    # Restrict access: Only Engineers can access this page
    if request.user.role.lower() != 'systemengineer':
        return redirect('teamlead_dashboard')

    return render(request, "engineer_dashboard.html")


@login_required(login_url='login')
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


@login_required(login_url='login')
def user_dashboard(request):
    return render(request, 'user_dashboard.html')

@login_required(login_url='login')
def manage_engineers(request):
    if request.user.role.lower() != 'teamlead':
        return redirect('engineer_dashboard')

    engineers = User.objects.filter(role__iexact='SystemEngineer')
    return render(request, 'manage_engineers.html', {'engineers': engineers})

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
    completed = TechRefresh.objects.filter(status__iexact='Completed').count()
    pending = TechRefresh.objects.filter(status__iexact='Pending').count()
    rescheduled = TechRefresh.objects.filter(status__iexact='Rescheduled').count()

    context = {
        'total_tasks': total_tasks,
        'completed': completed,
        'pending': pending,
        'rescheduled': rescheduled,
    }
    return render(request, 'reports.html', context)



