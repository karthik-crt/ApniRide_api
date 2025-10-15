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
    is_available = models.BooleanField(default=True)  # For drivers: available for rides
    fcm_token = models.TextField(null=True, blank=True)
    last_location_update = models.DateTimeField(auto_now=True)
    approval_state = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default='pending'
    )
    account_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('blocked', 'Blocked'),
        ],
        default='active'
    )
    suspended_until = models.DateTimeField(null=True, blank=True)

    @property
    def is_suspended(self):
        """Check if user is currently suspended and auto-reactivate if expired"""
        if self.account_status == "suspended" and self.suspended_until:
            if timezone.now() < self.suspended_until:
                return True
            else:
                # Auto-reactivate once suspension period is over
                self.account_status = "active"
                self.suspended_until = None
                self.save(update_fields=["account_status", "suspended_until"])
                return False
        return False
    
class Ride(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('arrived','Arrived'),
        ('ongoing','Ongoing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, related_name='rides', on_delete=models.CASCADE)
    driver = models.ForeignKey(User, related_name='assigned_rides', null=True, blank=True, on_delete=models.SET_NULL)
    booking_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    pickup = models.CharField(max_length=255)
    drop = models.CharField(max_length=255)
    pickup_lat = models.FloatField(null=True, blank=True)
    pickup_lng = models.FloatField(null=True, blank=True)
    drop_lat = models.FloatField(null=True, blank=True)
    drop_lng = models.FloatField(null=True, blank=True)
    pickup_mode = models.CharField(max_length=10, default="NOW", choices=[("NOW", "now"), ("LATER", "later")])
    pickup_time = models.DateTimeField(default=timezone.now)
    distance_km = models.FloatField(default=0)  
    vehicle_type = models.CharField(max_length=20,default='Car')
    payment_type = models.CharField(max_length=20, null=True, blank=True)
    fare = models.FloatField(default=0)  
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    driver_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    fare_estimate = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    driver_to_pickup_km = models.FloatField(default=0)
    driver_incentive = models.FloatField(default=0)  
    customer_reward = models.JSONField(default=dict, blank=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_driver = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_bookings')
    completed = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
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
    fcm_token = models.TextField(null=True, blank=True)   # add this
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
    max_distance = models.FloatField(null=True, blank=True)  
    per_km_rate = models.FloatField()  
    gst_percentage = models.FloatField(default=0)  # e.g. 5, 12, 18
    commission_percentage = models.FloatField(default=0)  # e.g. 10, 20
    
    def __str__(self):
        if self.max_distance:
            return f"{self.vehicle_type}: {self.min_distance}-{self.max_distance} km → ₹{self.per_km_rate}/km"
        return f"{self.vehicle_type}: {self.min_distance}+ km → ₹{self.per_km_rate}/km"
    
    def calculate_fare(self, distance):
        """
        Calculate fare breakdown for a given distance.
        Returns a dict with detailed breakdown for user, driver, and company.
        """
        if self.max_distance is None or (self.min_distance <= distance <= self.max_distance):
            # Calculate base components
            base_fare = distance * self.per_km_rate
            commission_amount = (base_fare * self.commission_percentage) / 100
            driver_earnings = base_fare - commission_amount
            
            # GST is applied to the base fare (the service value)
            gst_amount = (base_fare * self.gst_percentage) / 100
            
            # What user pays (base fare + GST)
            total_user_pays = base_fare + gst_amount

            return {
                "distance": distance,
                "base_fare": base_fare,
                "gst_amount": gst_amount,
                "commission_amount": commission_amount,
                "driver_earnings": driver_earnings,
                "total_user_pays": total_user_pays,
                "company_revenue": commission_amount,  # Company keeps commission
                "government_revenue": gst_amount       # GST goes to government
            }
        return None
    
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


class DriverRating(models.Model):
    ride = models.OneToOneField(
        Ride,
        on_delete=models.CASCADE,
        related_name="driver_rating"  # <-- changed from "rating"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="given_ratings"
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_ratings"
    )
    stars = models.PositiveSmallIntegerField(default=5)  # 1 to 5
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)   

from decimal import Decimal


class DriverWallet(models.Model):
    driver = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    updated_at = models.DateTimeField(auto_now=True)

    def deposit(self, amount, description="Deposit", transaction_type="deposit"):
        """Add amount to wallet safely and log transaction"""
        if not isinstance(self.balance, Decimal):
            self.balance = Decimal(self.balance)
        if not isinstance(amount, Decimal):
            amount = Decimal(amount)

        self.balance += amount
        self.save(update_fields=["balance", "updated_at"])
        
        # Log transaction
        UserWalletTransaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            balance_after=self.balance
        )
        
        return self.balance

    def withdraw(self, amount, description="Withdrawal", transaction_type="withdrawal"):
        """Withdraw if balance is sufficient and log transaction"""
        print("Wallet payment failed. Please try another method",dir(self))
        if not isinstance(self.balance, Decimal):
            self.balance = Decimal(self.balance)
        if not isinstance(amount, Decimal):
            amount = Decimal(amount)

        if self.balance >= amount:
            self.balance -= amount
            self.save(update_fields=["balance", "updated_at"])
            
            # Log transaction
            UserWalletTransaction.objects.create(
                wallet=self,
                transaction_type=transaction_type,
                amount=-amount,  # Negative for withdrawal
                description=description,
                balance_after=self.balance
            )
            
            return self.balance
        raise ValueError("Insufficient balance")

    def __str__(self):
        return f"{self.driver.username}'s Wallet - Balance: {self.balance}"


class UserWalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('cashback', 'Cashback'),
        ('reward', 'Reward'),
        ('ride_payment', 'Ride Payment Debited'),
        ('refund', 'Refund Credited'),
    ]
    
    wallet = models.ForeignKey(DriverWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Positive for credit, negative for debit
    description = models.TextField(blank=True, null=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    related_ride = models.ForeignKey('Ride', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_wallet_transactions')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} - ₹{self.amount} (Balance: {self.balance_after}) for {self.wallet.driver.username}"
    
from datetime import timedelta,date

class DriverIncentiveProgress(models.Model):
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='incentive_progress'
    )
    incentive_rule = models.ForeignKey(
        DriverIncentive,
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    travelled_distance = models.FloatField(default=0.0)
    rides_completed = models.IntegerField(default=0)
    earned = models.BooleanField(default=False)
    start_date = models.DateField(auto_now_add=True)
    
    @property
    def progress_percent(self):
        target = self.incentive_rule.days or 1
        percent = (self.rides_completed / target) * 100
        return round(min(percent, 100), 1)

    def __str__(self):
        return f"{self.driver} - {self.incentive_rule.ride_type} ({self.progress_percent}%)"




#Admin wallet


from django.db import models
from django.conf import settings
from decimal import Decimal

class AdminWallet(models.Model):
    """Admin wallet to manage platform funds, tracking Commission and GST separately"""
    name = models.CharField(max_length=100, default="Platform Wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_commission = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_gst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def deposit(self, amount, description="Deposit", transaction_type="deposit"):
        if not isinstance(amount, Decimal):
            amount = Decimal(amount)
        self.balance += amount
        self.save(update_fields=["balance", "updated_at"])
        AdminWalletTransaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            balance_after=self.balance
        )
        return self.balance

    def withdraw(self, amount, description="Withdrawal", transaction_type="withdrawal"):
        if not isinstance(amount, Decimal):
            amount = Decimal(amount)
        if self.balance >= amount:
            self.balance -= amount
            self.save(update_fields=["balance", "updated_at"])
            AdminWalletTransaction.objects.create(
                wallet=self,
                transaction_type=transaction_type,
                amount=-amount,
                description=description,
                balance_after=self.balance
            )
            return self.balance
        raise ValueError("Insufficient balance")

    def collect_commission(self, amount, ride=None, description="Commission Collected"):
        if not isinstance(amount, Decimal):
            amount = Decimal(amount)
        self.total_commission += amount
        self.balance += amount
        self.save(update_fields=["balance", "total_commission", "updated_at"])
        AdminWalletTransaction.objects.create(
            wallet=self,
            transaction_type="commission",
            amount=amount,
            description=description,
            balance_after=self.balance,
            related_ride=ride
        )
        return self.balance

    def collect_gst(self, amount, ride=None, description="GST Collected"):
        if not isinstance(amount, Decimal):
            amount = Decimal(amount)
        self.total_gst += amount
        self.balance += amount
        self.save(update_fields=["balance", "total_gst", "updated_at"])
        AdminWalletTransaction.objects.create(
            wallet=self,
            transaction_type="gst",
            amount=amount,
            description=description,
            balance_after=self.balance,
            related_ride=ride
        )
        return self.balance

    def refund_to_user(self, amount, user_wallet, description="Refund", ride=None, refund_gst=Decimal("0.00"), refund_commission=Decimal("0.00")):
        """Refund from admin wallet to user wallet, optionally splitting GST + commission"""
        if not isinstance(amount, Decimal):
            amount = Decimal(amount)

        # Deduct GST and Commission from admin wallet
        if refund_commission > 0:
            self.total_commission -= refund_commission
        if refund_gst > 0:
            self.total_gst -= refund_gst

        self.withdraw(
            amount=amount,
            description=f"Refund to {user_wallet.driver.username}: {description}",
            transaction_type="refund_payout"
        )

        # Deposit into user wallet
        user_wallet.deposit(
            amount=amount,
            description=f"Refund: {description}",
            transaction_type="refund"
        )
        return self.balance

    def __str__(self):
        return f"{self.name} - Balance: ₹{self.balance}"

class AdminWalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('commission', 'Commission'),
        ('gst', 'GST'),
        ('refund_payout', 'Refund Payout'),
        ('operational_expense', 'Operational Expense'),
        ('revenue', 'Revenue'),
    ]

    wallet = models.ForeignKey(AdminWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Positive for credit, negative for debit
    description = models.TextField(blank=True, null=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    related_ride = models.ForeignKey('Ride', on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_wallet_transactions')
    related_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_transactions')

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Admin Wallet Transaction"
        verbose_name_plural = "Admin Wallet Transactions"

    def __str__(self):
        return f"Admin {self.transaction_type} - ₹{self.amount} (Balance: {self.balance_after})"
