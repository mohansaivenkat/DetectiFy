from django.db import models
from django.contrib.auth import get_user_model
import uuid


User = get_user_model()

# ✅ Define this BEFORE the Product model
def generate_serial():
    return str(uuid.uuid4())

class Product(models.Model):
    product_name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200, blank=True)
    serial_number = models.CharField(max_length=200, unique=True, default=generate_serial)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    manufacture_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_genuine = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product_name} — {self.serial_number}"

class Report(models.Model):
    product_serial = models.CharField(max_length=200, blank=True)
    product_name = models.CharField(max_length=200, blank=True)
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    evidence_image = models.ImageField(upload_to='reports/', null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    
    STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"Report {self.id} — {self.product_name or self.product_serial}"
    
class CounterfeitSerial(models.Model):
    serial_number = models.CharField(max_length=200, unique=True)
    product_name = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    evidence_image = models.ImageField(upload_to='counterfeit/', null=True, blank=True)
    source_report = models.ForeignKey('Report', on_delete=models.SET_NULL, null=True, blank=True, related_name='counterfeit_entry')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='counterfeit_created_by')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Counterfeit — {self.serial_number}"