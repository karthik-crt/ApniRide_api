from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from .tasks import notify_ride_status

# User API to cancel a ride
class UserCancelRideViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ride_id):
        user = request.user
        new_status = request.data.get('status')
        ride = get_object_or_404(Ride, id=ride_id)

        
        if ride.status in ['completed', 'cancelled', 'cancelled_by_user']:
            return Response({
                "statusCode": "0",
                "statusMessage": f"Ride cannot be cancelled because it is {ride.status}."
            }, status=status.HTTP_400_BAD_REQUEST)

        
        if ride.driver != user and ride.user != user:
            return Response({
                "statusCode": "0",
                "statusMessage": "You are not authorized to cancel this ride."
            }, status=status.HTTP_403_FORBIDDEN)

        
        policy = CancellationPolicy.objects.filter(is_active=True).first()
        if not policy:
            return Response({
                "statusCode": "0",
                "statusMessage": "No active cancellation policy found."
            }, status=status.HTTP_400_BAD_REQUEST)

        
        cancelled_count = Ride.objects.filter(
            user=ride.user, is_cancelled_by_user=True
        ).count()

        charge = Decimal(policy.charge_amount) if cancelled_count >= policy.free_cancellations else Decimal("0.00")

        #  Handle wallets
        ride_wallet = ride.user.wallet
        admin_wallet, _ = AdminWallet.objects.get_or_create(name="Platform Wallet")

        if charge > 0:
            # Deduct from user wallet (allow negative)
            ride_wallet.balance -= charge
            ride_wallet.save(update_fields=["balance", "updated_at"])

            # Log user wallet transaction
            UserWalletTransaction.objects.create(
                wallet=ride_wallet,
                transaction_type="ride_payment",
                amount=-charge,
                description=f"Cancellation charge for Ride {ride.id}",
                balance_after=ride_wallet.balance,
                related_ride=ride
            )

            # Deposit into admin wallet
            admin_wallet.deposit(
                charge,
                description=f"Cancellation charge from {ride.user.username} for Ride {ride.id}",
                transaction_type="revenue"
            )

            # Mark old zero-charge cancellations as not free anymore
            Ride.objects.filter(
                user=ride.user,
                is_cancelled_by_user=True,
                cancellation_charge=0,
                status='cancelled_by_user'
            ).update(is_cancelled_by_user=False)

            ride.cancellation_charge = charge
            charge_status = "charged from wallet (wallet can go negative)"
        else:
            ride.cancellation_charge = Decimal("0.00")
            charge_status = "free cancellation"

        #  Update ride status
        ride.status = 'cancelled_by_user'
        ride.is_cancelled_by_user = True
        ride.cancelled_at = timezone.now()
        if ride.driver: 
            ride.driver.is_available = True
            ride.driver.save(update_fields=["is_available"])
        ride.save(update_fields=["status", "is_cancelled_by_user", "cancelled_at", "cancellation_charge"])

        #  Notify via WebSocket / FCM
        notify_ride_status(ride)

        #  Response
        return Response({
            "statusCode": "1",
            "statusMessage": "Ride cancelled successfully",
            "cancellation_charge": float(ride.cancellation_charge),
            "user_wallet_balance": float(ride_wallet.balance),
            "charge_status": charge_status,
            "remaining_free_cancellations": max(policy.free_cancellations - cancelled_count - 1, 0)
        }, status=status.HTTP_200_OK)