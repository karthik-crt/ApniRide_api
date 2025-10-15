# # from rest_framework import generics, permissions, status
# # from rest_framework.response import Response
# # from rest_framework.serializers import ValidationError
# # from django.utils import timezone
# # from django.db import transaction
# # import random
# # import logging
# # from datetime import datetime
# # from .utils import calculate_distance, get_nearby_driver_tokens, get_nearest_driver_distance
# # from ApniRide.firebase_app import send_multicast, send_fcm_notification
# # from .models import Ride  # Make sure to import your Ride model
# # from .serializers import RideSerializer
from .views import calculate_fare,calculate_incentives_and_rewards

# # logger = logging.getLogger(__name__)

# # class BookRideView(generics.CreateAPIView):
# #     serializer_class = RideSerializer
# #     permission_classes = [permissions.IsAuthenticated]

# #     def perform_create(self, serializer):
# #         # Extract and validate mandatory fields
# #         pickup_lat = self.request.data.get("pickup_lat")
# #         pickup_lng = self.request.data.get("pickup_lng")
# #         vehicle_type = self.request.data.get("vehicle_type")
# #         pickup_mode = self.request.data.get("pickup_mode")
        
# #         print("self.request.data.get", self.request.data.get("pickup"))
# #         print("self.request.data.get", self.request.data.get("drop"))
        
# #         # Optional fields
# #         drop_lat = self.request.data.get("drop_lat")
# #         drop_lng = self.request.data.get("drop_lng")
# #         pickup_time = self.request.data.get("pickup_time")
# #         booking_id = str(random.randint(1000, 9999))
        
# #         # Validate coordinates
# #         try:
# #             pickup_lat = float(pickup_lat)
# #             pickup_lng = float(pickup_lng)
# #             drop_lat = float(drop_lat) if drop_lat else None
# #             drop_lng = float(drop_lng) if drop_lng else None
# #         except (ValueError, TypeError):
# #             raise ValidationError("Coordinates must be valid numbers.")

# #         # Validate mandatory fields
# #         if not all([pickup_lat, pickup_lng, vehicle_type, pickup_mode]):
# #             raise ValidationError("pickup_lat, pickup_lng, vehicle_type, and pickup_mode are required.")

# #         # Validate pickup_time for 'LATER' mode
# #         if pickup_mode.upper() == "LATER":
# #             if not pickup_time:
# #                 raise ValidationError("pickup_time is required when pickup_mode is 'LATER'.")
            
# #             # Parse pickup_time and validate it's in the future
# #             try:
# #                 pickup_time_obj = timezone.datetime.fromisoformat(pickup_time.replace('Z', '+00:00'))
# #                 if pickup_time_obj <= timezone.now():
# #                     raise ValidationError("pickup_time must be in the future for 'LATER' mode.")
# #             except (ValueError, AttributeError):
# #                 raise ValidationError("pickup_time must be a valid ISO format datetime string.")
# #         else:
# #             # For immediate rides, use current time
# #             pickup_time_obj = timezone.now()

# #         # Calculate distance
# #         distance_km = float(self.request.data.get("distance_km", 0))
# #         if drop_lat and drop_lng:
# #             try:
# #                 distance_km = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
# #             except Exception as e:
# #                 raise ValidationError(f"Error calculating distance: {str(e)}")

# #         # Calculate fare and incentives
# #         try:
# #             fare = calculate_fare(vehicle_type, distance_km)
# #             driver_incentive, customer_reward = calculate_incentives_and_rewards(distance_km)
# #         except Exception as e:
# #             raise ValidationError(f"Error calculating fare or incentives: {str(e)}")

# #         # Get nearest driver and distance (for immediate rides only)
# #         nearest_driver = None
# #         driver_to_pickup_km = 0
        
# #         if pickup_mode.upper() != "LATER":
# #             nearest_driver, driver_to_pickup_km = get_nearest_driver_distance(pickup_lat, pickup_lng)
# #             print("Nearest driver:", nearest_driver)
# #             print("Distance to pickup (km):", driver_to_pickup_km)

