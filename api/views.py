from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail
from django.utils import timezone
from .models import *
from .serializers import *
import razorpay 
import json
from rest_framework import status
from django.conf import settings
from django.contrib.auth.hashers import make_password
from api import serializers
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "statusCode": "1",
                "statusMessage": "User registered successfully",
                "user_id": user.id,
                "username": user.username,
                "email":user.email,
                "driver_id":user.is_driver
            })

        return Response({
            "statusCode": "0",
            "statusMessage": "Registration failed",
            "errors": serializer.errors,
        })
    
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                "statusCode": "0",
                "statusMessage": "Email and password required"
            })

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "statusCode": "0",
                "statusMessage": "Invalid credentials"
            })

        user = authenticate(username=user.username, password=password)
        
        if not user:
            return Response({
                "statusCode": "0",
                "statusMessage": "Invalid credentials"
            })

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        print("user",user)
        user_data = UserLoginSerializer(user).data
        return Response({
            "statusCode": "1",
            "statusMessage": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            **user_data
        })


class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        try:
            serializer = SendOTPSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create(email=email, username=email)

            code = f"{random.randint(100000,999999)}"
            OTP.objects.create(user=user, code=code)
            send_mail("Your OTP", f"OTP: {code}", 'no-reply@cabapp.com', [email])
            return Response({"statusCode":"1","statusMessage":"OTP send Successfully"})
        except Exception as e:
            return Response({"statusCode":"0", "statusMessage": str(e)})


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            serializer = VerifyOTPSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            email = serializer.validated_data['email']
            code = serializer.validated_data['code']

            # Pick the first matching user (avoid get() multiple objects error)
            user = User.objects.filter(email=email).first()
            if not user:
                return Response({"statusCode": "0", "statusMessage": "User not found"}, status=404)

            # Find OTP
            otp = OTP.objects.filter(user=user, code=code, is_used=False).order_by('-created_at').first()
            if not otp or not otp.is_valid():
                return Response({
                    "statusCode": "0",
                    "statusMessage": "Failed",
                    "error": "OTP expired or invalid"
                }, status=400)

            # Mark OTP as used
            otp.is_used = True
            otp.save()

            # Create JWT tokens
            token = RefreshToken.for_user(user)

            return Response({
                "statusCode": "1",
                "statusMessage": "OTP Verified",
                "access": str(token.access_token),
                "refresh": str(token)
            })

        except Exception as e:
            return Response({"statusCode": "0", "statusMessage": str(e)})


class BookRideView(generics.CreateAPIView):
    serializer_class = RideSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RideHistoryView(generics.ListAPIView):
    serializer_class = RideSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        if self.request.user.is_driver:
            return Ride.objects.filter(driver=self.request.user)
        return Ride.objects.filter(user=self.request.user)

class AvailableRidesView(generics.ListAPIView):
    serializer_class = RideSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Ride.objects.filter(status='pending')

class AcceptRideView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id, status='pending')
            ride.status = 'accepted'
            ride.driver = request.user
            ride.save()
            return Response({"statusCode":"1","statusMessage": "Ride accepted"})
        except Exception as e:
            return Response({"statusCode":"0", "statusMessage": str(e)})

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import DriverLocation

class DriverLocationUpdate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')

            # Validate presence
            if latitude is None or longitude is None:
                return Response(
                    {"statusCode": "0", "statusMessage": "Latitude and longitude are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate numeric
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                return Response(
                    {"statusCode": "0", "statusMessage": "Latitude and longitude must be numbers"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Pass defaults to avoid NULL error
            loc, created = DriverLocation.objects.get_or_create(
                driver=request.user,
                defaults={'latitude': latitude, 'longitude': longitude}
            )

            if not created:  # If it already existed, update it
                loc.latitude = latitude
                loc.longitude = longitude
                loc.save(update_fields=["latitude", "longitude"])

            return Response(
                {"statusCode": "1", "statusMessage": "Location updated successfully","driver": {
                        "id": request.user.id,
                        "username": request.user.username
                    }},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"statusCode": "0", "statusMessage": f"Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetDriverLocation(APIView):
    def get(self, request, driver_id):
        loc = DriverLocation.objects.get(driver_id=driver_id)
        return Response({"lat": loc.latitude, "lng": loc.longitude})

class CreatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id, user=request.user)
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))
            order = client.order.create({"amount": int(ride.fare * 100), "currency": "INR", "payment_capture": 1})
            Payment.objects.create(user=request.user, ride=ride, razorpay_order_id=order['id'])
            return Response(order)
        except Exception as e:
            return Response({"statusCode":"0", "statusMessage": str(e)})

class ConfirmPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:
            data = request.data
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })
            payment = Payment.objects.get(razorpay_order_id=data['razorpay_order_id'])
            payment.razorpay_payment_id = data['razorpay_payment_id']
            payment.razorpay_signature = data['razorpay_signature']
            payment.paid = True
            payment.save()
            ride = payment.ride
            ride.paid = True
            ride.completed = True
            ride.completed_at = timezone.now()
            ride.save()
            return Response({"statusCode":"1","statusMessage": "Payment confirmed"})
        except Exception as e:
            return Response({"statusCode":"0", "statusMessage": str(e)})
    
