from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')  # home page selepas login
        else:
            messages.error(request, "Username atau password salah")
    return render(request, 'login.html')

def homepage(request):
    return render(request, 'homepage.html') 