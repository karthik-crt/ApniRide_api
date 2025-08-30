from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

import random
APPROVAL_CHOICES = [
    ('pending', 'Pending Approval'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]
class User(AbstractUser):
    is_driver = models.IntegerField(default=0, blank=True, null=True)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=50, default='', blank=True, null=True)
    is_user = models.IntegerField(default=0, blank=True, null=True)
    profile_photo = models.FileField(upload_to='profile_photos/', null=True, blank=True)
    emergency_contact_number = models.CharField(max_length=15, null=True, blank=True)
    driving_license = models.FileField(upload_to='documents/driving_license/', null=True, blank=True)
    rc_book = models.FileField(upload_to='documents/rc_book/', null=True, blank=True)
    aadhaar = models.FileField(upload_to='documents/aadhaar/', null=True, blank=True)
    pan_card = models.FileField(upload_to='documents/pan_card/', null=True, blank=True)
    vehicle_type = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    plate_number = models.CharField(max_length=20, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True) 
    is_online = models.BooleanField(default=False)
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)
    preferred_payment_method = models.CharField(max_length=50, default='', blank=True, null=True)
    approval_state = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default='pending'
    )
    
class Ride(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, related_name='rides', on_delete=models.CASCADE)
    driver = models.ForeignKey(User, related_name='assigned_rides', null=True, blank=True, on_delete=models.SET_NULL)
    pickup = models.CharField(max_length=255)
    drop = models.CharField(max_length=255)
    pickup_lat = models.FloatField(null=True, blank=True)
    pickup_lng = models.FloatField(null=True, blank=True)
    drop_lat = models.FloatField(null=True, blank=True)
    drop_lng = models.FloatField(null=True, blank=True)
    pickup_mode = models.CharField(max_length=10, default="NOW", choices=[("NOW", "Ride Now"), ("LATER", "Ride Later")])
    pickup_time = models.DateTimeField(default=timezone.now)
    distance_km = models.FloatField(default=0)  
    vehicle_type = models.CharField(max_length=20,default='Car')
    fare = models.FloatField(default=0)  
    fare_estimate = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    driver_incentive = models.FloatField(default=0)  
    customer_reward = models.JSONField(default=dict, blank=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    coupon_applied = models.CharField(max_length=20, null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    rejected_by = models.ManyToManyField(User, related_name='rejected_rides', blank=True)

    def __str__(self):
        return f"Ride {self.id} - {self.user.username} ({self.status})"


class DriverLocation(models.Model):
    driver = models.OneToOneField(User, on_delete=models.CASCADE, related_name='location')
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

# models.py
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('UPI', 'UPI'),
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ("WALLET", "Wallet"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=255)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='UPI')
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Ride {self.ride.id} - {self.user.username}"
    
    
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    def is_valid(self):
        return not self.is_used and (timezone.now() - self.created_at).total_seconds() < 300
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} -> {self.user.username}"

class FareRule(models.Model):
    vehicle_type = models.CharField(max_length=50)
    min_distance = models.FloatField(default=0)   # e.g. 0, 5, 10
    max_distance = models.FloatField(null=True, blank=True)  # None = "Above"
    per_km_rate = models.FloatField()  # e.g. 8, 9, 10, etc.

    def __str__(self):
        if self.max_distance:
            return f"{self.vehicle_type}: {self.min_distance}-{self.max_distance} km → ₹{self.per_km_rate}/km"
        return f"{self.vehicle_type}: {self.min_distance}+ km → ₹{self.per_km_rate}/km"
    
# Reward based on distance
class DistanceReward(models.Model):
    vehicle_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Enter vehicle type (admin can add new types dynamically)"
    )
    min_distance = models.FloatField()
    max_distance = models.FloatField(null=True, blank=True)  
    cashback = models.FloatField(default=0)
    water_bottles = models.IntegerField(default=0)
    tea = models.IntegerField(default=0)
    discount = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.min_distance}-{self.max_distance} km Reward"

# Tourism special offers
class TourismOffer(models.Model):
    name = models.CharField(max_length=100)
    discount = models.CharField(max_length=100, blank=True, null=True)
    tea = models.IntegerField(default=0)
    water_bottles = models.IntegerField(default=0)
    long_term_days = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
class IntegrationSettings(models.Model):
    maps_api_key = models.CharField(max_length=255, blank=True, null=True)
    sms_api_key = models.CharField(max_length=255, blank=True, null=True)
    payment_api_key = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Integration Settings"
class DriverIncentive(models.Model):
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="incentives"
    )
    ride_type = models.CharField(max_length=20)
    distance = models.FloatField(null=True, blank=True)
    days = models.IntegerField(null=True, blank=True)
    driver_incentive = models.DecimalField(max_digits=10, decimal_places=2)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.driver:
            return f"Incentive for {self.driver} ({self.ride_type})"
        return f"Global Incentive ({self.ride_type})"
class RefundRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='refund_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests')
    refund_amount = models.FloatField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund {self.id} for Ride {self.ride.id} - {self.status}"
    
class VehicleType(models.Model):
    name = models.CharField(max_length=50, unique=True)  
    description = models.TextField(blank=True, null=True)  
    vehicleImage = models.FileField(upload_to='vehicle_types/', null=True, blank=True)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2,default=0.00) 
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)  
    per_minute_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    seating_capacity = models.IntegerField()  
    luggage_capacity = models.IntegerField(default=0)  
    is_active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return self.name    
    
class Coupon(models.Model):
    """Coupon Model"""
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    discount_percent = models.PositiveIntegerField(default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField()

    def __str__(self):
        return self.code    
    
class Commission(models.Model):
    """Admin Commission from Driver"""
    driver = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.OneToOneField(Ride, on_delete=models.CASCADE)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commission-{self.booking.id}"    