class RejectRideView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id, status='pending')
        except Ride.DoesNotExist:
            return Response({
                "statusCode": "0",
                "statusMessage": "failed",
                "error": "Ride not found or already accepted/rejected."
            }, status=404)

        # Add current driver to rejected_by list
        ride.rejected_by.add(request.user)
        ride.save()

        # Optional notification if model exists
        if hasattr(models, "Notification") and ride.user:
            Notification.objects.create(
                user=ride.user,
                title='Ride Rejected',
                message=f'Your ride to {ride.drop} was rejected by {request.user.username}. Searching for another driver...'
            )

        return Response({
            "statusCode": "1",
            "statusMessage": "Ride rejected, rider notified.",
            "rider_name": ride.user.username if ride.user else None
        })

  
class SubmitRideFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]
 
    def post(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id, user=request.user)
        except Ride.DoesNotExist:
            return Response({"statusCode":"0","statusMessage":"Failed",'error': 'Ride not found'}, status=404)
 
        if not ride.completed:
            return Response({"statusCode":"0","statusMessage":"Failed",'error': 'Feedback can only be submitted after ride is completed'}, status=400)
 
        serializer = RideFeedbackSerializer(ride, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"statusCode":"1","statusMessage": 'Feedback submitted successfully', 'data': serializer.data})
    
from rest_framework import generics, permissions, filters
from django.contrib.auth import get_user_model
from .models import Ride, DriverLocation
from .models import Payment
from .models import Notification
from api.serializers import RideSerializer, DriverLocationSerializer, PaymentSerializer, UserRegisterSerializer
 
User = get_user_model()
 
class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserRegisterSerializer
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['id']           
    search_fields = ['username', 'email']
    
    
class AdminUserEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserRegisterSerializer
    queryset = User.objects.all()
    lookup_field = 'id'      
 
class AdminUserDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    lookup_field = 'id'  
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "statusCode": 1,
            "statusMessage": "Deleted successfully"
        }, status=status.HTTP_200_OK)
     
from django.http import JsonResponse

