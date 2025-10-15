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


from decimal import Decimal
from django.conf import settings
import razorpay

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def withdraw_to_driver(driver_wallet, amount, beneficiary_name, account_number, ifsc):
    """
    Withdraw money from driver's wallet to their bank account using Razorpay Payouts.

    Args:
        driver_wallet: Wallet object (must have 'balance' field)
        amount: Decimal, withdrawal amount in INR
        beneficiary_name: str, driver's bank account name
        account_number: str, driver's bank account number
        ifsc: str, bank IFSC code

    Returns:
        dict: { 'success': bool, 'balance': Decimal, 'payout_id': str, 'error': str }
    """

    # 1. Validate amount
    if amount <= 0:
        return {"success": False, "error": "Amount must be greater than zero"}

    # 2. Check wallet balance
    if driver_wallet.balance < amount:
        return {"success": False, "error": "Insufficient wallet balance"}

    try:
        # Convert INR to paise
        payout_amount = int(amount * 100)

        # 3. Call Razorpay Payouts API
        payout = razorpay_client.payouts.create({
            "account_number": settings.RAZORPAY_ACCOUNT_NUMBER,  # your Razorpay account
            "fund_account": {
                "account_type": "bank_account",
                "bank_account": {
                    "name": beneficiary_name,
                    "ifsc": ifsc,
                    "account_number": account_number
                }
            },
            "amount": payout_amount,
            "currency": "INR",
            "mode": "IMPS",
            "purpose": "payout"
        })

        # 4. Deduct wallet balance after successful payout
        driver_wallet.balance -= Decimal(amount)
        driver_wallet.save()

        # 5. Optionally, create a wallet transaction record here
        # WalletTransaction.objects.create(
        #     wallet=driver_wallet,
        #     amount=amount,
        #     transaction_type='withdraw',
        #     description=f"Payout ID: {payout.get('id')}"
        # )

        return {"success": True, "balance": driver_wallet.balance, "payout_id": payout.get("id")}

    except Exception as e:
        return {"success": False, "error": str(e)}
