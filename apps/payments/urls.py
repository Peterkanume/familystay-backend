from django.urls import path
from .views import (
    InitiatePaymentView, MpesaCallbackView, MpesaStatusView,
    PaymentHistoryView, PaymentDetailView, RequestPayoutView,
    PayoutHistoryView
)

urlpatterns = [
    # Payment endpoints
    path('initiate/', InitiatePaymentView.as_view(), name='initiate_payment'),
    path('mpesa/callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
    path('mpesa/status/<str:transaction_id>/', MpesaStatusView.as_view(), name='mpesa_status'),
    path('history/', PaymentHistoryView.as_view(), name='payment_history'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    
    # Payout endpoints
    path('payouts/request/', RequestPayoutView.as_view(), name='request_payout'),
    path('payouts/history/', PayoutHistoryView.as_view(), name='payout_history'),
]