class AdminDriverApprovalView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, driver_id):
        try:
            driver = User.objects.get(id=driver_id, is_driver=True)
            driver.is_active = True
            driver.save()
            return Response({"message": "Driver approved"})
        except User.DoesNotExist:
            return Response({"error": "Driver not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def delete(self, request, driver_id):
        try:
            driver = User.objects.get(id=driver_id, is_driver=True)
            driver.is_active = False
            driver.save()
            return Response({"message": "Driver deactivated"})
        except User.DoesNotExist:
            return Response({"error": "Driver not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

 
class AdminRideListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = RideSerializer
    queryset = Ride.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['pickup', 'drop', 'user__username', 'driver__username']
    ordering_fields = ['created_at', 'fare']
 
class AdminPaymentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'ride__id']
 
class AdminDriverLocationView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request, driver_id):
        try:
            loc = DriverLocation.objects.get(driver_id=driver_id)
            return Response({
                "driver": driver_id,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "updated_at": loc.updated_at
            })
        except DriverLocation.DoesNotExist:
            return Response({"error": "Location not found"}, status=404)
 
class AdminSendNotificationView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        message = request.data.get('message')

        if not user_id or not title or not message:
            return Response({"error": "Missing required fields"}, status=400)

        user = User.objects.get(id=user_id)
        notification = Notification.objects.create(user=user, title=title, message=message)

        return Response({
            "message": "Notification sent",
            "notification": {
                "id": notification.id,
                "user_id": notification.user.id,
                "title": notification.title,
                "message": notification.message,
                "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(notification, 'created_at') else None,
            }
        })

    
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    }

class UserLoginView(APIView):
    def post(self, request):
        mobile = request.data.get('mobile')
        if not mobile:
            return Response({
                "statusCode": "0",
                "statusMessage": "Mobile number is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(mobile=mobile).first()
        if user:
            tokens = get_tokens_for_user(user)
            user_data = UserLoginSerializer(user).data
            return Response({
                "statusCode": "1",
                "statusMessage": "Login successful",
                "is_oldUser": True,
                **tokens,
                **user_data
            })
        else:
            return Response({
                "statusCode": "1",
                "statusMessage": "New User",
                "is_oldUser": False
            })

class UserRegisterView(APIView):
    def post(self, request):
        mobile = request.data.get('mobile')
        username = request.data.get('username')
        email = request.data.get('email', "")

        if not mobile or not username:
            return Response({
                "statusCode": "0",
                "statusMessage": "Mobile and username are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(mobile=mobile).exists():
            return Response({
                "statusCode": "0",
                "statusMessage": "User already exists"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            mobile=mobile,
            username=username,
            email=email,
            is_user=True
        )

        tokens = get_tokens_for_user(user)
        user_data = UserLoginSerializer(user).data
        return Response({
            "statusCode": "1",
            "statusMessage": "Login successful",
            "is_oldUser": True,
            **tokens,
            **user_data
        })
        
class DriverLoginView(APIView):
    def post(self, request):
        mobile = request.data.get('mobile')
        if not mobile:
            return Response({
                "statusCode": "0",
                "statusMessage": "Mobile number is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        driver = User.objects.filter(mobile=mobile, is_driver=1).first()
        if driver:
            tokens = get_tokens_for_user(driver)
            driver_data = UserLoginSerializer(driver).data
            return Response({
                "statusCode": "1",
                "statusMessage": "Login successful",
                "is_oldUser": True,
                **tokens,
                **driver_data
            })
        else:
            return Response({
                "statusCode": "1",
                "statusMessage": "New Driver",
                "is_oldUser": False
            })




class DriverRegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser]  

    def post(self, request):
        mobile = request.data.get('mobile')
        username = request.data.get('username')
        email = request.data.get('email', "")
        vehicle_type = request.data.get('vehicle_type')
        model = request.data.get('model')
        plate_number = request.data.get('plate_number')
        state = request.data.get('state')

        driving_license = request.FILES.get('driving_license')
        rc_book = request.FILES.get('rc_book')
        aadhaar = request.FILES.get('aadhaar')
        pan_card = request.FILES.get('pan_card')

        if not all([mobile, username, vehicle_type, model, plate_number, state]):
            return Response({
                "statusCode": "0",
                "statusMessage": "All fields are required for driver registration"
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(mobile=mobile).exists():
            return Response({
                "statusCode": "0",
                "statusMessage": "Driver already exists"
            }, status=status.HTTP_400_BAD_REQUEST)

    
        driver = User.objects.create(
            mobile=mobile,
            username=username,
            email=email,
            is_driver=1,
            vehicle_type=vehicle_type,
            model=model,
            plate_number=plate_number,
            state=state,
            driving_license=driving_license,
            rc_book=rc_book,
            aadhaar=aadhaar,
            pan_card=pan_card
        )

        tokens = get_tokens_for_user(driver)
        driver_data = UserLoginSerializer(driver).data

        return Response({
            "statusCode": "1",
            "statusMessage": "Driver registered successfully",
            "is_oldUser": True,
            **tokens,
            **driver_data
        })


class RideStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ride_id):
        user = request.user
        new_status = request.data.get('status')

        if new_status not in ['accepted', 'completed', 'cancelled']:
            return Response({
                "statusCode": "0",
                "statusMessage": "Invalid status update."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate user is a driver
        if not getattr(user, 'is_driver', False):
            return Response({
                "statusCode": "0",
                "statusMessage": "Only drivers can update ride status."
            }, status=status.HTTP_403_FORBIDDEN)

        ride = get_object_or_404(Ride, id=ride_id)

        # Business logic for status transitions
        if new_status == 'accepted':
            if ride.status != 'pending':
                return Response({
                    "statusCode": "0",
                    "statusMessage": f"Ride cannot be accepted because it is {ride.status}."
                }, status=status.HTTP_400_BAD_REQUEST)
            if ride.driver is not None:
                return Response({
                    "statusCode": "0",
                    "statusMessage": "Ride is already assigned to another driver."
                }, status=status.HTTP_400_BAD_REQUEST)
            ride.driver = user
            ride.status = 'accepted'

        elif new_status == 'completed':
            # Only driver who accepted can complete
            if ride.status != 'accepted':
                return Response({
                    "statusCode": "0",
                    "statusMessage": f"Ride cannot be completed because it is {ride.status}."
                }, status=status.HTTP_400_BAD_REQUEST)
            if ride.driver != user:
                return Response({
                    "statusCode": "0",
                    "statusMessage": "You are not authorized to complete this ride."
                }, status=status.HTTP_403_FORBIDDEN)
            ride.status = 'completed'

        elif new_status == 'cancelled':
            # Add your cancellation logic, e.g. who can cancel and when
            if ride.status in ['completed', 'cancelled']:
                return Response({
                    "statusCode": "0",
                    "statusMessage": f"Ride cannot be cancelled because it is {ride.status}."
                }, status=status.HTTP_400_BAD_REQUEST)
            # Allow driver or passenger to cancel (example)
            if ride.driver != user and ride.user != user:
                return Response({
                    "statusCode": "0",
                    "statusMessage": "You are not authorized to cancel this ride."
                }, status=status.HTTP_403_FORBIDDEN)
            ride.status = 'cancelled'

        ride.save()

        serializer = RideSerializer(ride)
        return Response({
            "statusCode": "1",
            "statusMessage": f"Ride status updated to {ride.status}.",
            "ride": serializer.data
        })
        
