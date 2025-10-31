from django.db.models import Sum
from rest_framework import generics, permissions, response
from .models import *
from .serializers import *


class AdminWalletTransactionListAPI(generics.ListAPIView):
    """
    API endpoint to list all admin wallet transactions
    + optional filters (type, user, date range)
    + includes totals summary.
    """
    serializer_class = AdminWalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]  # or custom IsAdminUserOnly

    def get_queryset(self):
        queryset = AdminWalletTransaction.objects.select_related(
            'related_user', 'related_ride', 'wallet'
        )

        # Optional Filters
        txn_type = self.request.query_params.get('type')
        user_id = self.request.query_params.get('user_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if txn_type:
            queryset = queryset.filter(transaction_type=txn_type)
        if user_id:
            queryset = queryset.filter(related_user_id=user_id)
        if start_date and end_date:
            queryset = queryset.filter(created_at__date__range=[start_date, end_date])
        elif start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        elif end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        
        totals = queryset.aggregate(
            total_amount=Sum('amount') or 0,
            total_commission=Sum('commission_amount') or 0,
            total_gst=Sum('gst_amount') or 0,
        )

        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'summary': totals,
                'transactions': serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return response.Response({
            'summary': totals,
            'transactions': serializer.data
        })

from rest_framework import generics, permissions, response, status
class PaymentHistoryView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserWalletHistorySerializer

    def get(self, request, *args, **kwargs):
        # Fetch all wallet transactions
        queryset = UserWalletTransaction.objects.all().order_by('-created_at')

        serializer = self.serializer_class(queryset, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
    

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CancellationPolicy
from .serializers import CancellationPolicySerializer
from rest_framework.permissions import IsAdminUser

class CancellationPolicyListCreate(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        policies = CancellationPolicy.objects.all()
        serializer = CancellationPolicySerializer(policies, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CancellationPolicySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

    def patch(self, request):
        policy_id = request.data.get("id")
        if not policy_id:
            return Response({"detail": "Policy ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            policy = CancellationPolicy.objects.get(id=policy_id)
        except CancellationPolicy.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CancellationPolicySerializer(policy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
