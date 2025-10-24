from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# -------------------------
# CUSTOM USER MODEL
# -------------------------
class User(AbstractUser):
    ROLE_CHOICES = [
        ('TeamLead', 'Team Lead'),
        ('SystemEngineer', 'System Engineer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SystemEngineer')

    def save(self, *args, **kwargs):
        # Automatically assign TeamLead role if this user is a superuser
        if self.is_superuser:
            self.role = 'TeamLead'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"


# -------------------------
# TECH REFRESH MODEL
# -------------------------
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


# -------------------------
# INVENTORY MODEL
# -------------------------
class Inventory(models.Model):
    item_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    quantity = models.IntegerField(default=0)
    condition = models.CharField(max_length=50, choices=[
        ('Good', 'Good'),
        ('Faulty', 'Faulty'),
        ('In Use', 'In Use'),
        ('Returned', 'Returned'),
        ('Damaged', 'Damaged')
    ])
    location = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_inventory'
    )

    def __str__(self):
        return self.item_name


# -------------------------
# REQUEST MODEL
# -------------------------
class Request(models.Model):
    TYPE_CHOICES = [
        ('Tag Refresh', 'Tag Refresh'),
        ('Asset Refresh', 'Asset Refresh'),
        ('Tech Refresh', 'Tech Refresh'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    engineer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    location = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    old_barcode = models.CharField(max_length=100, blank=True, null=True)
    new_barcode = models.CharField(max_length=100, blank=True, null=True)
    old_serial = models.CharField(max_length=100, blank=True, null=True)
    new_serial = models.CharField(max_length=100, blank=True, null=True)
    old_ip = models.CharField(max_length=50, blank=True, null=True)
    new_ip = models.CharField(max_length=50, blank=True, null=True)
    new_mac = models.CharField(max_length=50, blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)
    proof = models.FileField(upload_to='proofs/', blank=True, null=True)
    assigned_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='approver', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    old_hostname = models.CharField(max_length=100, blank=True, null=True)
    new_hostname = models.CharField(max_length=100, blank=True, null=True)

    rescheduled_date = models.DateField(blank=True, null=True)

    FORMAT_STATUS_CHOICES = [
        ('Formatted', 'Formatted'),
        ('Not Formatted', 'Not Formatted'),
    ]
    format_status = models.CharField(max_length=20, choices=FORMAT_STATUS_CHOICES, blank=True, null=True)
    reason_not_formatted = models.TextField(blank=True, null=True)

    UPLOAD_STATUS_CHOICES = [
        ('Uploaded', 'Uploaded'),
        ('Not Yet', 'Not Yet'),
    ]
    upload_status = models.CharField(max_length=20, choices=UPLOAD_STATUS_CHOICES, default='Not Yet')
    reason_not_uploaded = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.type} - {self.engineer.username} ({self.status})"


# -------------------------
# TECH REFRESH REQUEST MODEL
# -------------------------
class TechRefreshRequest(models.Model):
    engineer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    old_barcode = models.CharField(max_length=100, blank=True, null=True)
    new_barcode = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, default='Pending')
    remarks = models.TextField(blank=True, null=True)
    proof = models.FileField(upload_to='proofs/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.engineer.username} - {self.status}"


# -------------------------
# NOTIFICATION MODEL
# -------------------------
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"
