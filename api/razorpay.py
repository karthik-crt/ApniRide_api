from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import razorpay,requests
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


# from decimal import Decimal
# from django.conf import settings
# import razorpay
# from .models import DriverWallet, UserWalletTransaction
# from django.db import transaction
# # Initialize Razorpay client
# razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# def withdraw_to_driver(driver_wallet, amount, beneficiary_name, account_number, ifsc):
#     # 1. Validate amount
#     if amount <= 0:
#         return {"success": False, "error": "Amount must be greater than zero"}

#     # 2. Check wallet balance
#     if driver_wallet.balance < amount:
#         return {"success": False, "error": "Insufficient wallet balance"}

#     try:
#         # Convert INR to paise
#         payout_amount = int(amount * 100)

#         # 3. Call Razorpay Payouts API
#         # payout = razorpay_client.payouts.create({
#         #     "account_number": settings.RAZORPAY_ACCOUNT_NO,  # your Razorpay account
#         #     "fund_account": {
#         #         "account_type": "bank_account",
#         #         "bank_account": {
#         #             "name": beneficiary_name,
#         #             "ifsc": ifsc,
#         #             "account_number": account_number
#         #         }
#         #     },
#         #     "amount": payout_amount,
#         #     "currency": "INR",
#         #     "mode": "IMPS",
#         #     "purpose": "payout"
#         # })

#         url = "https://api.razorpay.com/v1/payouts"
#         headers = {
#             "Content-Type": "application/json"
#         }

#         data = {
#             "account_number": settings.RAZORPAY_ACCOUNT_NO,
#             "amount": payout_amount,
#             "currency": "INR",
#             "mode": "NEFT",
#             "purpose": "Withdrawal to driver",
#             "fund_account": {
#                 "account_type": "bank_account",
#                 "name": beneficiary_name,
#                 "ifsc": ifsc,
#                 "account_number": account_number,
#                 "contact": {
#                     "name": beneficiary_name,
#                     "email": driver_wallet.driver.email,
#                     "contact": driver_wallet.driver.mobile,
#                     "contact_type": "Employee",
#                     "reference_id": driver_wallet.driverwallet.id or "Driver_"+str(driver_wallet.driver.id),
#                     "notes": {
#                         "driver_id": str(driver_wallet.driver.id)
#                     }
#                 }
#             },
#             "queue_if_low_balance": True,
#             "reference_id": driver_wallet.driverwallet.id or "Driver_"+str(driver_wallet.driver.id),
#             "narration": "Acme Corp Fund Transfer",
#             "notes": {
#                 "notes_key_1": "Beam me up Scotty",
#                 "notes_key_2": "Engage"
#             }
#         }

#         response = requests.post(url, headers=headers, json=data)

#         with transaction.atomic():
#             driver_wallet.balance -= amount
#             driver_wallet.save()

#             UserWalletTransaction.objects.create(
#                 wallet=driver_wallet,
#                 amount=-amount,
#                 transaction_type='withdrawal',
#                 description=f"Payout ID: {response.json().get('id')}",
#                 balance_after=driver_wallet.balance,
#                 related_ride=None  # Set if linked to a ride
#             )

#         return {"success": True, "balance": driver_wallet.balance, "payout_id": payout.get("id")}

#     except Exception as e:
#         return {"success": False, "error": str(e)}


# E:\Cab\Cab-New\ApniRide_api\api\razorpay.py
from django.db import transaction
from decimal import Decimal
from django.conf import settings
import razorpay
import requests
from requests.auth import HTTPBasicAuth
import time
from .models import DriverWallet, UserWalletTransaction

def withdraw_to_driver(driver_wallet, amount, beneficiary_name, account_number, ifsc):
    print("driver_wallet",driver_wallet)
    print("amount",amount)
    print("beneficiary_name",beneficiary_name)
    print("account_number",account_number)
    print("ifsc",ifsc)
    
    if amount <= 0:
        return {"success": False, "error": "Amount must be greater than zero", "balance": driver_wallet.balance, "payout_id": None}

    
    if driver_wallet.balance < amount:
        return {"success": False, "error": "Insufficient wallet balance", "balance": driver_wallet.balance, "payout_id": None}

   
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        with transaction.atomic():
            
            contact_data = {
                "name": beneficiary_name,
                "email": driver_wallet.driver.email or "default@example.com",  
                "contact": driver_wallet.driver.mobile or "9999999999",  
                "type": "employee",
                "reference_id": f"Driver_{driver_wallet.driver_id}",
                "notes": {
                    "driver_id": str(driver_wallet.driver_id)
                }
            }
            contact_response = requests.post(
                "https://api.razorpay.com/v1/contacts",
                json=contact_data,
                headers={"Content-Type": "application/json"},
                auth=HTTPBasicAuth(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            print("Contact response status:", contact_response.json())
            if contact_response.status_code not in (200, 201):  # Accept 200 or 201 as success
                error_response = contact_response.json()
                return {
                    "success": False,
                    "error": f"Failed to create contact: {error_response.get('error', {}).get('description', 'Unknown error')}",
                    "balance": driver_wallet.balance,
                    "payout_id": None
                }
            contact_id = contact_response.json()["id"]

            # Step 2: Create fund account
            fund_account_data = {
                "contact_id": contact_id,
                "account_type": "bank_account",
                "bank_account": {
                    "name": beneficiary_name,
                    "account_number": account_number,
                    "ifsc": ifsc
                }
            }
            fund_account = razorpay_client.fund_account.create(data=fund_account_data)
            fund_account_id = fund_account["id"]

            # Step 3: Create payout
            payout_amount = int(amount * 100)  # Convert to paise
            url = "https://api.razorpay.com/v1/payouts"
            headers = {"Content-Type": "application/json"}
            auth = HTTPBasicAuth(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            payout_data = {
                "account_number": settings.RAZORPAY_ACCOUNT_NO,  # Your Razorpay-linked account
                "fund_account_id": fund_account_id,
                "amount": payout_amount,
                "currency": "INR",
                "mode": "IMPS",  # Use IMPS for faster testing
                "purpose": "payout",
                "queue_if_low_balance": True,
                "reference_id": f"Withdraw_{driver_wallet.id}_{int(time.time())}",
                "narration": "ApniRide Withdrawal",
                "notes": {
                    "driver_id": str(driver_wallet.driver_id),
                    "wallet_id": str(driver_wallet.id)
                }
            }

            response = requests.post(url, json=payout_data, headers=headers, auth=auth)
            print("Payout response status:", response.json())
            if response.status_code == 200:
                payout_result = response.json()
                return {
                    "success": True,
                    "balance": driver_wallet.balance,
                    "payout_id": payout_result["id"],
                    "error": None
                }
            else:
                error_response = response.json()
                return {
                    "success": False,
                    "error": f"Payout failed: {error_response.get('error', {}).get('description', 'Unknown error')}",
                    "balance": driver_wallet.balance,
                    "payout_id": None
                }

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Network error: {str(e)}", "balance": driver_wallet.balance, "payout_id": None}
    except Exception as e:
        return {"success": False, "error": f"Withdrawal failed: {str(e)}", "balance": driver_wallet.balance, "payout_id": None}