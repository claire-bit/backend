# orders/views.py
import requests
from datetime import datetime
from base64 import b64encode

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from products.models import Product
from users.models import CustomUser
from orders.models import Order
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.http import JsonResponse




def get_mpesa_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
    r.raise_for_status()
    return r.json().get("access_token")


def initiate_stk_push(phone, amount):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password_str = settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp
    password = b64encode(password_str.encode()).decode()

    access_token = get_mpesa_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": "GlobalConnect",
        "TransactionDesc": "Product purchase"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        headers=headers,
        json=payload
    )

    return response.json()


@api_view(["POST"])
def checkout(request):
    product_id = request.data.get("product")
    amount = request.data.get("amount")
    phone = request.data.get("phone")
    affiliate_id = request.data.get("affiliate")

    if not all([product_id, amount, phone]):
        return Response({"error": "Missing required fields."}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)

    buyer = request.user if request.user.is_authenticated else None
    affiliate = CustomUser.objects.filter(id=affiliate_id).first() if affiliate_id else None

    # Save the order before initiating payment
    order = Order.objects.create(
        product=product,
        amount=amount,
        buyer=buyer,
        affiliate=affiliate,
        status="pending"
    )

    try:
        stk_response = initiate_stk_push(phone, amount)

        if stk_response.get("ResponseCode") != "0":
            order.status = "failed"
            order.save()
            return Response({
                "error": "STK Push failed.",
                "details": stk_response
            }, status=400)

        # ✅ Save M-Pesa STK identifiers
        order.checkout_request_id = stk_response.get("CheckoutRequestID")
        order.merchant_request_id = stk_response.get("MerchantRequestID")
        order.save()

        return Response({
            "message": stk_response.get("CustomerMessage", "STK push sent."),
            "order_id": order.id,
            "merchant_request_id": stk_response.get("MerchantRequestID"),
            "checkout_request_id": stk_response.get("CheckoutRequestID")
        }, status=200)

    except Exception as e:
        order.status = "failed"
        order.save()
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
@permission_classes([AllowAny])  # Or use IsAuthenticated if login is required
def check_payment_status(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return Response({
            "order_id": order.id,
            "status": order.status,
        })
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=404)
    
@csrf_exempt
@api_view(['POST'])
def mpesa_callback(request):
    """
    Handles M-Pesa payment confirmation from Safaricom
    """
    data = request.data

    try:
        body = data.get("Body", {})
        stk_callback = body.get("stkCallback", {})

        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")

        # Attempt to find the order using CheckoutRequestID
        order = Order.objects.filter(checkout_request_id=checkout_request_id).first()

        if not order:
            return JsonResponse({"error": "Order not found"}, status=404)

        if result_code == 0:
            order.status = "paid"
        else:
            order.status = "failed"

        order.save()

        return JsonResponse({"message": "Callback processed"}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)    