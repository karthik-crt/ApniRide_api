# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from .models import Ride, User,DriverIncentiveProgress
from .serializers import DriverEarningsSerializer,DriverIncentiveProgressSerializer

class DriverEarningsAPIView(APIView):
    """
    API to get driver earnings and ride counts: daily, weekly, monthly
    """

    def get_rides_data(self, driver, start_date, end_date, period_name):
        rides = Ride.objects.filter(
            driver=driver,
            completed=True,
            completed_at__date__range=[start_date, end_date]
        )
        total_earnings = rides.aggregate(total=Sum('fare'))['total'] or 0
        total_rides = rides.count()

        return {
            'period': period_name,
            'total_earnings': total_earnings,
            'total_rides': total_rides
        }

    def get(self, request, driver_id):
        try:
            driver = User.objects.get(id=driver_id, is_driver=1)
        except User.DoesNotExist:
            return Response({"error": "Driver not found"}, status=404)

        today = timezone.now().date()

        # Daily
        daily_data = self.get_rides_data(driver, today, today, "daily")

        # Weekly (Monday to Sunday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        weekly_data = self.get_rides_data(driver, start_of_week, end_of_week, "weekly")

        # Monthly
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        monthly_data = self.get_rides_data(driver, first_day_of_month, last_day_of_month, "monthly")

        data = [daily_data, weekly_data, monthly_data]
        serializer = DriverEarningsSerializer(data, many=True)
        return Response({"StatusCode":"1","StatusMessage":"Sucess","data":serializer.data})


# views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import DriverWallet
from .serializers import DriverWalletSerializer, WalletTransactionSerializer

class DriverWalletDetailView(generics.RetrieveAPIView):
    """Get wallet balance"""
    serializer_class = DriverWalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Just return the wallet instance
        wallet, _ = DriverWallet.objects.get_or_create(driver=self.request.user)
        return wallet

    def retrieve(self, request, *args, **kwargs):
        wallet = self.get_object()
        serializer = self.get_serializer(wallet)
        return Response({
            "StatusCode": "1",
            "StatusMessage": "Success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class WalletDepositView(generics.GenericAPIView):
    """Deposit money to wallet"""
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet, _ = DriverWallet.objects.get_or_create(driver=request.user)
        amount = serializer.validated_data["amount"]
        wallet.deposit(amount)

        return Response({
            "StatusCode": "1",
            "message": "Deposit successful",
            "balance": wallet.balance
        }, status=status.HTTP_200_OK)

from .razorpay import withdraw_to_driver
from decimal import Decimal

class WalletWithdrawView(generics.GenericAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet, _ = DriverWallet.objects.get_or_create(driver=request.user)
        amount = serializer.validated_data["amount"]
        beneficiary_name = request.user.username  
        account_number = request.data.get("account_number")
        ifsc = request.data.get("ifsc")
        try:
            wallet.withdraw(amount)
        except ValueError as e:
            # Explicit StatusCode for error
            return Response({
                "StatusCode": "0",
                "StatusMessage": str(e),
                "balance": wallet.balance
            }, status=status.HTTP_400_BAD_REQUEST)

        driver_wallet = DriverWallet.objects.get(driver=request.user)

        result = withdraw_to_driver(
            driver_wallet=driver_wallet,
            amount=Decimal(request.data.get("amount", 0)),
            beneficiary_name=beneficiary_name,
            account_number=account_number,
            ifsc=ifsc
        )
        print("withdraw result",result)
        
        if result['success']:
            print("Withdraw successful! New balance:", result['balance'])
            print("Payout ID:", result['payout_id'])
        else:
            print("Withdraw failed:", result['error'])

        # Explicit StatusCode for success
        return Response({
            "StatusCode": "1",
            "StatusMessage": "Withdrawal successful",
            "balance": wallet.balance
        }, status=status.HTTP_200_OK)



# views.py

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserWalletTransaction, DriverWallet
from .serializers import UserWalletTransactionSerializer

class DriverWalletTransactionHistoryView(generics.ListAPIView):
    serializer_class = UserWalletTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return transactions for the logged-in driver
        driver = self.request.user
        return UserWalletTransaction.objects.filter(wallet__driver=driver).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        wallet = DriverWallet.objects.filter(driver=request.user).first()
        current_balance = wallet.balance if wallet else 0
        return Response({
            "StatusCode":"1",
            "StatusMessage":"Sucess",
            "data":{
            "driver": request.user.username,
            "current_balance": current_balance,
            "transactions": serializer.data
            }
        })
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import DriverIncentive, DriverIncentiveProgress

class DriverIncentiveProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all incentive rules
        incentive_rules = DriverIncentive.objects.all().select_related('driver')
        
        data = []
        for rule in incentive_rules:
            print("ruke",rule)
            progress = DriverIncentiveProgress.objects.filter(incentive_rule=rule).first()
            print("progress",progress)
            rule_data = {
                'ride_type': rule.ride_type,
                'min_rides':f"{rule.days}Rides" if rule.days is not None else "N/A",
                'distance': f"{rule.distance}KM" if rule.distance is not None else "N/A", 
                'driver_incentive': float(rule.driver_incentive),
                'details': rule.details
            }
            if progress:
                rule_data.update({
                    'rides_completed': progress.rides_completed,
                    'travelled_distance': progress.travelled_distance,
                    'progress_percent': progress.progress_percent,
                    'earned': progress.earned
                })
            else:
                rule_data.update({
                    'rides_completed': 0,
                    'travelled_distance':0,
                    'progress_percent': 0.0,
                    'earned': False
                })
            data.append(rule_data)

        return Response({
            "StatusCode": "1",
            "StatusMessage": "Success",
            "data": data
        })