# #         # Pickup to drop distance
# #         if drop_lat and drop_lng:
# #             pickup_to_drop_km = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
# #         else:
# #             pickup_to_drop_km = 0

# #         print("Pickup to Drop distance (km):", pickup_to_drop_km)

# #         # Save ride
# #         ride = serializer.save(
# #             user=self.request.user,
# #             pickup_lat=pickup_lat,
# #             pickup_lng=pickup_lng,
# #             drop_lat=drop_lat,
# #             drop_lng=drop_lng,
# #             pickup_mode=pickup_mode,
# #             pickup_time=pickup_time_obj,
# #             distance_km=distance_km,
# #             fare=fare,
# #             driver_incentive=driver_incentive,
# #             customer_reward=customer_reward,
# #             vehicle_type=vehicle_type,
# #             booking_id=booking_id,
# #             status='PENDING'  # Make sure status is set appropriately
# #         )

# #         # Send notifications only for immediate rides
# #         if pickup_mode.upper() != "LATER":
# #             self.send_ride_notifications(ride, driver_to_pickup_km, distance_km)
# #         else:
# #             # For later rides, you might want to schedule a task
# #             # Here you can use Celery, Django Q, or APScheduler
# #             self.schedule_later_ride_notification(ride)

# #     def send_ride_notifications(self, ride, driver_to_pickup_km, distance_km):
# #         """Send notifications to nearby drivers"""
# #         tokens = get_nearby_driver_tokens(ride.pickup_lat, ride.pickup_lng)
# #         if tokens:
# #             notification = {
# #                 "title": "New Ride Request 🚖",
# #                 "body": f"Pickup near you: {ride.pickup}, - {ride.drop}"
# #             }
# #             data_payload = {
# #                 "ride_id": str(ride.id),
# #                 "booking_id": str(ride.booking_id),
# #                 "pickup_location": str(ride.pickup),
# #                 "drop_location": str(ride.drop),
# #                 "driver_to_pickup_km": str(round(driver_to_pickup_km, 2)),  
# #                 "pickup_to_drop_km": str(round(distance_km, 2)),
# #                 "action": "NEW_RIDE"
# #             }

# #             print("Tokens found:", tokens)
# #             try:
# #                 response = send_multicast(tokens, notification=notification, data=data_payload)
# #                 print("Notification response:", response)
# #             except Exception as e:
# #                 logger.error(f"FCM send error: {e}")

# #     def schedule_later_ride_notification(self, ride):
# #         """
# #         Schedule notification for later rides
# #         You'll need to implement this based on your task queue system
# #         """
# #         # Example using Celery:
# #         # from .tasks import send_ride_notification_task
# #         # send_ride_notification_task.apply_async((ride.id,), eta=ride.pickup_time)
        
# #         # For APScheduler:
# #         # scheduler.add_job(
# #         #     send_ride_notifications,
# #         #     'date',
# #         #     run_date=ride.pickup_time,
# #         #     args=[ride]
# #         # )
        
# #         print(f"Ride scheduled for later at {ride.pickup_time}. Notifications will be sent then.")
# #         # For now, just log it
# #         logger.info(f"Later ride scheduled: Ride {ride.id} for {ride.pickup_time}")

# #     def create(self, request, *args, **kwargs):
# #         serializer = self.get_serializer(data=request.data)
# #         serializer.is_valid(raise_exception=True)
# #         self.perform_create(serializer)

# #         ride_data = serializer.data
# #         pickup_mode = request.data.get("pickup_mode", "").upper()
        
# #         if pickup_mode == "LATER":
# #             status_message = "Ride scheduled successfully"
# #         else:
# #             status_message = "Ride booked successfully"

# #         return Response({
# #             "statusCode": 1,
# #             "statusMessage": status_message,
# #             "ride": ride_data
# #         }, status=status.HTTP_201_CREATED)
    


# # from apscheduler.schedulers.background import BackgroundScheduler

# # scheduler = BackgroundScheduler()
# # scheduler.start()

