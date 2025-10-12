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

    #Manage User
    path('manage-users/', views.manage_users, name='manage_users'),
    path('add-user/', views.add_user, name='add_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('dashboard/teamlead/manage-engineers/edit/<int:engineer_id>/', 
     views.edit_engineer, name='edit_engineer'),
    path('dashboard/teamlead/manage-engineers/delete/<int:engineer_id>/', views.delete_engineer, name='delete_engineer'),


    #Manage inventory
    #path('inventory/', views.inventory_list, name='inventory_list'),
    #path('inventory/add/', views.add_inventory, name='add_inventory'),
    #path('inventory/edit/<int:item_id>/', views.edit_inventory, name='edit_inventory'),
    #path('inventory/delete/<int:item_id>/', views.delete_inventory, name='delete_inventory'),






]
