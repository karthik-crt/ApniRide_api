from rest_framework import generics, permissions, response, status
from django.db import transaction
from decimal import Decimal
from .models import *
from .serializers import *

class PaymentRefundView(generics.GenericAPIView):
    """Create a refund request for a ride"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        refund_amount = request.data.get("refund_amount")
        booking_id = request.data.get("booking_id")

        if not booking_id:
            return response.Response(
                {"error": "booking_id is required."},
                status=status.HTTP_200_OK
            )
        
        if not refund_amount:
            return response.Response(
                {"error": "refund_amount is required."},
                status=status.HTTP_200_OK
            )

        try:
            ride = Ride.objects.get(booking_id=booking_id)
        except Ride.DoesNotExist:
            return response.Response(
                {"error": "Ride not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not ride.paid:
            return response.Response(
                {"error": "Cannot refund an unpaid ride."},
                status=status.HTTP_200_OK
            )

        driver = ride.driver
        user = ride.user

        # Fetch or create wallets
        driver_wallet, _ = DriverWallet.objects.get_or_create(driver=driver)
        user_wallet, _ = DriverWallet.objects.get_or_create(driver=user) 

        # Use ride fare as refund amount if not provided
        refund_amount = Decimal(refund_amount or ride.fare)

        driver_wallet.withdraw(
            amount=refund_amount,
            description=f"Refund for Ride {ride.booking_id}",
            transaction_type="refund"
        )

        user_wallet.deposit(
            amount=refund_amount,
            description=f"Refund received for Ride {ride.booking_id}",
            transaction_type="refund"
        )

        return response.Response({
            "StatusCode":"1",
            "message": "Refund processed successfully.",
            "ride_id": ride.id,
            "refund_amount": str(refund_amount),
            "driver_wallet_balance": str(driver_wallet.balance),
            "user_wallet_balance": str(user_wallet.balance),
        }, status=status.HTTP_200_OK)