# # def schedule_later_ride_notification(self, ride):
# #     from .utils import send_ride_notifications
# #     scheduler.add_job(
# #         send_ride_notifications,
# #         'date',
# #         run_date=ride.pickup_time,
# #         args=[ride],
# #         id=f'ride_notification_{ride.id}'
# #     )




# import logging
# import random
# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.serializers import ValidationError
# from django.utils import timezone
# from .utils import calculate_distance, get_nearby_driver_tokens, get_nearest_driver_distance
# from .serializers import *
# from ApniRide.firebase_app import send_multicast
# from .views import calculate_fare,calculate_incentives_and_rewards
#  # moved scheduler into its own file (cleaner)

# import logging
# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.serializers import ValidationError
# from django.utils import timezone
# import random

# from .utils import calculate_distance, get_nearby_driver_tokens, get_nearest_driver_distance
# from .serializers import *
# from ApniRide.firebase_app import send_multicast
# from .models import Ride

# # APScheduler
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.date import DateTrigger
# from django_apscheduler.jobstores import register_events

# # 🔹 Setup logger
# logger = logging.getLogger()

# # 🔹 Scheduler instance
# scheduler = BackgroundScheduler(timezone="UTC")

# def start():
#     if not scheduler.running:
#         register_events(scheduler)
#         scheduler.start()
#         logger.info("APScheduler started successfully.")

# def schedule_ride_notification(ride_id, pickup_time):
#     trigger = DateTrigger(run_date=pickup_time)
#     scheduler.add_job(
#         send_ride_notification,
#         trigger=trigger,
#         args=[ride_id],
#         id=f"ride_{ride_id}",
#         replace_existing=True,
#     )
#     logger.info(f"Notification scheduled for ride {ride_id} at {pickup_time}")


# def send_ride_notification(ride_id):
#     try:
#         ride = Ride.objects.get(id=ride_id)
#         tokens = get_nearby_driver_tokens(ride.pickup_lat, ride.pickup_lng)

#         if not tokens:
#             logger.warning(f"⚠️ No drivers found for scheduled ride {ride.id}.")
#             return

#         notification = {
#             "title": "New Ride Request 🚖",
#             "body": f"Pickup near you: {ride.pickup},-{ride.drop}"
#         }
#         data_payload = {
#             "ride_id": str(ride.id),
#             "booking_id": str(ride.booking_id),
#             "pickup_location": str(ride.pickup),
#             "drop_location": str(ride.drop),
#             "driver_to_pickup_km": "0",
#             "pickup_to_drop_km": str(round(ride.distance_km, 2)),
#             "action": "NEW_RIDE"
#         }

#         response = send_multicast(tokens, notification=notification, data=data_payload)
#         logger.info(f"📨 Scheduled notification sent for ride {ride.id}, response: {response}")

#     except Exception as e:
#         logger.error(f"❌ Error sending scheduled ride notification for ride {ride_id}: {e}")


# class BookRideView(generics.CreateAPIView):
#     serializer_class = RideSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         type = self.request.data.get("type")
#         print("self.request.data.get",type)
#         pickup_lat = self.request.data.get("pickup_lat")
#         pickup_lng = self.request.data.get("pickup_lng")
#         vehicle_type = self.request.data.get("vehicle_type")
#         pickup_mode = self.request.data.get("pickup_mode")
#         drop_lat = self.request.data.get("drop_lat")
#         drop_lng = self.request.data.get("drop_lng")
#         pickup_time = self.request.data.get("pickup_time")
#         booking_id = str(random.randint(1000, 9999))

#         # Validate numbers
#         try:
#             pickup_lat = float(pickup_lat)
#             pickup_lng = float(pickup_lng)
#             drop_lat = float(drop_lat) if drop_lat else None
#             drop_lng = float(drop_lng) if drop_lng else None
#         except (ValueError, TypeError):
#             raise ValidationError("Coordinates must be valid numbers.")

