from rest_framework import serializers
from .models import User, Ride, DriverLocation, Payment, OTP,IntegrationSettings
from .models import *

class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = '__all__'
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class AdminRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        # This will actually create a superuser
        user = User.objects.create_superuser(**validated_data)
        return user

class UserWalletHistorySerializer(serializers.ModelSerializer):
    customer_reward = serializers.SerializerMethodField()
    booking_id = serializers.SerializerMethodField()
    driver_id = serializers.SerializerMethodField()
    class Meta:
        model = UserWalletTransaction
        fields = [
            'id',
            'transaction_type',
            'amount',
            'description',
            'balance_after',
            'created_at',
            'wallet',
            'related_ride',
            'customer_reward', 
            'booking_id',
            'driver_id'
        ]

    def get_customer_reward(self, obj):
        if obj.related_ride:
            return getattr(obj.related_ride, 'customer_reward', None)
        return None
    
    def get_booking_id(self, obj):
        if obj.related_ride:
            return getattr(obj.related_ride, 'booking_id', None)
        return None
    def get_driver_id(self, obj):
        if obj.related_ride and obj.related_ride.driver_id:
            return obj.related_ride.driver_id
        return None
    
class RideSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    usernumber = serializers.CharField(source="user.mobile", read_only=True)
    driver_name = serializers.CharField(source="driver.username", read_only=True)
    driver_number = serializers.CharField(source="driver.mobile", read_only=True)
    driver_vehicle_number = serializers.CharField(source="driver.plate_number", read_only=True)
    driver_image = serializers.CharField(source="driver.profile_photo", read_only=True)
    vehicle_name = serializers.CharField(source="driver.model", read_only=True)
    class Meta:
        model = Ride
        fields = '__all__'
        read_only_fields = [
            'user', 'driver', 'status', 'fare', 'completed','driver_image','driver_vehicle_number','driver_name','driver_number',
            'paid', 'created_at', 'completed_at', 'driver_incentive', 'customer_reward','vehicle_name','usernumber','driver_earnings','driver_to_pickup_km'
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['username'] = instance.user.username if instance.user else None
        rep['driver_name'] = instance.driver.username if instance.driver else None
        return rep
    
class DriverLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverLocation
        fields = '__all__'
        read_only_fields = ['driver','updated_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['user','ride','razorpay_order_id','paid']

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class RideFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = ['id', 'rating', 'feedback']
        read_only_fields = ['id']
 
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            "username": {"validators": []}  
        }

class AdminRideSerializer(serializers.ModelSerializer):
    userName = serializers.CharField(source='user.username', read_only=True)
    driverName = serializers.CharField(source='driver.username', read_only=True)
    rejectedByIds = serializers.PrimaryKeyRelatedField(many=True, source='rejected_by', read_only=True)
    class Meta:
        model = Ride
        fields = [
            'id', 'pickup', 'drop', 'fare', 'status', 'completed', 'paid',
            'created_at', 'completed_at', 'rating', 'feedback', 'user', 'driver',
            'userName', 'driverName', 'rejectedByIds','pickup_lat','pickup_lng','drop_lat','drop_lng','booking_id'
        ]    

class DriverPingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverLocation
        fields = ["latitude", "longitude"]

from rest_framework import serializers
from .models import FareRule

class FareRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FareRule
        fields = "__all__"
        

# serializers.py
from rest_framework import serializers
from .models import DistanceReward, TourismOffer,DriverIncentive

class DistanceRewardSerializer(serializers.ModelSerializer):
    vehicle_image_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = DistanceReward
        fields = "__all__"
    def get_vehicle_image_url(self, obj):
        request = self.context.get('request')
        if obj.vehicle_image:
            if request:
                return request.build_absolute_uri(obj.vehicle_image.url)
            return obj.vehicle_image.url
        return None
class TourismOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourismOffer
        fields = "__all__"
    
class IntegrationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationSettings
        fields = ["id", "maps_api_key", "sms_api_key", "payment_api_key", "updated_at"]    
        
class DriverIncentiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverIncentive
        fields = "__all__"        

class GetDriverIncentiveSerializer(serializers.ModelSerializer):
    min_rides = serializers.IntegerField(source='days',allow_null=True, required=False)  # Rename 'days' as 'min_rides'

    class Meta:
        model = DriverIncentive
        fields = [
            'id',
            'ride_type',
            'distance',
            'min_rides',        # renamed from 'days'
            'driver_incentive',
            'max_distance',
            'rides_count',
            'details',
            'created_at',
        ]
from .models import Payment, RefundRequest,VehicleType

class PaymentSerializer(serializers.ModelSerializer):
    rideId = serializers.CharField(source='ride.id', read_only=True)
    userId = serializers.CharField(source='user.id', read_only=True)
    amount = serializers.FloatField(source='ride.fare', read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'rideId', 'userId', 'amount', 'method', 'status', 'created_at']

    def get_status(self, obj):
        if obj.paid:
            return 'completed'
        elif obj.razorpay_payment_id:
            return 'pending'
        return 'failed'

class RefundRequestSerializer(serializers.ModelSerializer):
    rideId = serializers.CharField(source='ride.id', read_only=True)
    userId = serializers.CharField(source='user.id', read_only=True)

    class Meta:
        model = RefundRequest
        fields = ['id', 'rideId', 'userId', 'refund_amount', 'reason', 'status', 'requested_at']
        
class VehicleTypeSerializer(serializers.ModelSerializer):
    # Read-only field to provide full URL to frontend
    vehicleImageUrl = serializers.SerializerMethodField(read_only=True)
    pricing_rules = serializers.SerializerMethodField()
    class Meta:
        model = VehicleType
        fields = '__all__'  # includes vehicleImage field

    def get_vehicleImageUrl(self, obj):
        request = self.context.get('request')
        if obj.vehicleImage:
            return request.build_absolute_uri(obj.vehicleImage.url)
        return None  
    def get_pricing_rules(self, obj):
        rules = FareRule.objects.filter(vehicle_type=obj.name).order_by('min_distance')
        return FareRuleSerializer(rules, many=True).data 
        
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['method', 'paid', 'created_at', 'razorpay_payment_id']

class RefundRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = ['refund_amount', 'reason', 'status', 'requested_at']

class AdminRideHistorySerializer(serializers.ModelSerializer):
    payment = PaymentSerializer(read_only=True)
    refund_requests = RefundRequestSerializer(many=True, read_only=True)
    driver_name = serializers.CharField(source='driver.username', default=None)
    user_name = serializers.CharField(source='user.username')

    class Meta:
        model = Ride
        fields = [
            'id', 'pickup', 'drop', 'distance_km', 'vehicle_type',
            'fare', 'driver_incentive', 'customer_reward', 'status',
            'completed', 'paid', 'created_at', 'completed_at',
            'rating', 'feedback', 'driver_name', 'user_name',
            'payment', 'refund_requests','booking_id'
        ]      
        
class UserOnlineStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_online']
        
class UserSerializer(serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField()
    profile_photo_upload = serializers.FileField(write_only=True, required=False)
    class Meta:
        model = User
        fields = ['username', 'profile_photo','profile_photo_upload','suspended_until','account_status', 'mobile', 'emergency_contact_number','approval_state', 'preferred_payment_method']
        
    def get_profile_photo(self, obj):
        request = self.context.get("request")
        if obj.profile_photo:
            return request.build_absolute_uri(obj.profile_photo.url)
        
    def update(self, instance, validated_data):
        photo = validated_data.pop('profile_photo_upload', None)
        if photo:
            instance.profile_photo = photo
        return super().update(instance, validated_data)    
        return None                
    
class RegisterTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField()


class UpdateLocationSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    is_available = serializers.BooleanField()


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = ['id','rider','pickup_lat','pickup_lng','drop_lat','drop_lng','status','assigned_driver']
        read_only_fields = ['id','status','assigned_driver']    
        
        
from rest_framework import serializers
from .models import Ride

class RideStatusSerializer(serializers.ModelSerializer):
    driver_name = serializers.SerializerMethodField()
    driver_photo = serializers.SerializerMethodField()
    vehicle_number = serializers.SerializerMethodField()
    otp = serializers.SerializerMethodField()
    driver_number = serializers.SerializerMethodField()
    vechicle_name = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    class Meta:
        model = Ride
        fields = [
            'booking_id', 'status', 'pickup', 'drop', 'pickup_time',
            'driver_name', 'driver_number', 'vechicle_name',
            'driver_photo', 'vehicle_number', 'otp',
            'fare', 'completed', 'paid','vehicle_type','gst_amount','payment_type','pickup_lat', 'pickup_lng','drop_lat','drop_lng','user_name'
        ]
    def get_driver_name(self, obj):
        return obj.driver.username if obj.driver else None

    def get_user_name(self, obj):
        return obj.user.username if obj.user else None

    def get_driver_photo(self, obj):
        if obj.driver and obj.driver.profile_photo:
            request = self.context.get('request')
            photo_url = obj.driver.profile_photo.url
            return request.build_absolute_uri(photo_url) if request else photo_url
        return None

    def get_vehicle_number(self, obj):
        return obj.driver.plate_number if obj.driver else None

    def get_otp(self, obj):
        return getattr(obj, "otp", None)

    def get_driver_number(self, obj):
        return obj.driver.mobile if obj.driver else None

    def get_vechicle_name(self, obj):
        return obj.driver.model if obj.driver else None
    
    
class DriverEarningsSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_earnings = serializers.FloatField()
    total_rides = serializers.IntegerField()    
    
    
class RideInvoiceSerializer(serializers.ModelSerializer):
    vehicle_name = serializers.SerializerMethodField()
    vehicle_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Ride
        fields = [
            'id', 'booking_id', 'pickup', 'drop', 'pickup_time',
            'fare', 'vehicle_name', 'vehicle_image'
        ]
    
    def get_vehicle_name(self, obj):
        return obj.vehicle_type  # Or get from VehicleType model if linked
    
    def get_vehicle_image(self, obj):
        vehicle = VehicleType.objects.filter(name=obj.vehicle_type).first()
        if vehicle and vehicle.vehicleImage:
            request = self.context.get('request')
            return request.build_absolute_uri(vehicle.vehicleImage.url) if request else vehicle.vehicleImage.url
        return None    
    
from django.urls import reverse
    
class RideHistorySerializer(serializers.ModelSerializer):
    vehicle_display = serializers.SerializerMethodField()
    pickup_info = serializers.SerializerMethodField()
    invoice_pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Ride
        fields = ['id', 'vehicle_display', 'fare', 'pickup_info', 'pickup_time', 'invoice_pdf_url']
    
    def get_vehicle_display(self, obj):
        # Pull vehicle info from driver if available
        driver = obj.driver or obj.assigned_driver
        if driver:
            return f"{driver.vehicle_type or 'N/A'}, {driver.model or 'N/A'}, {driver.plate_number or 'N/A'}"
        # fallback to ride vehicle_type if no driver assigned
        return f"{obj.vehicle_type or 'N/A'}"
    
    def get_pickup_info(self, obj):
        return f"{obj.pickup} ({obj.pickup_time.strftime('%I.%M %p')})"
    
    def get_invoice_pdf_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(reverse('ride-invoice', args=[obj.id]))
        return None
    
class DriverRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    user_image = serializers.ImageField(source="user.profile_photo", read_only=True)
    driver_name = serializers.CharField(source="driver.username", read_only=True)

    class Meta:
        model = DriverRating
        fields = ["id", "ride", "user", "driver", "stars", "feedback","user_image", "created_at", "user_name", "driver_name"]
        read_only_fields = ["id", "created_at", "user","user_image", "driver", "ride"]    


class DriverWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverWallet
        fields = ["id", "driver", "balance", "updated_at"]
        read_only_fields = ["id", "driver", "balance", "updated_at"]


class WalletTransactionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

class UserWalletTransactionSerializer(serializers.ModelSerializer):
    ride_id = serializers.SerializerMethodField()

    class Meta:
        model = UserWalletTransaction
        fields = [
            'id',
            'transaction_type',
            'amount',
            'description',
            'balance_after',
            'created_at',
            'ride_id'
        ]

    def get_ride_id(self, obj):
        return obj.related_ride.id if obj.related_ride else None
    
class DriverIncentiveProgressSerializer(serializers.ModelSerializer):
    ride_type = serializers.CharField(source='incentive_rule.ride_type', read_only=True)
    target_rides = serializers.IntegerField(source='incentive_rule.min_rides', read_only=True)
    cashback = serializers.DecimalField(source='incentive_rule.driver_incentive', max_digits=10, decimal_places=2, read_only=True)
    days_left = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = DriverIncentiveProgress
        fields = [
            'id',
            'ride_type',
            'rides_completed',
            'target_rides',
            'days_left',
            'progress_percent',
            'cashback',
            'earned',
        ]

    def get_days_left(self, obj):
        return obj.days_left

    def get_progress_percent(self, obj):
        return obj.progress_percent
    
class AdminWalletTransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    related_user_name = serializers.CharField(source='related_user.username', read_only=True)
    related_ride_id = serializers.IntegerField(source='related_ride.id', read_only=True)
    booking_id = serializers.CharField(source='related_ride.booking_id', read_only=True)

    class Meta:
        model = AdminWalletTransaction
        fields = [
            'id',
            'transaction_type',
            'transaction_type_display',
            'amount',
            'commission_amount',
            'gst_amount',
            'balance_after',
            'description',
            'related_user_name',
            'related_ride_id',
            'booking_id',
            'created_at',
        ]    



class CancellationPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = CancellationPolicy
        fields = '__all__'        