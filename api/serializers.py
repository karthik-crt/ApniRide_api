from rest_framework import serializers
from .models import User, Ride, DriverLocation, Payment, OTP,IntegrationSettings


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

# class RideSerializer(serializers.ModelSerializer):
#     username = serializers.CharField(source="user.username", read_only=True)
#     driver_name = serializers.CharField(source="driver.username", read_only=True)

#     class Meta:
#         model = Ride
#         fields = '__all__'
#         read_only_fields = [
#             'user','driver','status','fare','completed',
#             'paid','created_at','completed_at'
#         ]
#         # Add the extra fields to output
#         extra_fields = ['username', 'driver_name']

#     def to_representation(self, instance):
#         # include both default + extra fields
#         rep = super().to_representation(instance)
#         rep['username'] = instance.user.username if instance.user else None
#         rep['driver_name'] = instance.driver.username if instance.driver else None
#         return rep


class RideSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    driver_name = serializers.CharField(source="driver.username", read_only=True)


    class Meta:
        model = Ride
        fields = '__all__'
        read_only_fields = [
            'user', 'driver', 'status', 'fare', 'completed',
            'paid', 'created_at', 'completed_at', 'driver_incentive', 'customer_reward'
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
            'userName', 'driverName', 'rejectedByIds'
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
    class Meta:
        model = DistanceReward
        fields = "__all__"

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
    vehicleImage = serializers.SerializerMethodField()
    class Meta:
        model = VehicleType
        fields = "__all__"  
        
    def get_vehicleImage(self, obj):
        request = self.context.get('request')
        if obj.vehicleImage:  # assuming your model field name is `vehicleImage`
            return request.build_absolute_uri(obj.vehicleImage.url)
        return None   
        
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['method', 'paid', 'created_at', 'razorpay_payment_id']

class RefundRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = ['refund_amount', 'reason', 'status', 'requested_at']

class RideHistorySerializer(serializers.ModelSerializer):
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
            'payment', 'refund_requests'
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
        fields = ['username', 'profile_photo','profile_photo_upload', 'mobile', 'emergency_contact_number','approval_state', 'preferred_payment_method']
        
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
        
        
        