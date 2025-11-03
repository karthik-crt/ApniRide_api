import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance in kilometers between two GPS coordinates
    using the Haversine formula.
    """
    # Convert strings/floats to float
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

    # Radius of the Earth in km
    R = 6371.0
    # Convert degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return round(distance, 2)  # distance in km rounded to 2 decimals


# rides/utils.py
import math


def haversine_distance(lat1, lng1, lat2, lng2):
    # returns kilometers
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


from .models import User


def find_nearby_drivers(pickup_lat, pickup_lng, radius_km=5, limit=10):
    candidates = User.objects.filter(is_available=True).exclude(fcm_token__isnull=True).exclude(fcm_token='')
    nearby = []
    for d in candidates:
        if d.lat is None or d.lng is None:
            continue
        dist = haversine_distance(pickup_lat, pickup_lng, d.lat, d.lng)
        if dist <= radius_km:
            nearby.append((dist, d))
    nearby.sort(key=lambda x: x[0])
    return [d for _, d in nearby[:limit]]

from .models import DriverLocation

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# def get_nearby_driver_tokens(pickup_lat, pickup_lng, radius_km=5):
#     drivers = User.objects.exclude(fcm_token__isnull=True).exclude(fcm_token="")
#     tokens = []
#     for d in drivers:
#         if d.current_lat and d.current_lng:
#             dist = haversine(pickup_lat, pickup_lng, d.current_lat, d.current_lng)
#             print(f"Driver {d.username}: {dist} km away")
#             if dist <= radius_km:
#                 tokens.append(d.fcm_token)
#     print("Nearby drivers:", tokens)                
#     return tokens

def get_nearby_driver_tokens(pickup_lat, pickup_lng, radius_km=5, vehicle_type=None):
    """
    Returns FCM tokens for nearby drivers filtered by vehicle type (if given).
    If vehicle_type == 'any' or None, all drivers are included.
    """
    # Base queryset: only drivers with valid FCM tokens
    drivers = (
        User.objects.filter(is_driver=True, is_available=True, is_online=True)
        .exclude(fcm_token__isnull=True)
        .exclude(fcm_token="")
        .exclude(current_lat__isnull=True)
        .exclude(current_lng__isnull=True)
    )

    # Filter by vehicle_type unless it's "any" or empty
    if vehicle_type and vehicle_type.lower() != "any":
        drivers = drivers.filter(vehicle_type__iexact=vehicle_type)

    tokens = []
    for d in drivers:
        if d.current_lat and d.current_lng:
            dist = haversine(pickup_lat, pickup_lng, d.current_lat, d.current_lng)
            print(f"Driver {d.username}: {dist} km away ({getattr(d, 'vehicle_type', 'N/A')})")
            if dist <= radius_km:
                tokens.append(d.fcm_token)

    print(f"Nearby {vehicle_type or 'all'} drivers:", tokens)
    return tokens


def get_nearest_driver_distance(pickup_lat, pickup_lng):
    drivers = User.objects.filter(is_driver=True,is_available=True,is_online=True)\
                          .exclude(current_lat__isnull=True, current_lng__isnull=True)
    nearest_driver = None
    min_distance = None

    for driver in drivers:
        dist = calculate_distance(pickup_lat, pickup_lng, driver.current_lat, driver.current_lng)
        if min_distance is None or dist < min_distance:
            min_distance = dist
            nearest_driver = driver
    
    return nearest_driver, min_distance


from django.template.loader import render_to_string
from xhtml2pdf import pisa
import tempfile

def generate_invoice_pdf(ride):
    html = render_to_string('invoice_template.html', {'ride': ride})
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output:
        pisa_status = pisa.CreatePDF(html, dest=output)
        if pisa_status.err:
            return None
        return output.name
    

# utils.py
from django.db.models import Avg, Count
from .models import *

def get_driver_rating_summary(driver_id):
    ratings = DriverRating.objects.filter(driver_id=driver_id)

    avg_rating = ratings.aggregate(Avg("stars"))["stars__avg"] or 0
    total_reviews = ratings.count()

    # Distribution (1-5 stars)
    distribution = ratings.values("stars").annotate(count=Count("stars"))

    return {
        "avg_rating": round(avg_rating, 1),
        "total_reviews": total_reviews,
        "distribution": {d["stars"]: d["count"] for d in distribution},
        "recent_feedback": ratings.order_by("-created_at")[:10],  # last 10 feedbacks
    }

from datetime import date
from decimal import Decimal
from django.db import transaction

# def update_driver_incentive_progress(driver, ride):
#     """
#     Update or create a DriverIncentiveProgress record after a ride is completed,
#     and credit incentive if earned but not already paid.
#     """
#     # Fetch active incentives for the ride type
#     active_incentives = DriverIncentive.objects.all()


#     driver_wallet, _ = DriverWallet.objects.get_or_create(driver=driver)

