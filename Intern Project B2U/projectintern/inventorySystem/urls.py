from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.homepage, name='homepage'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('dashboard/teamlead/', views.teamlead_dashboard, name='teamlead_dashboard'),
    path('dashboard/systemengineer/', views.systemengineer_dashboard, name='systemengineer_dashboard'),

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
    path('view-request/<int:request_id>/', views.view_request_details, name='view_request_details'),
    path('request/<int:request_id>/details/', views.view_request_details, name='view_request_details'),

    # Engineer Requests
    path('dashboard/systemengineer/create-request/', views.create_request, name='create_request'),

    # Reports & Exports
    path('dashboard/teamlead/reports/', views.reports, name='reports'),
    path('dashboard/teamlead/export/excel/', views.export_requests_excel, name='export_requests_excel'),
    path('dashboard/teamlead/export/pdf/', views.export_requests_pdf, name='export_requests_pdf'),

    # Dashboard
    path('dashboard/systemengineer/', views.systemengineer_dashboard, name='systemengineer_dashboard'),

    # Create Task
    path('dashboard/systemengineer/create_task/', views.create_task, name='create_task'),

    # My Submissions
 # System Engineer Dashboard & Tasks
path('dashboard/systemengineer/', views.systemengineer_dashboard, name='systemengineer_dashboard'),
path('dashboard/systemengineer/create_task/', views.create_task, name='create_task'),
path('dashboard/systemengineer/my_submissions/', views.my_submissions, name='my_submissions'),
path('dashboard/systemengineer/notifications/', views.notifications, name='notifications'),
path('dashboard/systemengineer/update_status/<int:pk>/', views.update_status, name='update_status'),

    # Update Inventory Status
    path('dashboard/systemengineer/update_status/<int:pk>/', views.update_status, name='update_status'),

    # Notifications
    path('dashboard/systemengineer/notifications/', views.notifications, name='notifications'),


    # MAINTENANCE LOGS
    path('inventory/maintenance-logs/', views.maintenance_logs, name='maintenance_logs'),

    # ASSIGNED ITEMS
    path('inventory/assigned-items/', views.assigned_items, name='assigned_items'),

    # FEEDBACK
    path('inventory/send-feedback/', views.send_feedback, name='send_feedback'),
]
