from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import random
from django.core.cache import cache  # Using Django cache to store OTP temporarily
import time
from mailosaur import MailosaurClient
from mailosaur.models import MessageCreateOptions
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Mailosaur configuration (replace with your actual values)
MAILOSAUR_API_KEY = "1tbQ8H9UnpXIBMxEU7ZecLOUDYV5aAL5"
MAILOSAUR_SERVER_ID = "7p45d6wj"

# Initialize Mailosaur client
mailosaur = MailosaurClient(MAILOSAUR_API_KEY)

def send_otp_via_mailosaur(email, otp):
    try:
        recipient = email  # Use the user's email from the request
        subject = "Your OTP Code"
        body = f"<p>Your OTP is {otp}. It is valid for 10 minutes.</p>"
        options = MessageCreateOptions(
            recipient,
            True,  # HTML email
            subject,
            html=body
        )

        # Send the email using Mailosaur
        mailosaur.messages.create(MAILOSAUR_SERVER_ID, options)
        logger.info(f"OTP {otp} sent to {email} via Mailosaur")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP via Mailosaur: {str(e)}")
        return False

# Create your views here.

def home(request):
    return render(request, 'home.html')

def first(request):
    return render(request, 'main.html')

def result(request):
    return render(request,'results.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Successfully logged in!')
                return redirect('first')  # Redirect to home after successful login
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return render(request, 'login.html', {'mode': 'l'})

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not all([username, email, password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'login.html', {'mode': 's'})
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'login.html', {'mode': 's'})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'login.html', {'mode': 's'})
        
        # Generate and send OTP
        otp = str(random.randint(100000, 999999))  # 6-digit OTP
        request.session['otp'] = otp  # Store OTP in session
        request.session['username'] = username  # Store username in session
        request.session['email'] = email  # Store email in session
        request.session['password'] = password  # Store password in session
        request.session['attempts'] = 0  # Initialize failed attempts
        request.session['timestamp'] = time.time()  # Store time for timer reference

        # Use Mailosaur to send OTP
        try:
            if send_otp_via_mailosaur(email, otp):
                messages.success(request, 'OTP sent to your email. Please verify.')
                return redirect('otp')
            else:
                messages.error(request, 'Failed to send OTP. Please try again.')
                return render(request, 'login.html', {'mode': 's'})
        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            messages.error(request, f'An error occurred while sending OTP: {str(e)}')
            return render(request, 'login.html', {'mode': 's'})
    
    return render(request, 'login.html', {'mode': 's'})

