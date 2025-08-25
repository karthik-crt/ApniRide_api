from rest_framework.views import APIView
from rest_framework import generics, permissions ,parsers
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

from rest_framework import permissions
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
import random
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
        distance = float(self.request.data.get("distance_km"))
        vehicle_type = self.request.data.get("vehicle_type")

        fare = calculate_fare(vehicle_type, distance)
        driver_incentive, customer_reward = calculate_incentives_and_rewards(distance)

        serializer.save(
            user=self.request.user,
            fare=fare,
            driver_incentive=driver_incentive,
            customer_reward=customer_reward
        )


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
    serializer_class = UserEditSerializer
    queryset = User.objects.all()
    lookup_field = 'id'

    # allow form-data, files, JSON
    parser_classes = [parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser]
      
 
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
    serializer_class = AdminRideSerializer
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

        if not getattr(user, 'is_driver', False):
            return Response({
                "statusCode": "0",
                "statusMessage": "Only drivers can update ride status."
            }, status=status.HTTP_403_FORBIDDEN)

        ride = get_object_or_404(Ride, id=ride_id)

        
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
        

class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        try:
            today = timezone.now().date()
            week_ago = today - timedelta(days=6)

            dashboard_stats = {
                "activeRides": Ride.objects.filter(status='accepted').count(),
                "totalRevenue": Payment.objects.filter(paid=True).aggregate(total=Sum('ride__fare'))['total'] or 0,
                "revenueGrowth": self.calculate_revenue_growth(),
                "totalUsers": User.objects.filter(is_user=True).count(),
                "newUsersToday": User.objects.filter(is_user=True, date_joined__date=today).count(),
                "totalDrivers": User.objects.filter(is_driver=True).count(),
                "onlineDrivers": DriverLocation.objects.filter(updated_at__gte=timezone.now() - timedelta(minutes=15)).count(),
                "todayRides": Ride.objects.filter(created_at__date=today).count(),
                "todayRevenue": Payment.objects.filter(paid=True, ride__created_at__date=today).aggregate(total=Sum('ride__fare'))['total'] or 0,
                "avgRating": Ride.objects.filter(rating__isnull=False).aggregate(avg=Avg('rating'))['avg'] or 0
            }
            revenue_chart = self.get_revenue_chart_data(week_ago, today)
            ride_chart = self.get_ride_chart_data(week_ago, today)

            return Response({
                "statusCode": "1",
                "statusMessage": "Dashboard data retrieved successfully",
                "dashboardStats": dashboard_stats,
                "revenueChart": revenue_chart,
                "rideChart": ride_chart
            })

        except Exception as e:
            return Response({
                "statusCode": "0",
                "statusMessage": f"Error retrieving dashboard data: {str(e)}"
            }, status=500)

    def calculate_revenue_growth(self):
        today = timezone.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        previous_week_start = current_week_start - timedelta(days=7)
        
        current_week_revenue = Payment.objects.filter(
            paid=True,
            ride__created_at__date__gte=current_week_start,
            ride__created_at__date__lte=today
        ).aggregate(total=Sum('ride__fare'))['total'] or 0
        
        previous_week_revenue = Payment.objects.filter(
            paid=True,
            ride__created_at__date__gte=previous_week_start,
            ride__created_at__date__lte=previous_week_start + timedelta(days=6)
        ).aggregate(total=Sum('ride__fare'))['total'] or 0
        
        if previous_week_revenue == 0:
            return 0 if current_week_revenue == 0 else 100
        return ((current_week_revenue - previous_week_revenue) / previous_week_revenue * 100)

    def get_revenue_chart_data(self, start_date, end_date):
        labels = [(start_date + timedelta(days=x)).strftime('%a') for x in range(7)]
        revenue_data = []
        
        for i in range(7):
            date = start_date + timedelta(days=i)
            total = Payment.objects.filter(
                paid=True,
                ride__created_at__date=date
            ).aggregate(total=Sum('ride__fare'))['total'] or 0
            revenue_data.append(total)
        
        return {
            "labels": labels,
            "revenue": revenue_data
        }

    def get_ride_chart_data(self, start_date, end_date):
        days = (end_date - start_date).days + 1
        labels = [(start_date + timedelta(days=x)).strftime('%a') for x in range(days)]
        ride_data = []

        for i in range(days):
            date = start_date + timedelta(days=i)
            count = Ride.objects.filter(created_at__date=date).count()
            ride_data.append(count)

        return {
            "labels": labels,
            "rides": ride_data
        }