#     for incentive in active_incentives:
#         progress, _ = DriverIncentiveProgress.objects.get_or_create(
#             driver=driver,
#             incentive_rule=incentive,
#         )

#         # Update progress
#         progress.rides_completed += 1
#         progress.travelled_distance += ride.distance_km or 0

#         # Check if incentive is earned and not paid yet
#         incentive_earned = (
#             (incentive.days and progress.rides_completed >= incentive.days) or
#             (incentive.distance and progress.travelled_distance >= incentive.distance)
#         )
#         if incentive_earned and not progress.earned:
#             progress.earned = True
#             driver_wallet.add_incentive(
#                 amount=incentive.driver_incentive,
#                 transaction_type = "driver_incentive",
#                 description=f"Incentive completed by Driver #{ride.driver.id} for Ride #{ride.booking_id}"
#             )
#             progress.earned = True  # Mark as credited

#         progress.save()

def update_driver_incentive_progress(driver, ride):
    driver_wallet, _ = DriverWallet.objects.get_or_create(driver=driver)
    active_incentives = DriverIncentive.objects.all()

    for incentive in active_incentives:
        ride_type_for_incentive = get_ride_type(ride.distance_km, incentive)

        # Skip incentives that don't match the current ride
        if ride_type_for_incentive is None:
            continue

        progress, _ = DriverIncentiveProgress.objects.get_or_create(
            driver=driver,
            incentive_rule=incentive,
        )

        # Update progress
        progress.rides_completed += 1
        progress.travelled_distance += ride.distance_km or 0

        # Check if incentive earned
        incentive_earned = (
            (incentive.days and progress.rides_completed >= incentive.days) or
            (incentive.distance and progress.travelled_distance >= incentive.distance)
        )

        if incentive_earned and not progress.earned:
            driver_wallet.add_incentive(
                amount=incentive.driver_incentive,
                transaction_type="driver_incentive",
                ride=ride,
                description=f"Incentive completed by Driver #{driver.id} for Ride #{ride.booking_id}"
            )
            progress.earned = True
        print("Incentive Progress:", progress.rides_completed, progress.travelled_distance, progress.earned)
        progress.save()


def get_ride_type(travelled_distance, incentive):
    """
    Determine the ride type for this incentive.
    """
    if incentive.distance is None:
        return "city"
    elif incentive.ride_type == "city_distance":
        # For city_distance incentives with min/max km
        if incentive.distance <= travelled_distance <= (incentive.max_distance or float('inf')):
            return "city_distance"
        else:
            return None
    elif incentive.distance < travelled_distance < (incentive.max_distance or float('inf')):
        return "long"
    else:
        return "tourist"

#Admin


def get_or_create_admin_wallet():
    wallet, created = AdminWallet.objects.get_or_create(name="Platform Main Wallet")
    return wallet

def calculate_ride_commission(ride_amount, commission_percentage=10):
    if not isinstance(ride_amount, Decimal):
        ride_amount = Decimal(ride_amount)
    commission = (ride_amount * Decimal(commission_percentage)) / Decimal(100)
    return commission.quantize(Decimal('0.01'))

def calculate_ride_gst(ride_amount, gst_percentage=5):
    if not isinstance(ride_amount, Decimal):
        ride_amount = Decimal(ride_amount)
    gst = (ride_amount * Decimal(gst_percentage)) / Decimal(100)
    return gst.quantize(Decimal('0.01'))

def process_ride_payment(ride, ride_amount, driver_wallet, commission_percentage=10, gst_percentage=5):
    admin_wallet = get_or_create_admin_wallet()
    
    commission = calculate_ride_commission(ride_amount, commission_percentage)
    gst = calculate_ride_gst(ride_amount, gst_percentage)
    driver_earnings = ride_amount - commission - gst
    
    try:
        # Collect Commission & GST
        admin_wallet.collect_commission(commission, ride=ride, description=f"Commission from ride #{ride.id}")
        admin_wallet.collect_gst(gst, ride=ride, description=f"GST from ride #{ride.id}")
        
        # Pay driver
        driver_wallet.deposit(driver_earnings, description=f"Earnings from ride #{ride.id}", transaction_type="ride_payment")
        return True, "Payment processed successfully"
    except Exception as e:
        return False, f"Payment processing failed: {str(e)}"




def refund_ride_amount(ride, user_wallet, refund_amount, refund_commission=Decimal("0.00"), refund_gst=Decimal("0.00")):
    admin_wallet = get_or_create_admin_wallet()
    
    try:
        admin_wallet.refund_to_user(
            amount=refund_amount,
            user_wallet=user_wallet,
            description=f"Refund for ride #{ride.id}",
            ride=ride,
            refund_commission=refund_commission,
            refund_gst=refund_gst
        )
        return True, "Refund processed successfully"
    except Exception as e:
        return False, f"Refund failed: {str(e)}"
