from django.urls import path,include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
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
    path("rides/<int:ride_id>/cancel/", CancelRideView.as_view()),
    
    #Location
    path('location/update/', DriverLocationUpdate.as_view()),
    path('location/<int:driver_id>/', GetDriverLocation.as_view()),
    
    #Add vechical
    path('', include(router.urls)),
    
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
    path('refund-requests/', RefundRequestListView.as_view(), name='refund-request-list'),
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
    #settings
    path("settings/", IntegrationSettingsView.as_view()),
    #driver incentive
    path("driver-incentive/", DriverIncentiveView.as_view()),
    path("driver-incentive/<int:driver_id>/", DriverIncentiveView.as_view()),
    path("incentives/<int:pk>/", DriverIncentiveView.as_view()),
    # Mobile
    path('userLogin',UserLoginView.as_view()),
    path('userRegister',UserRegisterView.as_view()),
    path('driver/register',DriverRegisterView.as_view()),
    path('driver/login',DriverLoginView.as_view())
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)