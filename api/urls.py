from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
from django.conf import settings
from django.conf.urls.static import static
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

    path('location/update/', DriverLocationUpdate.as_view()),
    path('location/<int:driver_id>/', GetDriverLocation.as_view()),

    path('payments/initiate/<int:ride_id>/', CreatePaymentView.as_view()),
    path('payments/confirm/', ConfirmPaymentView.as_view()),
    
    path('users/', AdminUserListView.as_view()),
    path('users/<int:id>', AdminUserEditView.as_view()),
    path('users/<int:id>/delete', AdminUserDeleteView.as_view()),
    path('drivers/approve/<int:driver_id>/', AdminDriverApprovalView.as_view()),
    # changed
    path('admin/drivers/<int:driver_id>/approve/', AdminDriverApprovalView.as_view()),
    # 
    path('rides/', AdminRideListView.as_view()),
    path('payments/', AdminPaymentListView.as_view()),
    path('drivers/location/<int:driver_id>/', AdminDriverLocationView.as_view()),
    path('notifications/send/', AdminSendNotificationView.as_view()),
    
    # Mobile
    path('userLogin',UserLoginView.as_view()),
    path('userRegister',UserRegisterView.as_view()),
    path('driver/register',DriverRegisterView.as_view()),
    path('driver/login',DriverLoginView.as_view())
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)