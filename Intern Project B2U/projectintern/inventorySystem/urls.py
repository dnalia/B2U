from django.urls import path
from . import views  # <-- import module views

urlpatterns = [
    path('', views.homepage, name='homepage'), 
    path('login/', views.login_view, name='login'),
]
