# urls.py
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

    # Tech Refresh
    path('tech-refresh/add/', views.add_tech_refresh, name='add_tech_refresh'),
    path('tech-refresh/', views.tech_refresh_list, name='tech_refresh_list'),

    # Manage Engineers (Team Lead)
    path('dashboard/teamlead/manage-engineers/', views.manage_engineers, name='manage_engineers'),
    path('dashboard/teamlead/manage-engineers/edit/<int:engineer_id>/', views.edit_engineer, name='edit_engineer'),
    path('dashboard/teamlead/manage-engineers/delete/<int:engineer_id>/', views.delete_engineer, name='delete_engineer'),

    # Manage Requests (Team Lead)
    path('dashboard/teamlead/manage-requests/', views.manage_requests, name='manage_requests'),
    path('dashboard/teamlead/request/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('dashboard/teamlead/request/<int:request_id>/reject/', views.reject_request, name='reject_request'),

    # Engineer Requests
    path('dashboard/engineer/create-request/', views.create_request, name='create_request'),

    # Team Lead pages
    path('dashboard/teamlead/approvals/', views.approvals, name='approvals'),
    path('dashboard/teamlead/all-records/', views.all_records, name='all_records'),
    path('dashboard/teamlead/reports/', views.reports, name='reports'),

    
]
