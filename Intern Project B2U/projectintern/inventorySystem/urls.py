from django.urls import path
from . import views  # <-- import module views

urlpatterns = [
    path('', views.homepage, name='homepage'), 
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('tech-refresh/add/', views.add_tech_refresh, name='add-tech-refresh'),
    path('tech-refresh/', views.tech_refresh_list, name='tech-refresh-list'),
    path('dashboard/user/', views.user_dashboard, name='user-dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin-dashboard'),

]
