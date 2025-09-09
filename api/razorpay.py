from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import razorpay
import json

# Razorpay client initialization
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def home(request):
    return render(request, "index.html", {"key_id": settings.RAZORPAY_KEY_ID})

def create_order(request):
    if request.method == "POST":
        # Create an order with Razorpay
        amount = 500  # Amount in paise (e.g., ₹500)
        currency = "INR"

        order_data = {
            "amount": amount,
            "currency": currency
        }
        razorpay_order = razorpay_client.order.create(data=order_data)
        return JsonResponse({"order_id": razorpay_order["id"], "amount": amount})
    return HttpResponse("Method not allowed", status=405)

def payment_success(request):
    return render(request, "success.html")

def verify_signature(request):
    if request.method == "POST":
        # Data from Razorpay Checkout
        payment_id = request.POST.get("razorpay_payment_id")
        order_id = request.POST.get("razorpay_order_id")
        signature = request.POST.get("razorpay_signature")

        # Verify signature
        try:
            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            })
            return redirect("payment_success")
        except razorpay.errors.SignatureVerificationError:
            return HttpResponse("Signature verification failed", status=400)
    return HttpResponse("Method not allowed", status=405)