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
        ride_id = request.data.get("ride_id" or None)
        if ride_id:
            try:
                ride = Ride.objects.get(id=ride_id) 
            except Ride.DoesNotExist:
                return Response({
                    "StatusCode": "0",
                    "message": f"Ride with id {ride_id} not found"
                }, status=status.HTTP_400_BAD_REQUEST)

            cashback_amount = Decimal(amount)
            wallet.add_cashback(
                amount=cashback_amount,
                ride=ride, 
                description=f"Cashback credited for Ride {ride_id}",
            )
            message = "Cashback credited successfully"
        else:
            wallet.deposit(amount)
            message = "Deposit successful"

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

from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserWalletTransaction, DriverWallet
from .serializers import UserWalletTransactionSerializer

class DriverWalletTransactionHistoryView(generics.ListAPIView):
    serializer_class = UserWalletTransactionSerializer
    permission_classes = [IsAuthenticated]

    def make_aware_if_naive(self, dt):
        """Safely make a datetime aware if it's naive"""
        if timezone.is_naive(dt):
            return timezone.make_aware(dt)
        return dt

    def get_queryset(self):
        driver = self.request.user
        queryset = UserWalletTransaction.objects.filter(wallet__driver=driver).order_by('-created_at')

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        filter_type = self.request.query_params.get('filter_type')

    
        if not start_date and not end_date and not filter_type:
            return queryset

      
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                start_date = self.make_aware_if_naive(start_date)
                end_date = self.make_aware_if_naive(end_date)
                queryset = queryset.filter(created_at__range=[start_date, end_date])
            except ValueError:
                pass

       
        elif filter_type:
            now = timezone.now()

            if filter_type.lower() == 'daily':
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end = now.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(created_at__range=[start, end])

            elif filter_type.lower() == 'weekly':
                start = now - timedelta(days=now.weekday())  # Monday
                end = start + timedelta(days=7)
                queryset = queryset.filter(created_at__range=[start, end])

            elif filter_type.lower() == 'monthly':
                start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if now.month == 12:
                    end = start.replace(year=now.year + 1, month=1)
                else:
                    end = start.replace(month=now.month + 1)
                queryset = queryset.filter(created_at__range=[start, end])

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        wallet = DriverWallet.objects.filter(driver=request.user).first()
        current_balance = wallet.balance if wallet else 0

        return Response({
            "StatusCode": "1",
            "StatusMessage": "Success",
            "data": {
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