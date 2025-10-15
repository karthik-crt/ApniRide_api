# views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Ride, DriverRating
from .serializers import DriverRatingSerializer
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count
from rest_framework import status


class SubmitRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        print("in",Ride.user)
        try:
            ride = get_object_or_404(Ride, id=ride_id, user=request.user)
        except Ride.DoesNotExist as e:
            return Response({"error": "Ride not found"}, status=404)

        # Only allow rating if ride is completed
        if ride.status != 'completed':
            return Response({"error": "Ride not completed yet"}, status=400)

        stars = request.data.get("stars")
        feedback = request.data.get("feedback", "")

        if not stars or int(stars) not in range(1, 6):
            return Response({"error": "Stars must be between 1 and 5"}, status=400)

        rating, created = DriverRating.objects.update_or_create(
            ride=ride,
            user=request.user,
            driver=ride.driver,
            defaults={"stars": stars, "feedback": feedback}
        )

        # optional: sync to Ride model fields for backward compatibility
        ride.rating = stars
        ride.feedback = feedback
        ride.save(update_fields=["rating", "feedback"])

        serializer = DriverRatingSerializer(rating)
        return Response({"StatusCode":"1","StatusMessage":"Sucess","data":serializer.data})




from django.db.models import Avg, Count, F
from .models import Ride

class DriverRatingSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        driver = request.user
        ratings = DriverRating.objects.filter(driver=driver)

        avg_rating = ratings.aggregate(Avg("stars"))["stars__avg"] or 0
        total_reviews = ratings.count()

        # Distribution (1–5 stars)
        distribution = ratings.values("stars").annotate(count=Count("stars"))
        dist_dict = {i: 0 for i in range(1, 6)}
        for d in distribution:
            dist_dict[d["stars"]] = d["count"]

        # Ride summaries
        total_rides = Ride.objects.filter(driver=driver).count()
        completed_rides = Ride.objects.filter(driver=driver, completed=True).count()
        completion_rate = round((completed_rides / total_rides) * 100, 1) if total_rides else 0

        avg_trip_time = (
            Ride.objects.filter(driver=driver, completed=True)
            .exclude(completed_at=None)
            .annotate(duration=F("completed_at") - F("pickup_time"))
            .aggregate(avg_time=Avg("duration"))["avg_time"]
        )

        # Top destination
        top_destination = (
            Ride.objects.filter(driver=driver, completed=True)
            .values("drop")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")
            .first()
        )
        top_destination_name = top_destination["drop"] if top_destination else None

        data = {
            "avg_rating": round(avg_rating, 1),
            "total_reviews": total_reviews,
            "distribution": dist_dict,
            "recent_feedback": DriverRatingSerializer(ratings.order_by("-created_at")[:10], many=True).data,
            "ride_summary": {
                "total_rides": total_rides,
                "completion_rate": completion_rate,
                "avg_trip_time": str(avg_trip_time) if avg_trip_time else None,
                "top_destination": top_destination_name,
            }
        }
        return Response({"StatusCode":"1","StatusMessage":"Sucess","data":data})



class DriverDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure the user is a driver
        if not request.user.is_driver:
            return Response(
                {"error": "User is not a driver"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get today's date range (from midnight to now)
        today = timezone.now().date()
        start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(today, datetime.max.time()))

        # Calculate today's earnings (sum of fare for completed rides)
        today_earnings = (
            Ride.objects.filter(
                driver=request.user,
                status="completed",
                completed_at__range=[start_of_day, end_of_day]
            )
            .aggregate(total_earnings=Sum("fare"))
            .get("total_earnings") or 0.0
        )

        # Calculate average rating for the driver
        avg_rating = (
            DriverRating.objects.filter(driver=request.user)
            .aggregate(avg_stars=Avg("stars"))
            .get("avg_stars") or 0.0
        )
        # Round to 2 decimal places
        avg_rating = round(avg_rating, 2)

        # Count today's trips (completed or ongoing)
        trips_today = Ride.objects.filter(
            driver=request.user,
            status__in=["completed", "ongoing"],
            created_at__range=[start_of_day, end_of_day]
        ).count()

        # Prepare response data
        dashboard_data = {
            "today_earnings": float(today_earnings),  # Convert Decimal to float for JSON
            "average_rating": avg_rating,
            "trips_today": trips_today
        }

        return Response({"StatusCode":1,"StatusMessage":"Sucess","data":dashboard_data})
    
