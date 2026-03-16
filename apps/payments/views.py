from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
import uuid
import logging

from .models import Payment, Payout, TransactionLog
from .serializers import (
    PaymentSerializer, PaymentInitiateSerializer, PaymentVerifySerializer,
    PayoutSerializer, PayoutRequestSerializer, TransactionLogSerializer
)
from apps.accounts.permissions import IsHost, IsAdmin
from apps.bookings.models import Booking

logger = logging.getLogger(__name__)


class InitiatePaymentView(APIView):
    """Initiate payment for a booking"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        booking_id = serializer.validated_data['booking_id']
        payment_method = serializer.validated_data['payment_method']
        phone_number = serializer.validated_data['phone_number']
        
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Generate transaction ID
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # Create payment record
        payment = Payment.objects.create(
            booking=booking,
            payer=request.user,
            recipient=booking.listing.host,
            transaction_id=transaction_id,
            payment_method=payment_method,
            amount=booking.total_amount,
            currency='KES',
            status='INITIATED',
            description=f"Payment for booking {booking.booking_reference}"
        )
        
        # For M-Pesa, initiate STK push
        if payment_method == 'MPESA':
            try:
                # Simulate M-Pesa STK push
                # In production, integrate with Safaricom API
                provider_reference = f"MPE-{uuid.uuid4().hex[:10].upper()}"
                payment.provider_reference = provider_reference
                payment.provider_response = {
                    'phone_number': phone_number,
                    'status': 'pending',
                    'message': 'STK push sent'
                }
                payment.save()
                
                # Log transaction
                TransactionLog.objects.create(
                    transaction_type='PAYMENT_INITIATED',
                    transaction_id=transaction_id,
                    user=request.user,
                    amount=booking.total_amount,
                    status='INITIATED',
                    request_data={
                        'booking_id': booking_id,
                        'payment_method': payment_method,
                        'phone_number': phone_number
                    },
                    response_data=payment.provider_response
                )
                
                return Response({
                    'message': 'Payment initiated. Please check your phone for M-Pesa prompt.',
                    'transaction_id': transaction_id,
                    'provider_reference': provider_reference,
                    'amount': float(booking.total_amount)
                })
                
            except Exception as e:
                logger.error(f"M-Pesa error: {str(e)}")
                payment.status = 'FAILED'
                payment.error_message = str(e)
                payment.save()
                return Response({
                    'error': 'Payment initiation failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # For other payment methods (Card, PayPal, Bank)
        return Response({
            'message': 'Payment initiated',
            'transaction_id': transaction_id,
            'amount': float(booking.total_amount),
            'payment_url': f'/checkout/{transaction_id}'  # Placeholder
        })


class MpesaCallbackView(APIView):
    """Handle M-Pesa callback"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # In production, validate M-Pesa signature
        callback_data = request.data
        
        try:
            result_code = callback_data.get('ResultCode')
            result_desc = callback_data.get('ResultDesc')
            transaction_id = callback_data.get('TransID')
            amount = callback_data.get('TransAmount')
            phone = callback_data.get('MSISDN')
            
            # Find payment by provider reference
            payment = Payment.objects.filter(provider_reference=transaction_id).first()
            
            if not payment:
                logger.error(f"Payment not found for transaction: {transaction_id}")
                return Response({'status': 'failed'})
            
            if result_code == 0:
                # Success
                with transaction.atomic():
                    payment.status = 'COMPLETED'
                    payment.completed_at = timezone.now()
                    payment.provider_response = callback_data
                    payment.save()
                    
                    # Update booking
                    booking = payment.booking
                    booking.payment_status = 'PAID'
                    booking.booking_status = 'CONFIRMED'
                    booking.save()
                    
                    # Log success
                    TransactionLog.objects.create(
                        transaction_type='PAYMENT_COMPLETED',
                        transaction_id=payment.transaction_id,
                        user=payment.payer,
                        amount=payment.amount,
                        status='COMPLETED',
                        response_data=callback_data
                    )
            else:
                # Failed
                payment.status = 'FAILED'
                payment.error_message = result_desc
                payment.provider_response = callback_data
                payment.save()
                
                TransactionLog.objects.create(
                    transaction_type='PAYMENT_FAILED',
                    transaction_id=payment.transaction_id,
                    user=payment.payer,
                    amount=payment.amount,
                    status='FAILED',
                    response_data=callback_data
                )
            
            return Response({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Callback error: {str(e)}")
            return Response({'status': 'error'})


class MpesaStatusView(APIView):
    """Check M-Pesa payment status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, transaction_id):
        payment = get_object_or_404(Payment, transaction_id=transaction_id, payer=request.user)
        
        return Response({
            'transaction_id': payment.transaction_id,
            'status': payment.status,
            'amount': float(payment.amount),
            'provider_reference': payment.provider_reference,
            'created_at': payment.created_at
        })


class PaymentHistoryView(generics.ListAPIView):
    """Get user's payment history"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(
            models.Q(payer=self.request.user) | models.Q(recipient=self.request.user)
        ).select_related('booking', 'payer', 'recipient')


class PaymentDetailView(generics.RetrieveAPIView):
    """Get payment details"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Payment.objects.filter(
            models.Q(payer=user) | models.Q(recipient=user)
        )


class RequestPayoutView(APIView):
    """Request payout from earnings"""
    permission_classes = [IsHost]
    
    def post(self, request):
        serializer = PayoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check host has sufficient balance (placeholder)
        # In production, calculate from completed bookings
        
        # Create payout request
        payout = Payout.objects.create(
            host=request.user,
            amount=serializer.validated_data['amount'],
            currency='KES',
            payout_method=serializer.validated_data['payout_method'],
            account_details={
                'phone_number': serializer.validated_data.get('phone_number'),
                'bank_name': serializer.validated_data.get('bank_name'),
                'account_number': serializer.validated_data.get('account_number'),
                'account_name': serializer.validated_data.get('account_name'),
                'paypal_email': serializer.validated_data.get('paypal_email')
            },
            reference=f"PO-{uuid.uuid4().hex[:10].upper()}"
        )
        
        return Response({
            'message': 'Payout requested successfully',
            'payout': PayoutSerializer(payout).data
        })


class PayoutHistoryView(generics.ListAPIView):
    """Get host's payout history"""
    serializer_class = PayoutSerializer
    permission_classes = [IsHost]
    
    def get_queryset(self):
        return Payout.objects.filter(host=self.request.user)


# Import Q for complex queries
from django.db import models
