from django.db import models

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('TeamLead', 'Team Lead'),
        ('SystemEngineer', 'System Engineer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SystemEngineer')

    def __str__(self):
        return f"{self.username} ({self.role})"

    

class TechRefresh(models.Model):
    engineer_name = models.CharField(max_length=100)
    user_name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    
    old_hostname = models.CharField(max_length=100)
    new_hostname = models.CharField(max_length=100)
    
    old_serial_number = models.CharField(max_length=100)
    new_serial_number = models.CharField(max_length=100)

    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Rescheduled', 'Rescheduled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    date_if_rescheduled = models.DateField(null=True, blank=True)

    FORMAT_STATUS = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
    ]
    format_status = models.CharField(max_length=20, choices=FORMAT_STATUS)

    reason_not_formatted = models.TextField(null=True, blank=True)

    UPLOAD_STATUS = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
    ]
    upload_status = models.CharField(max_length=20, choices=UPLOAD_STATUS)

    reason_not_uploaded = models.TextField(null=True, blank=True)

    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.engineer_name} - {self.user_name}"
