from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.utils import timezone

# Model Engineer
class Engineer(models.Model):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    lan_id = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=50, default='Windows 10')

    def __str__(self):
        return self.name


# Model AssignedTask
class AssignedTask(models.Model):
    engineer = models.ForeignKey(Engineer, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    lan_id = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    replacement_type = models.CharField(
        max_length=50,
        choices=[
            ('PC (Asset Refresh)', 'PC (Asset Refresh)'),
            ('Laptop (Tech Refresh)', 'Laptop (Tech Refresh)'),
            ('RAM (Parts Upgrade)', 'RAM (Parts Upgrade)')
        ],
    )
    assigned_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.engineer.name} - {self.replacement_type}"

# ======================================================
# 1. CUSTOM USER MODEL
# ======================================================
class User(AbstractUser):
    ROLE_CHOICES = [
        ('TeamLead', 'Team Lead'),
        ('SystemEngineer', 'System Engineer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SystemEngineer')

    def save(self, *args, **kwargs):
        # Auto-assign TeamLead role if superuser
        if self.is_superuser:
            self.role = 'TeamLead'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"


# ======================================================
# 2. INVENTORY MODEL
# ======================================================
class Inventory(models.Model):
    CONDITION_CHOICES = [
        ('Good', 'Good'),
        ('Faulty', 'Faulty'),
        ('In Use', 'In Use'),
        ('Returned', 'Returned'),
        ('Damaged', 'Damaged'),
    ]

    item_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    location = models.CharField(max_length=100)

    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_inventory'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} ({self.condition})"


# ======================================================
# 3. REQUEST MODEL
# ======================================================
class Request(models.Model):
    TYPE_CHOICES = [
        ('Asset Refresh', 'Asset Refresh'),
        ('Parts Upgrade', 'Parts Upgrade'),
        ('Tech Refresh', 'Tech Refresh'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    FORMAT_STATUS_CHOICES = [
        ('Formatted', 'Formatted'),
        ('Not Formatted', 'Not Formatted'),
    ]
    UPLOAD_STATUS_CHOICES = [
        ('Uploaded', 'Uploaded'),
        ('Not Yet', 'Not Yet'),
    ]

    engineer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    location = models.CharField(max_length=100)
    user = models.CharField(max_length=100)

    old_barcode = models.CharField(max_length=100, blank=True, null=True)
    new_barcode = models.CharField(max_length=100, blank=True, null=True)
    old_serial = models.CharField(max_length=100, blank=True, null=True)
    new_serial = models.CharField(max_length=100, blank=True, null=True)
    old_ip = models.GenericIPAddressField(blank=True, null=True)
    new_ip = models.GenericIPAddressField(blank=True, null=True)
    new_mac = models.CharField(max_length=50, blank=True, null=True)
    old_hostname = models.CharField(max_length=100, blank=True, null=True)
    new_hostname = models.CharField(max_length=100, blank=True, null=True)

    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    rescheduled_date = models.DateField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    format_status = models.CharField(max_length=20, choices=FORMAT_STATUS_CHOICES, blank=True, null=True)
    upload_status = models.CharField(max_length=20, choices=UPLOAD_STATUS_CHOICES, default='Not Yet')

    reason_not_formatted = models.TextField(blank=True, null=True)
    reason_not_uploaded = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    proof = models.FileField(upload_to='', blank=True, null=True)

    assigned_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='approver_requests',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} - {self.engineer.username} ({self.status})"


# ======================================================
# 4. TECH REFRESH MODEL
# ======================================================
class TechRefresh(models.Model):
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Rescheduled', 'Rescheduled'),
    ]
    FORMAT_STATUS = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
    ]
    UPLOAD_STATUS = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
    ]

    engineer_name = models.CharField(max_length=100)
    user_name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)

    old_hostname = models.CharField(max_length=100)
    new_hostname = models.CharField(max_length=100)
    old_serial_number = models.CharField(max_length=100)
    new_serial_number = models.CharField(max_length=100)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    date_if_rescheduled = models.DateField(null=True, blank=True)

    format_status = models.CharField(max_length=20, choices=FORMAT_STATUS, default='Pending')
    reason_not_formatted = models.TextField(null=True, blank=True)

    upload_status = models.CharField(max_length=20, choices=UPLOAD_STATUS, default='Pending')
    reason_not_uploaded = models.TextField(null=True, blank=True)

    remarks = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.engineer_name} - {self.user_name}"


# ======================================================
# 5. TECH REFRESH REQUEST MODEL
# ======================================================
class TechRefreshRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    engineer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    old_barcode = models.CharField(max_length=100, blank=True, null=True)
    new_barcode = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)
    proof = models.FileField(upload_to='proofs/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.engineer.username} - {self.status}"


# ======================================================
# 6. TASK MODEL
# ======================================================
class Task(models.Model):
    STATUS_CHOICES = [
        ('Assigned', 'Assigned'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Overdue', 'Overdue'),
    ]

    engineer = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Assigned')

    related_request = models.ForeignKey(
        Request,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_tasks'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


# ======================================================
# 7. NOTIFICATION MODEL
# ======================================================
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To: {self.user.username} - {self.message[:50]}"


# ======================================================
# 8. ASSIGNED TASK MODEL (FINAL, CLEAN)
# ======================================================
class AssignedTask(models.Model):
    engineer = models.ForeignKey(User, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    lan_id = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100)
    os = models.CharField(max_length=50)
    replacement_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='Pending')
    remarks = models.TextField(blank=True, null=True)
    proof = models.FileField(upload_to='proofs/', blank=True, null=True)
    assigned_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.engineer.username}"


class TaskHistory(models.Model):
    engineer = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(AssignedTask, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    remarks = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.engineer.username} - {self.status}"

class Submission(models.Model):
    engineer = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(AssignedTask, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default="Pending Verification")
    submitted_date = models.DateTimeField(auto_now_add=True)


