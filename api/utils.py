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

def get_nearby_driver_tokens(pickup_lat, pickup_lng, radius_km=5):
    drivers = User.objects.exclude(fcm_token__isnull=True).exclude(fcm_token="")
    tokens = []
    for d in drivers:
        if d.current_lat and d.current_lng:
            dist = haversine(pickup_lat, pickup_lng, d.current_lat, d.current_lng)
            print(f"Driver {d.username}: {dist} km away")
            if dist <= radius_km:
                tokens.append(d.fcm_token)
    print("Nearby drivers:", tokens)                
    return tokens

def get_nearest_driver_distance(pickup_lat, pickup_lng):
    drivers = User.objects.filter(is_driver=True)\
                          .exclude(current_lat__isnull=True, current_lng__isnull=True)
    nearest_driver = None
    min_distance = None

    for driver in drivers:
        dist = calculate_distance(pickup_lat, pickup_lng, driver.current_lat, driver.current_lng)
        if min_distance is None or dist < min_distance:
            min_distance = dist
            nearest_driver = driver
    
    return nearest_driver, min_distance
