from django.urls import path,include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
from .driver_earning import *
from .driver_rating import *
from .users import *
from .refund import *
from .book import BookRideView
from .revenue import *
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'vehicle-types', VehicleTypeViewSet, basename='vehicle-type')
urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('otp/send/', SendOTPView.as_view()),
    path('otp/verify/', VerifyOTPView.as_view()),

    path('rides/book/', BookRideView.as_view()),
    path('rides/history/', RideHistoryView.as_view()),
    path('rides/available/', AvailableRidesView.as_view()),
    path('rides/accept/<int:ride_id>/', AcceptRideView.as_view()),
    path('rides/<int:ride_id>/status/', RideStatusUpdateView.as_view()),
    path('rides/reject/<int:ride_id>/', RejectRideView.as_view()),
    path('rides/feedback/<int:ride_id>/', SubmitRideFeedbackView.as_view()),
    path("rides/<int:ride_id>/arrived/", RideReachedPickupView.as_view()),
    path("ride/<int:ride_id>/ongoing/",StartRide.as_view()),
    path("rides/<int:ride_id>/cancel/", CancelRideView.as_view()),
    
    path("booking/status/<str:booking_id>", BookingStatusAPIView.as_view()),
    # Driver
    path('driver/<int:pk>/online-status/', DriverOnlineStatusUpdateView.as_view()),
    path('fcm/token',UpdateFCMToken.as_view()),
    path("rides/<int:ride_id>/rate/", SubmitRatingView.as_view(), name="submit_rating"),
    path("driver/ratings/summary/", DriverRatingSummaryView.as_view(), name="driver_rating_summary"),
    path('driver/dashboard/', DriverDashboardAPIView.as_view(), name='driver-dashboard'),
    # History
    path('admin/booking-history/', AdminBookingHistoryView.as_view(), name='admin-booking-history'),
    path('user/booking-history/', UserBookingHistoryView.as_view(), name='user-booking-history'),
    path('driver/ride-history/', DriverRideHistoryView.as_view(), name='driver-ride-history'),
    path('profile/', UserProfilePatchView.as_view()),
    #Location
    path('location/update/', DriverLocationUpdate.as_view()),
    path('location/<int:driver_id>/', GetDriverLocation.as_view()),
    
    #Add vechical
    path('', include(router.urls)),
    path('user/vehicle-types/', UserVehicleTypeView.as_view()),
    path('driver/vehicle-type/',driverVehicleType.as_view()),
    # Payments
    path('payments/initiate/<int:ride_id>/', CreatePaymentView.as_view()),
    path('payments/confirm/', ConfirmPaymentView.as_view()),
    
    path('users/', AdminUserListView.as_view()),
    path('users/<int:id>', AdminUserEditView.as_view()),
    path('users/<int:id>/delete', AdminUserDeleteView.as_view()),
    path('drivers/approve/<int:driver_id>/', AdminDriverApprovalView.as_view()),
    # changed
    path('admin/drivers/<int:driver_id>/approve/', AdminDriverApprovalView.as_view()),
    # 
    path('rides', AdminRideListView.as_view()),
    path('payments/', AdminPaymentListView.as_view()),
    path('payments', PaymentListView.as_view(), name='payment-list'),
    path('payments/<int:payment_id>/adjust/', AdjustFareView.as_view(), name='adjust-fare'),
    path('refund-payment', PaymentRefundView.as_view()),
    path('refund-requests/<int:refund_id>/issue/', IssueRefundView.as_view(), name='issue-refund'),
    path('drivers/location/<int:driver_id>/', AdminDriverLocationView.as_view()),
    path('notifications/send/', AdminSendNotificationView.as_view()),
    
    # Fare Rules manually
    path('fare-rules/', FareRuleListView.as_view()),              
    path('fare-rules/<int:pk>/', FareRuleDetailView.as_view()),   

    #distance reward
    path('distance-rewards/', DistanceRewardAPIView.as_view()),
    path('distance-rewards/<int:pk>/', DistanceRewardAPIView.as_view()),
    #User offer
    path('tourism-offers/', TourismOfferAPIView.as_view()),
    path('tourism-offers/<int:pk>/', TourismOfferAPIView.as_view()),
    
    #Dashboard
    path('adminDashboard',AdminDashboardView.as_view()),
    path('earnings/<int:driver_id>', DriverEarningsAPIView.as_view()),
    #settings
    path("settings/", IntegrationSettingsView.as_view()),
    #driver incentive
    path("driver-incentive/", DriverIncentiveView.as_view()),
    path("driver-incentive/<int:driver_id>/", DriverIncentiveView.as_view()),
    path("incentives/<int:pk>/", DriverIncentiveView.as_view()),
    path('driver/incentive-progress/', DriverIncentiveProgressView.as_view(), name='driver-incentive-progress'),
    # Mobile
    path('userLogin',UserLoginView.as_view()),
    path('userRegister',UserRegisterView.as_view()),
    path('driver/register',DriverRegisterView.as_view()),
    path('driver/login',DriverLoginView.as_view()),
    path('invoice/<int:ride_id>/', RideInvoiceAPIView.as_view(), name='ride-invoice'),
    path('invoice/history/', RideHistoryAPIView.as_view(), name='ride-history'),
    #block user
    path("suspend/<int:pk>/", SuspendUserAPIView.as_view(), name="suspend_user"),
    path("block/<int:pk>/", BlockUserAPIView.as_view(), name="block_user"),
    path("activate/<int:pk>/", ActivateUserAPIView.as_view(), name="activate_user"),
    #wallet
    path("wallet/", DriverWalletDetailView.as_view(), name="wallet-detail"),
    path("wallet/deposit/", WalletDepositView.as_view(), name="wallet-deposit"),
    path("wallet/withdraw/", WalletWithdrawView.as_view(), name="wallet-withdraw"),
    path('driver/wallet/transactions/', DriverWalletTransactionHistoryView.as_view()),
    path('admin/transactions/', AdminWalletTransactionListAPI.as_view(), name='admin_transactions_api'),
    path('user/wallet/transactions/', PaymentHistoryView.as_view(), name='user_wallet_transactions_api'),
    path('cancellation-policies/', CancellationPolicyListCreate.as_view(), name='cancellation-policies-list'),
    # Logout
    path('logout', LogoutView.as_view()),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)