def otp_view(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        attempts = request.session.get('attempts', 0) + 1

        if not stored_otp:
            messages.error(request, 'No OTP found. Please register again.')
            return redirect('register')

        if entered_otp == stored_otp:
            # OTP verified successfully
            username = request.session.get('username')
            email = request.session.get('email')
            password = request.session.get('password')

            # Create user
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                # Clear all session data
                for key in list(request.session.keys()):
                    del request.session[key]
                messages.success(request, 'Account created and verified successfully! Please log in.')
                return redirect('login_user')
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                messages.error(request, f'An error occurred while saving user data: {str(e)}')
                return redirect('register')
        else:
            request.session['attempts'] = attempts
            if attempts >= 3:
                # Clear session data and redirect to register page
                for key in list(request.session.keys()):
                    del request.session[key]
                messages.error(request, 'Too many incorrect attempts. Please register again.')
                return redirect('register')
            else:
                messages.error(request, f'Invalid OTP. {3 - attempts} attempts remaining.')
                return render(request, 'otp.html', {'attempts_left': 3 - attempts})

    attempts_left = 3 - request.session.get('attempts', 0)
    if attempts_left < 0:  # Safety check
        attempts_left = 0
    return render(request, 'otp.html', {'attempts_left': attempts_left})

def logout_user(request):
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('home')


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Transaction  # Reuse or create a new model for expenses

@csrf_exempt
def add_expense(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            category = request.POST.get('category')
            amount = float(request.POST.get('amount'))
            date = request.POST.get('date')

            transaction = Transaction(
                user=request.user,
                date=date,
                amount=amount,
                description=f"Expense: {category}",
                transaction_id=f"expense_{date}_{category}"  
            )
            transaction.save()

            return JsonResponse({'status': 'success', 'message': 'Expense added successfully'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'User not authenticated or invalid request'}, status=401)

import requests
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def exchange_paytm_token(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            auth_code = data.get('authCode')

            token_url = 'https://accounts.paytm.com/oauth2/token'
            payload = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'client_id': 'YOUR_CLIENT_ID',
                'client_secret': 'YOUR_CLIENT_SECRET',
                'redirect_uri': 'YOUR_REDIRECT_URI',
                'login_type': 'mobile'  # Specify mobile login
            }

            token_response = requests.post(token_url, data=payload).json()

            access_token = token_response.get('access_token')

            return JsonResponse({'status': 'success', 'accessToken': access_token})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def send_paytm_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mobile = data.get('mobile')

            # Hypothetical Paytm API call to send OTP
            otp_url = 'https://api.paytm.com/otp/send'
            payload = {
                'mobile': mobile,
                'client_id': 'YOUR_CLIENT_ID'
            }

            response = requests.post(otp_url, data=payload).json()

            return JsonResponse({'status': 'success', 'message': 'OTP sent'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
import json
import pdfplumber
import re
from datetime import datetime
from .models import Transaction  # Ensure this model exists in models.py

@csrf_exempt
def upload_transactions(request):
    if request.method == 'POST' and request.FILES.get('transaction_pdf') and request.user.is_authenticated:
        try:
            pdf_file = request.FILES['transaction_pdf']
            transactions = []

            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    pattern = r'Date:\s*(\d{1,2}/\d{1,2}/\d{4})\s*Amount:\s*(\d*\.?\d+)\s*Description:\s*(.*?)(?=\s*Date:|\Z)'
                    matches = re.finditer(pattern, text, re.DOTALL)

                    for match in matches:
                        date_str, amount_str, description = match.groups()
                        try:
                            date = datetime.strptime(date_str, '%m/%d/%Y').date()
                            amount = float(amount_str)
                            transaction_id = f"{date}-{amount}-{description[:10]}".replace(" ", "_")

                            if not Transaction.objects.filter(transaction_id=transaction_id, user=request.user).exists():
                                transaction = Transaction(
                                    user=request.user,
                                    date=date,
                                    amount=amount,
                                    description=description.strip(),
                                    transaction_id=transaction_id
                                )
                                transaction.save()
                                transactions.append({
                                    'date': date.isoformat(),
                                    'amount': amount,
                                    'description': description.strip()
                                })

                        except ValueError as e:
                            continue

            return JsonResponse({
                'status': 'success',
                'data': transactions,
                'message': f'Successfully processed {len(transactions)} new transactions'
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'No PDF file uploaded or user not authenticated'}, status=400)

# Other views (recent_transactions, send_paytm_otp, verify_paytm_otp) remain unchanged...

# View to fetch 10 most recent transactions
@csrf_exempt
def recent_transactions(request):
    if request.method == 'GET' and request.user.is_authenticated:
        try:
            transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:10]
            transaction_list = [{
                'date': t.date.isoformat(),
                'amount': float(t.amount),
                'description': t.description
            } for t in transactions]

            return JsonResponse({
                'status': 'success',
                'transactions': transaction_list
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

# View to send Paytm OTP
@csrf_exempt
def send_paytm_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mobile = data.get('mobile')

            # Hypothetical Paytm API call to send OTP
            otp_url = 'https://api.paytm.com/otp/send'  # Replace with actual endpoint from Paytm docs
            payload = {
                'mobile': mobile,
                'client_id': 'YOUR_CLIENT_ID'  # Replace with actual Client ID from Paytm
            }

            response = requests.post(otp_url, data=payload).json()

            return JsonResponse({'status': 'success', 'message': 'OTP sent'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

# View to verify Paytm OTP
@csrf_exempt
def verify_paytm_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mobile = data.get('mobile')
            otp = data.get('otp')

            # Hypothetical Paytm API call to verify OTP
            verify_url = 'https://api.paytm.com/otp/verify'  # Replace with actual endpoint from Paytm docs
            payload = {
                'mobile': mobile,
                'otp': otp,
                'client_id': 'YOUR_CLIENT_ID'  # Replace with actual Client ID from Paytm
            }

            response = requests.post(verify_url, data=payload).json()

            access_token = response.get('access_token')

            return JsonResponse({'status': 'success', 'accessToken': access_token})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)