#         if not all([pickup_lat, pickup_lng, vehicle_type, pickup_mode]):
#             raise ValidationError("pickup_lat, pickup_lng, vehicle_type, and pickup_mode are required.")

#         if pickup_mode.upper() == "LATER" and not pickup_time:
#             raise ValidationError("pickup_time is required when pickup_mode is 'LATER'.")

#         distance_km = float(self.request.data.get("distance_km", 0))
#         if drop_lat and drop_lng:
#             distance_km = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)

#         fare = calculate_fare(vehicle_type, distance_km)
#         driver_incentive, customer_reward = calculate_incentives_and_rewards(distance_km)

#         nearest_driver, driver_to_pickup_km = get_nearest_driver_distance(pickup_lat, pickup_lng)

#         ride = serializer.save(
#             user=self.request.user,
#             pickup_lat=pickup_lat,
#             pickup_lng=pickup_lng,
#             drop_lat=drop_lat,
#             drop_lng=drop_lng,
#             pickup_mode=pickup_mode.upper(),
#             pickup_time=pickup_time if pickup_mode.upper() == "LATER" else timezone.now(),
#             distance_km=distance_km,
#             fare=fare,
#             driver_incentive=driver_incentive,
#             customer_reward=customer_reward,
#             vehicle_type=vehicle_type,
#             booking_id=booking_id
#         )

