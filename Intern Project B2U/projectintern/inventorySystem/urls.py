from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/teamlead/', views.teamlead_dashboard, name='teamlead_dashboard'),
    path('dashboard/systemengineer/', views.systemengineer_dashboard, name='systemengineer_dashboard'),
    path('tech-refresh/add/', views.add_tech_refresh, name='add_tech_refresh'),
    path('tech-refresh/', views.tech_refresh_list, name='tech_refresh_list'),
    path('dashboard/teamlead/manage-engineers/', views.manage_engineers, name='manage_engineers'),
    path('dashboard/teamlead/manage-engineers/edit/<int:engineer_id>/', views.edit_engineer, name='edit_engineer'),
    path('dashboard/teamlead/manage-engineers/delete/<int:engineer_id>/', views.delete_engineer, name='delete_engineer'),
    path('manage_requests/', views.manage_requests, name='manage_requests'),
    path('reports/export/pdf/', views.export_requests_pdf, name='export_requests_pdf'),
    path('request/<int:req_id>/details/', views.view_request_details, name='view_request_details'),
    path('dashboard/teamlead/reports/<int:request_id>/', views.report_details, name='report_details'),
    path('request/<int:req_id>/approve/', views.approve_request, name='approve_request'),
    path('request/<int:req_id>/reject/', views.reject_request, name='reject_request'),
    path('dashboard/systemengineer/create-request/', views.create_request, name='create_request'),
    path('dashboard/teamlead/reports/', views.reports, name='reports'),
    path('dashboard/teamlead/export/excel/', views.export_requests_excel, name='export_requests_excel'),
    path('dashboard/teamlead/export/pdf/', views.export_requests_pdf, name='export_requests_pdf'),
    path('dashboard/systemengineer/', views.systemengineer_dashboard, name='systemengineer_dashboard'),
    path('dashboard/systemengineer/create_task/', views.create_task, name='create_task'),
    path('dashboard/systemengineer/my_submissions/', views.my_submissions, name='my_submissions'),
    path('task/<int:task_id>/download/', views.download_task_pdf, name='download_task_pdf'),
    path('dashboard/systemengineer/my_submissions/<int:req_id>/view/', views.view_request_details, name='task_detail'),
    path('dashboard/systemengineer/my_submissions/<int:task_id>/download/', views.download_task_pdf, name='download_task_pdf'),
    path('dashboard/systemengineer/my_submissions/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('dashboard/systemengineer/my_submissions/<int:task_id>/cancel/', views.cancel_task, name='cancel_task'),
    path('dashboard/systemengineer/notifications/', views.notifications_view, name='notifications'),
    path('dashboard/systemengineer/notifications/mark/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('dashboard/systemengineer/update_status/<int:pk>/', views.update_status, name='update_status'),
    path('assign-task/', views.assign_task, name='assign_task'),
    path('assign-task/', views.assign_task, name='assign_task'),
    path('task-history/', views.task_history, name='task_history'),
    path('assign-task/', views.assign_task, name='assign_task'),
    path('task-history/<int:engineer_id>/', views.task_history, name='task_history'),
    path('engineer-tasks/', views.engineer_tasks, name='engineer_tasks'),
    path('systemengineer/create_task/', views.create_task, name='create_task'),
    #path('systemengineer/submit_task/', views.submit_task, name='submit_task'),
    path('systemengineer/submit_task/<int:task_id>/', views.submit_task, name='submit_task'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
