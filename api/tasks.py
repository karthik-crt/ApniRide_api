from django.utils import timezone
from django.db import transaction
from .models import User
import logging

logger = logging.getLogger(__name__)

def auto_reactivate_users():
    """Re-activate suspended users whose suspension time has expired."""
    now = timezone.now()
    with transaction.atomic():
        expired_users = User.objects.filter(
            account_status="suspended",
            suspended_until__lt=now
        )

        for user in expired_users:
            user.account_status = "active"
            user.suspended_until = None
            user.save(update_fields=["account_status", "suspended_until"])

            logger.info(f" Auto reactivated user {user.id}")
from celery import shared_task
from .models import DriverIncentiveProgress

@shared_task
def reset_earned_field():
    # Reset all earned fields to False
    DriverIncentiveProgress.objects.update(earned=False)
    return "DriverIncentiveProgress earned field reset to False"

from celery import shared_task
from django.utils import timezone
from .models import Ride
from .utils import get_nearby_driver_tokens
from ApniRide.firebase_app import send_multicast
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_scheduled_ride_notification(ride_id):
    try:
        print("working in ")
        ride = Ride.objects.get(id=ride_id)
        tokens = get_nearby_driver_tokens(ride.pickup_lat, ride.pickup_lng)
        if not tokens:
            logger.warning(f"No drivers found for scheduled ride {ride.id}.")
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
            "driver_to_pickup_km": "0",
            "pickup_to_drop_km": str(round(ride.distance_km, 2)),
            "action": "NEW_RIDE"
        }

        response = send_multicast(tokens, notification=notification, data=data_payload)
        logger.info(f"Scheduled ride notification sent for ride {ride.id}: {response}")

    except Ride.DoesNotExist:
        logger.error(f"Ride {ride_id} not found for scheduled notification.")
    except Exception as e:
        logger.error(f"Error sending scheduled ride notification for ride {ride_id}: {e}")
