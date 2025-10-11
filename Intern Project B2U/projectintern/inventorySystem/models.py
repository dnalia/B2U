from django.db import models

class AssetUpdate(models.Model):
    engineer_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    type = models.CharField(max_length=100)  # e.g. Asset Refresh
    user_name = models.CharField(max_length=100)

    old_pc_barcode = models.CharField(max_length=100, blank=True, null=True)
    old_monitor_barcode = models.CharField(max_length=100, blank=True, null=True)

    new_pc_barcode = models.CharField(max_length=100, blank=True, null=True)
    new_pc_serial_no = models.CharField(max_length=100, blank=True, null=True)
    new_monitor_barcode_no = models.CharField(max_length=100, blank=True, null=True)
    new_monitor_serial_no = models.CharField(max_length=100, blank=True, null=True)

    old_ip_address = models.CharField(max_length=50, blank=True, null=True)
    new_ip_address = models.CharField(max_length=50, blank=True, null=True)
    new_mac_address = models.CharField(max_length=100, blank=True, null=True)

    start_time = models.CharField(max_length=50)
    end_time = models.CharField(max_length=50)

    status = models.CharField(max_length=50)
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.engineer_name} - {self.location} - {self.status}"

class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username