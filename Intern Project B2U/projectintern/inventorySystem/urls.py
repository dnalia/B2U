from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.homepage, name='homepage'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('dashboard/teamlead/', views.teamlead_dashboard, name='teamlead_dashboard'),
    path('dashboard/engineer/', views.engineer_dashboard, name='engineer_dashboard'),

    # Tech Refresh Forms
    path('tech-refresh/add/', views.add_tech_refresh, name='add-tech-refresh'),
    path('tech-refresh/', views.tech_refresh_list, name='tech-refresh-list'),

    # (Optional) Other dashboards if needed later
    path('dashboard/admin/', views.admin_dashboard, name='admin-dashboard'),
    path('dashboard/user/', views.user_dashboard, name='user-dashboard'),

    #Manage System Engineer 
    path('dashboard/teamlead/manage-engineers/', views.manage_engineers, name='manage_engineers'),

    #Approvals
    path('dashboard/teamlead/approvals/', views.approvals, name='approvals'),

    #All rec
    path('dashboard/teamlead/all-records/', views.all_records, name='all_records'),

    #report team lead part
    path('dashboard/teamlead/reports/', views.reports, name='reports'),




]