from rest_framework import viewsets
from .models import FareRule

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FareRule
from .serializers import FareRuleSerializer

# List all rules or create a new one
class FareRuleListView(APIView):
    def get(self, request):
        rules = FareRule.objects.all().order_by('vehicle_type', 'min_distance')
        serializer = FareRuleSerializer(rules, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FareRuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Retrieve, update, or delete a specific rule
class FareRuleDetailView(APIView):
    def get_object(self, pk):
        return FareRule.objects.get(pk=pk)

    def get(self, request, pk):
        rule = self.get_object(pk)
        serializer = FareRuleSerializer(rule)
        return Response(serializer.data)

    def patch(self, request, pk):
        rule = self.get_object(pk)
        serializer = FareRuleSerializer(rule, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        rule = self.get_object(pk)
        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FareRuleViewSet(viewsets.ModelViewSet):
    queryset = FareRule.objects.all()
    serializer_class = serializers.FareRuleSerializer
        
def calculate_fare(vehicle_type, distance):
    from .models import FareRule
    
    rules = FareRule.objects.filter(vehicle_type=vehicle_type).order_by("min_distance")

    for rule in rules:
        if rule.max_distance is None:  # "Above"
            if distance >= rule.min_distance:
                return distance * rule.per_km_rate
        elif rule.min_distance <= distance <= rule.max_distance:
            return distance * rule.per_km_rate

    return 0  # fallback if no rule matched

        
def calculate_incentives_and_rewards(distance):
    driver_incentive = 0
    customer_reward = {}

    # Driver incentives
    if distance > 10:
        driver_incentive += 15
    if 50 <= distance <= 100:
        driver_incentive += 50
    elif 100 <= distance <= 200:
        driver_incentive += 100  

    
    if distance > 10:
        customer_reward = {"cashback": 5, "water_bottles": 1}
    if 6 <= distance <= 10:
        customer_reward = {"cashback": 8}
    if 40 <= distance <= 50:
        customer_reward = {"water_bottles": 2, "tea": 1}
    if 50 <= distance <= 100:
        customer_reward = {"discount": "10% restaurant", "water_bottles": 3, "tea": 1}
    if distance > 200:
        customer_reward = {"discount": "10% restaurant", "water_bottles": 5, "tea": 1}

    return driver_incentive, customer_reward
        
class CancelRideView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ride_id):
        try:
            ride = get_object_or_404(Ride, id=ride_id)

            # Prevent cancelling completed or already cancelled rides
            if ride.status in ['completed', 'cancelled']:
                return Response({
                    "statusCode": "0",
                    "statusMessage": f"Ride cannot be cancelled because it is {ride.status}."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Only rider (user) or driver assigned can cancel
            if ride.user != request.user and ride.driver != request.user:
                return Response({
                    "statusCode": "0",
                    "statusMessage": "You are not authorized to cancel this ride."
                }, status=status.HTTP_403_FORBIDDEN)

            # Update ride status
            ride.status = 'cancelled'
            ride.save(update_fields=["status"])

            # Notify other party (optional, if Notification model exists)
            if hasattr(models, "Notification"):
                if request.user == ride.user and ride.driver:
                    Notification.objects.create(
                        user=ride.driver,
                        title='Ride Cancelled',
                        message=f'Ride {ride.id} has been cancelled by {ride.user.username}.'
                    )
                elif request.user == ride.driver:
                    Notification.objects.create(
                        user=ride.user,
                        title='Ride Cancelled',
                        message=f'Your ride {ride.id} was cancelled by driver {ride.driver.username}.'
                    )

            serializer = RideSerializer(ride)
            return Response({
                "statusCode": "1",
                "statusMessage": "Ride cancelled successfully.",
                "ride": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "statusCode": "0",
                "statusMessage": f"Error cancelling ride: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)      
            

from django.contrib import admin
from .models import DistanceReward, TourismOffer

@admin.register(DistanceReward)
class DistanceRewardAdmin(admin.ModelAdmin):
    list_display = ("min_distance", "max_distance", "cashback", "water_bottles", "tea", "discount")
    list_editable = ("cashback", "water_bottles", "tea", "discount")

@admin.register(TourismOffer)
class TourismOfferAdmin(admin.ModelAdmin):
    list_display = ("name", "discount", "tea", "water_bottles", "long_term_days")
    list_editable = ("discount", "tea", "water_bottles", "long_term_days")
            

def calculate_customer_rewards(distance):
    from .models import DistanceReward

    # Fetch all rewards from DB
    rewards = DistanceReward.objects.all()
    applicable_reward = {}

    for reward in rewards:
        max_dist = reward.max_distance if reward.max_distance is not None else float('inf')
        if reward.min_distance <= distance <= max_dist:
            applicable_reward = {
                "cashback": reward.cashback,
                "water_bottles": reward.water_bottles,
                "tea": reward.tea,
                "discount": reward.discount
            }
            break

    return applicable_reward

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import DistanceReward, TourismOffer
from .serializers import DistanceRewardSerializer, TourismOfferSerializer
from django.shortcuts import get_object_or_404

# DistanceReward API
class DistanceRewardAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            reward = get_object_or_404(DistanceReward, pk=pk)
            serializer = DistanceRewardSerializer(reward)
        else:
            rewards = DistanceReward.objects.all().order_by("min_distance")
            serializer = DistanceRewardSerializer(rewards, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DistanceRewardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        reward = get_object_or_404(DistanceReward, pk=pk)
        serializer = DistanceRewardSerializer(reward, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        reward = get_object_or_404(DistanceReward, pk=pk)
        reward.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# TourismOffer API
class TourismOfferAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            offer = get_object_or_404(TourismOffer, pk=pk)
            serializer = TourismOfferSerializer(offer)
        else:
            offers = TourismOffer.objects.all()
            serializer = TourismOfferSerializer(offers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TourismOfferSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        offer = get_object_or_404(TourismOffer, pk=pk)
        serializer = TourismOfferSerializer(offer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        offer = get_object_or_404(TourismOffer, pk=pk)
        offer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class IntegrationSettingsView(APIView):

    def get(self, request):
        settings, created = IntegrationSettings.objects.get_or_create(id=1)
        serializer = IntegrationSettingsSerializer(settings)
        return Response(serializer.data)

    def patch(self, request):
        settings, created = IntegrationSettings.objects.get_or_create(id=1)
        serializer = IntegrationSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Settings updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DriverIncentiveView(APIView):

    def get(self, request, driver_id=None):
        if driver_id:
            # Fetch incentives for a particular driver
            records = DriverIncentive.objects.filter(driver_id=driver_id)
        else:
            # Fetch all incentives (global + drivers)
            records = DriverIncentive.objects.all()

        serializer = DriverIncentiveSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, driver_id=None):
        if driver_id:
            # Update/create incentive for specific driver
            record, created = DriverIncentive.objects.get_or_create(
                driver_id=driver_id,
                ride_type=request.data.get("ride_type"),
                defaults={
                    "distance": request.data.get("distance"),
                    "days": request.data.get("days"),
                    "driver_incentive": request.data.get("driver_incentive", 0),
                    "details": request.data.get("details", "")
                }
            )
        else:
            # Global incentive
            record, created = DriverIncentive.objects.get_or_create(
                driver=None,
                ride_type=request.data.get("ride_type"),
                defaults={
                    "distance": request.data.get("distance"),
                    "days": request.data.get("days"),
                    "driver_incentive": request.data.get("driver_incentive", 0),
                    "details": request.data.get("details", "")
                }
            )

        serializer = DriverIncentiveSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Incentive updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            record = DriverIncentive.objects.get(pk=pk)
            record.delete()
            return Response({"message": "Incentive deleted successfully"}, status=status.HTTP_200_OK)
        except DriverIncentive.DoesNotExist:
            return Response({"error": "Incentive not found"}, status=status.HTTP_404_NOT_FOUND)