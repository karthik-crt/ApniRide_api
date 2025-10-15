# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse
from .models import Ride
from .utils import generate_invoice_pdf
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import *
import os

class RideInvoiceAPIView(APIView):
    def get(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=404)
        
        # Generate PDF
        pdf_path = generate_invoice_pdf(ride)
        
        # Return a file response
        filename = f"Invoice_{ride.booking_id}.pdf"
        return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename=filename)


class RideHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication

    def get(self, request):
        user = request.user
        # Now user is guaranteed to be authenticated
        rides = Ride.objects.filter(user=user).order_by('-pickup_time')
        serializer = RideHistorySerializer(rides, many=True, context={'request': request})
        return Response({"StatusCode":"1","StatusMessage":"Sucess","data":serializer.data})