#         # Notification handling
#         if pickup_mode.upper() == "NOW":
#             tokens = get_nearby_driver_tokens(ride.pickup_lat, ride.pickup_lng)
#             if tokens:
#                 notification = {"title": "New Ride Request 🚖", "body": f"Pickup near you: {ride.pickup},-{ride.drop}"}
#                 data_payload = {
#                     "ride_id": str(ride.id),
#                     "booking_id": str(ride.booking_id),
#                     "pickup_location": str(ride.pickup),
#                     "drop_location": str(ride.drop),
#                     "driver_to_pickup_km": str(round(driver_to_pickup_km, 2)),
#                     "pickup_to_drop_km": str(round(distance_km, 2)),
#                     "action": "NEW_RIDE"
#                 }
#                 send_multicast(tokens, notification=notification, data=data_payload)
#                 logger.info(f"📨 Instant ride notification sent for ride {ride.id}")
#         else:
#             # Schedule for later ride
#             schedule_ride_notification(ride.id, ride.pickup_time)

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         return Response({
#             "statusCode": 1,
#             "statusMessage": "Ride booked successfully",
#             "ride": serializer.data
#         }, status=status.HTTP_201_CREATED)


# 03.10.25

import logging
import random
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework import serializers

from .models import Ride, Payment, DriverWallet
from .utils import (
    calculate_distance,
    get_nearby_driver_tokens, 
    get_nearest_driver_distance
)
from .serializers import RideSerializer
from ApniRide.firebase_app import send_multicast

# APScheduler imports
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from django_apscheduler.jobstores import register_events

logger = logging.getLogger(__name__)

# Scheduler instance
scheduler = BackgroundScheduler(timezone="UTC")

def start_scheduler():
    """Start the APScheduler if not running"""
    if not scheduler.running:
        register_events(scheduler)
        scheduler.start()
        logger.info("APScheduler started successfully.")

def schedule_ride_notification(ride_id, pickup_time):
    """Schedule a ride notification for later rides"""
    trigger = DateTrigger(run_date=pickup_time)
    scheduler.add_job(
        send_ride_notification,
        trigger=trigger,
        args=[ride_id],
        id=f"ride_notification_{ride_id}",
        replace_existing=True,
    )
    logger.info(f"Notification scheduled for ride {ride_id} at {pickup_time}")

def send_ride_notification(ride_id):
    """Send notifications to nearby drivers for a scheduled ride"""
    try:
        ride = Ride.objects.get(id=ride_id)
        tokens = get_nearby_driver_tokens(ride.pickup_lat, ride.pickup_lng)

        if not tokens:
            logger.warning(f"⚠️ No drivers found for scheduled ride {ride.id}.")
            return

        notification = {
            "title": "New Ride Request 🚖",
            "body": f"Pickup near you: {ride.pickup} - {ride.drop}"
        }
        data_payload = {
            "ride_id": str(ride.id),
            "booking_id": str(ride.booking_id),
            "pickup_location": str(ride.pickup),
            "drop_location": str(ride.drop),
            "driver_to_pickup_km": "0",  # Default for scheduled
            "pickup_to_drop_km": str(round(ride.distance_km, 2)),
            "action": "NEW_RIDE"
        }

        response = send_multicast(tokens, notification=notification, data=data_payload)
        logger.info(f"📨 Scheduled notification sent for ride {ride.id}, response: {response}")

    except Ride.DoesNotExist:
        logger.error(f"❌ Ride {ride_id} not found for scheduled notification.")
    except Exception as e:
        logger.error(f"❌ Error sending scheduled ride notification for ride {ride_id}: {e}")


class RideSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    driver_name = serializers.CharField(source="driver.username", read_only=True, allow_null=True)

    class Meta:
        model = Ride
        fields = '__all__'
        read_only_fields = [
            'user', 'driver', 'status', 'fare', 'completed',
            'paid', 'created_at', 'completed_at', 'driver_incentive', 'customer_reward',
            'booking_id', 'otp', 'rating', 'feedback'
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['username'] = instance.user.username if instance.user else None
        rep['driver_name'] = instance.driver.username if instance.driver else None
        return rep

    def validate(self, data):
        pickup_mode = data.get('pickup_mode', '').upper()
        if pickup_mode not in ['NOW', 'LATER']:
            raise serializers.ValidationError("pickup_mode must be 'NOW' or 'LATER'.")
        data['pickup_mode'] = pickup_mode  # Normalize
        return data


class BookRideView(generics.CreateAPIView):
    serializer_class = RideSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        payment_type = self.request.data.get("type", "cod").lower()
        print(f"Payment type: {payment_type}")
        
        # Extract and validate mandatory fields
        pickup = self.request.data.get("pickup")
        drop = self.request.data.get("drop")
        pickup_lat = self.request.data.get("pickup_lat")
        pickup_lng = self.request.data.get("pickup_lng")
        vehicle_type = self.request.data.get("vehicle_type")
        pickup_mode = self.request.data.get("pickup_mode", "NOW").upper()
        print(f"Pickup: {pickup}")
        print(f"Drop: {drop}")
        
        # Optional fields
        drop_lat = self.request.data.get("drop_lat")
        drop_lng = self.request.data.get("drop_lng")
        pickup_time_str = self.request.data.get("pickup_time")
        print("pickup_time""2025-10-06T14:00:00Z",pickup_time_str)
        booking_id = str(random.randint(1000, 9999))
        
        # Validate coordinates
        try:
            pickup_lat = float(pickup_lat)
            pickup_lng = float(pickup_lng)
            drop_lat = float(drop_lat) if drop_lat else None
            drop_lng = float(drop_lng) if drop_lng else None
        except (ValueError, TypeError):
            raise ValidationError("Coordinates must be valid numbers.")

        # Validate mandatory fields
        if not all([pickup_lat, pickup_lng, vehicle_type, pickup_mode, pickup, drop]):
            raise ValidationError("pickup_lat, pickup_lng, vehicle_type, pickup_mode, pickup, and drop are required.")

        # Validate and parse pickup_time for 'LATER' mode
        pickup_time_obj = timezone.now()
        if pickup_mode == "LATER":
            if not pickup_time_str:
                raise ValidationError("pickup_time is required when pickup_mode is 'LATER'.")
            try:
                pickup_time_obj = timezone.datetime.fromisoformat(pickup_time_str.replace('Z', '+00:00'))
                print("pickup_time" "2025-10-06T14:00:00Z",pickup_time_obj)
                if pickup_time_obj <= timezone.now():
                    raise ValidationError("pickup_time must be in the future for 'LATER' mode.")
            except (ValueError, AttributeError):
                raise ValidationError("pickup_time must be a valid ISO format datetime string.")

        # Calculate distance
        # if distance_km == 0 or distance_km is None:
        try:
            distance_km = float(self.request.data.get("distance_km", 0))

            # distance_km = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
        except Exception as e:
            raise ValidationError(f"Error calculating distance: {str(e)}")
        print("distance_km",distance_km)
        # Calculate fare and incentives
        try:
            overall = calculate_fare(vehicle_type, distance_km)
            fare = int(overall['total_user_pays'])
            gst_amount =int(overall['gst_amount'])
            commission_amount = int(overall['commission_amount'])
            driver_earnings = int(overall['driver_earnings'])
            company_revenue = int(overall['company_revenue'])
            # driver_incentive, customer_reward = calculate_incentives_and_rewards(distance_km)
        except Exception as e:
            raise ValidationError(f"Error calculating fare or incentives: {str(e)}")

        # Get nearest driver and distance (for immediate rides only)
        nearest_driver = None
        driver_to_pickup_km = 0
        if pickup_mode == "NOW":
            nearest_driver, driver_to_pickup_km = get_nearest_driver_distance(pickup_lat, pickup_lng)
            print(f"Nearest driver: {nearest_driver}")
            print(f"Distance to pickup (km): {driver_to_pickup_km}")
            if nearest_driver is None:
                raise ValidationError({
                    "statusCode": 0,
                    "statusMessage": "No drivers available nearby. Please try again later."
                })
        # Pickup to drop distance 
        pickup_to_drop_km = distance_km  # Already calculated

        print(f"Pickup to Drop distance (km): {pickup_to_drop_km}")
        
        # Save ride and handle payment within transaction
        with transaction.atomic():
            ride = serializer.save(
                user=self.request.user,
                pickup=pickup,
                drop=drop,
                pickup_lat=pickup_lat,
                pickup_lng=pickup_lng,
                drop_lat=drop_lat,
                drop_lng=drop_lng,
                pickup_mode=pickup_mode,
                pickup_time=pickup_time_obj,
                distance_km=distance_km,
                fare=fare,
                gst_amount = gst_amount,
                commission_amount = commission_amount,
                driver_earnings = driver_earnings,
                driver_to_pickup_km = driver_to_pickup_km,
                fare_estimate = company_revenue+gst_amount,
                vehicle_type=vehicle_type,
                booking_id=booking_id,
                payment_type = payment_type,
                status='pending',  # Default status
                paid=False  # Will be updated in payment handling
            )

            # Handle payment creation
            print("calling handle_payment")
            self._handle_payment_creation(ride, fare, payment_type)

        # Send notifications or schedule
        if pickup_mode == "NOW":
            self._send_ride_notifications(ride, driver_to_pickup_km, distance_km)
        else:
            # schedule_ride_notification(ride.id, ride.pickup_time)
            from api.tasks import send_scheduled_ride_notification
            delay_seconds = (pickup_time_obj - timezone.now()).total_seconds()
            send_scheduled_ride_notification.apply_async(
                args=[ride.id],
                countdown=delay_seconds
            )

    def _handle_payment_creation(self, ride, fare, payment_type):
        print("fare",fare)
        print("paymentyoe",payment_type)
        """Create Payment record based on payment type"""
        if payment_type == 'cod':
            Payment.objects.create(
                user=self.request.user,
                ride=ride,
                razorpay_order_id='',  # Not applicable for COD
                method='Cash',
                paid=False,
                status='PENDING'
            )
            logger.info(f"COD payment record created for ride {ride.id}")

        elif payment_type == 'wallet':
            try:
                # wallet = self.request.user
                wallet, _ = DriverWallet.objects.get_or_create(driver=self.request.user)
                print("wallet",wallet)
                if wallet.balance < Decimal(str(fare)):
                    raise ValidationError({"StatusCode":"0","StatusMessage":"Insufficient wallet balance for this ride","Balance":wallet.balance})

                # Debit wallet and log transaction
                print("ff",Decimal(str(fare)),ride.booking_id,)
                wallet.withdraw(
                    Decimal(str(fare)), 
                    description=f"Ride payment for booking {ride.booking_id}", 
                    transaction_type='ride_payment'
                )
                print("completed",self.request.user)
                # Create completed payment record
                Payment.objects.create(
                    user=self.request.user,
                    ride=ride,
                    razorpay_order_id='',  # Not applicable for wallet
                    method='WALLET',
                    paid=True,
                    status='COMPLETED'
                )
                
                # Update ride as paid
                ride.paid = True
                ride.save(update_fields=['paid'])
                
                logger.info(f"Wallet payment completed for ride {ride.id}")
            except ValidationError:
                raise  # Re-raise validation errors
            except Exception as e:
                logger.error(f"Wallet payment failed for ride {ride.id}: {e}")
                raise ValidationError("Wallet payment failed. Please try another method.")

        elif payment_type == 'razorpay':
            # Create pending payment record (frontend will handle initiation and verify later)
            temp_order_id = f"order_{ride.id}_{int(timezone.now().timestamp())}"
            Payment.objects.create(
                user=self.request.user,
                ride=ride,
                razorpay_order_id=temp_order_id,  # Temp ID for tracking; update on verification
                razorpay_payment_id='',
                razorpay_signature='',
                method='UPI',  # Default; update based on actual method later
                paid=False,
                status='PENDING'
            )
            logger.info(f"Razorpay pending payment record created for ride {ride.id} (Temp Order: {temp_order_id})")

        else:
            raise ValidationError("Invalid payment type. Supported: cod, wallet, razorpay")

    def _send_ride_notifications(self, ride, driver_to_pickup_km, distance_km):
        """Send notifications to nearby drivers"""
        driver_to_pickup_km = driver_to_pickup_km or 0
        distance_km = distance_km or 0
        tokens = get_nearby_driver_tokens(ride.pickup_lat, ride.pickup_lng,vehicle_type=ride.vehicle_type)
        if tokens:
            notification = {
                "title": "New Ride Request 🚖",
                "body": f"Pickup near you: {ride.pickup} - {ride.drop}"
            }
            data_payload = {
                "ride_id": str(ride.id),
                "booking_id": str(ride.booking_id),
                "pickup_location": str(ride.pickup),
                "drop_location": str(ride.drop),
                "driver_to_pickup_km": str(round(driver_to_pickup_km, 2)),  
                "pickup_to_drop_km": str(round(distance_km, 2)),
                "excepted_earnings":str(round(ride.driver_earnings,0)),
                "user_number":ride.user.mobile,
                "action": "NEW_RIDE"
            }

            print(f"Tokens found: {tokens}")
            try:
                response = send_multicast(tokens, notification=notification, data=data_payload)
                print(f"Notification response: {response}")
                logger.info(f"📨 Instant ride notification sent for ride {ride.id}")
            except Exception as e:
                logger.error(f"FCM send error for ride {ride.id}: {e}")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Refresh serializer to include updates (e.g., paid status)
        ride = Ride.objects.get(id=serializer.data['id'])
        serializer = self.get_serializer(ride)

        pickup_mode = request.data.get("pickup_mode", "NOW").upper()
        status_message = "Ride scheduled successfully" if pickup_mode == "LATER" else "Ride booked successfully"

        response_data = {
            "statusCode": 1,
            "statusMessage": status_message,
            "ride": serializer.data
        }

        # Include payment info
        payment_type = request.data.get("type", "cod").lower()
        if payment_type == 'razorpay':
            response_data['payment'] = {
                'status': 'pending',
                'method': 'razorpay',
                'message': 'Please complete payment in the app to confirm the ride.'
            }
        elif payment_type == 'wallet':
            response_data['payment'] = {
                'status': 'completed',
                'method': 'wallet'
            }
        elif payment_type == 'cod':
            response_data['payment'] = {
                'status': 'pending',
                'method': 'cod',
                'message': 'Payment will be collected by the driver.'
            }

        return Response(response_data, status=status.HTTP_201_CREATED)
    
    