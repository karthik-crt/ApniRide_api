from django.db.models import Sum
from rest_framework import generics, permissions, response
from .models import AdminWalletTransaction
from .serializers import AdminWalletTransactionSerializer


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
