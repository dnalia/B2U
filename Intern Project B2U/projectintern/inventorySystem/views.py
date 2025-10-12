from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from .models import User,TechRefresh
from django.contrib.auth.decorators import login_required


def logout_view(request):
    logout(request)
    return redirect('login')  # tukar kalau nama login kau lain


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        selected_role = request.POST.get('role')  # Get the role from dropdown

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if the selected role matches the user's role in the database
            if user.role == selected_role:
                login(request, user)
                if user.role == 'TeamLead':
                    return redirect('admin-dashboard')
                else:
                    return redirect('user-dashboard')
            else:
                messages.error(request, "Selected role does not match your account role.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')




def homepage(request):
    return render(request, 'homepage.html') 

@login_required(login_url='login')  # 👈 user kena login dulu
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


@login_required(login_url='login')  # 👈 access list pun kena login
def tech_refresh_list(request):
    records = TechRefresh.objects.all()
    return render(request, 'tech_refresh_list.html', {'records': records})

@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

@login_required
def user_dashboard(request):
    return render(request, 'user_dashboard.html')