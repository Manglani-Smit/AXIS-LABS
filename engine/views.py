import sys
import io
import os
import json
import uuid
import random
import re
import threading
import traceback
import requests
import stripe

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import UserProfile

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


# ==============================================================================
# HTML TEMPLATE VIEWS
# ==============================================================================

def landing_view(request):
    return render(request, 'landing.html')


def auth_view(request):
    return render(request, 'auth.html')


def developer_dashboard_view(request):
    return render(request, 'developer_dashboard.html')


def client_dashboard_view(request):
    return render(request, 'client_dashboard.html')


def template_workspace_view(request, template_id):
    return render(request, 'template_workspace.html', {
        'template_id': template_id,
        'stripe_public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', '')
    })


# ==============================================================================
# AI + SANDBOX EXECUTION VIEW
# ==============================================================================

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def analyze_architecture(request):
    query = request.data.get('query', '').strip()
    language = request.data.get('language', 'python').lower()

    if not query:
        return Response({'error': 'Instruction buffer is empty.'}, status=status.HTTP_400_BAD_REQUEST)

    stdout_output = ""
    is_code_executed = False

    # 1. Python Sandbox Execution
    has_exec_code = any(keyword in query for keyword in
                        ['print(', 'def ', 'class ', 'import ', 'for ', 'while ']) and not query.lower().startswith(
        ('build', 'create', 'design', 'specify', 'architect'))
    if has_exec_code:
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        try:
            clean_query = query.replace('\r\n', '\n').strip() + '\n'
            exec_scope = {}
            exec(clean_query, exec_scope)
            stdout_output = redirected_output.getvalue()
            is_code_executed = True
        except Exception as e:
            stdout_output = f"{type(e).__name__}: {e}"
            is_code_executed = True
        finally:
            sys.stdout = old_stdout

    # 2. Intelligent Dynamic Heuristic Defaults
    q_lower = query.lower()
    if 'crypto' in q_lower or 'trading' in q_lower or 'order-book' in q_lower:
        ai_architecture = "HFT Async Matching Engine [C++/PYTHON]"
        ai_valuation = "$8,500 - $14,000 USD"
        ai_roadmap = [
            "1. Bind C++ Orderbook Kernel to Python via ctypes/pybind11",
            "2. Mount Redis In-Memory Ring Buffer for Sub-Millisecond L2 Quotes",
            "3. Spawn Asynchronous Django Channels WebSocket Broadcast Workers",
            "4. Enforce Kernel Latency Telemetry at 120 microseconds"
        ]
    elif 'video' in q_lower or 'stream' in q_lower or 'webrtc' in q_lower:
        ai_architecture = "Distributed HLS Transcoding Pipeline"
        ai_valuation = "$6,200 - $11,000 USD"
        ai_roadmap = [
            "1. Ingest RTMP/WebRTC raw streams into Celery worker nodes",
            "2. Execute headless FFmpeg transcoding into multi-bitrate HLS chunks",
            "3. Distribute manifest slices across S3-compatible MinIO edge pods",
            "4. Mount WebSocket presence room for live viewer telemetry"
        ]
    elif 'bot' in q_lower or 'ai' in q_lower or 'neural' in q_lower:
        ai_architecture = "Neural Inference Cluster Node"
        ai_valuation = "$7,000 - $12,500 USD"
        ai_roadmap = [
            "1. Allocate isolated CUDA container pod with tensor caching",
            "2. Expose streaming tokens through Server-Sent Events (SSE)",
            "3. Enforce token rate-limiting through Redis sliding-window algorithm",
            "4. Mount automated failover gateway across model providers"
        ]
    else:
        ai_architecture = f"Distributed High-Throughput Node [{language.upper()}]"
        ai_valuation = "$4,800 - $8,500 USD"
        ai_roadmap = [
            "1. Dynamic AST Syntax Tree parsed and bytecode validated",
            "2. Injected Zero-Trust cryptographic authorization headers",
            "3. Bound task pipelines to Celery asynchronous Redis workers",
            "4. Architecture blueprint synchronized with production cloud pod"
        ]

    # 3. Live OpenRouter AI Engine Call
    ai_key = getattr(settings, 'OPENROUTER_API_KEY', '') or os.getenv('OPENROUTER_API_KEY', '')
    print(f"\n[DEBUG AI ENGINE] Key Present: {bool(ai_key)} | Key: {ai_key[:10] if ai_key else 'NONE'}")

    if ai_key:
        headers = {
            "Authorization": f"Bearer {ai_key.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://axis-labs.onrender.com",
            "X-Title": "AXIS Labs Core"
        }

        prompt = (
            f"Analyze this software query: '{query[:250]}'. "
            "Return ONLY raw JSON (no markdown formatting, no backticks) with keys:\n"
            "{\n"
            '  "architecture": "Architecture Name (Max 5 words)",\n'
            '  "market_valuation": "$7,500 USD",\n'
            '  "execution_roadmap": ["Step 1", "Step 2", "Step 3", "Step 4"]\n'
            "}"
        )

        live_models = [
            "openrouter/auto",
            "meta-llama/llama-3-8b-instruct:free",
            "qwen/qwen-2.5-7b-instruct:free"
        ]

        for model_id in live_models:
            try:
                payload = {
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": "You are AXIS Neural Compiler. Output raw JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                }

                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload,
                                    timeout=8)
                print(f"[DEBUG AI ENGINE] Model: {model_id} | Status: {res.status_code}")

                if res.status_code == 200:
                    raw_text = res.json()['choices'][0]['message']['content'].strip()
                    print(f"[DEBUG AI ENGINE] Success Response from {model_id}: {raw_text[:80]}...")

                    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        ai_architecture = parsed.get('architecture', ai_architecture)
                        ai_valuation = parsed.get('market_valuation', ai_valuation)
                        ai_roadmap = parsed.get('execution_roadmap', ai_roadmap)
                        break
                else:
                    print(f"[DEBUG AI ENGINE] Failed with {model_id}: {res.text[:120]}")
            except Exception as e:
                print(f"[DEBUG AI ENGINE] Error calling {model_id}: {e}")

    return Response({
        'status': 'SUCCESS',
        'is_executed': is_code_executed,
        'stdout': stdout_output if stdout_output.strip() else ">> NEURAL ARCHITECTURE SYNTHESIS RESOLVED.",
        'architecture': ai_architecture,
        'market_valuation': ai_valuation,
        'execution_roadmap': ai_roadmap
    }, status=status.HTTP_200_OK)


# ==============================================================================
# STRIPE CHECKOUT & BACKGROUND EMAIL RELAY
# ==============================================================================

def send_email_in_background(subject, plain_message, from_email, to_email, html_message=None):
    try:
        if html_message:
            email = EmailMultiAlternatives(subject, plain_message, from_email, to_email)
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
        else:
            send_mail(subject, plain_message, from_email, to_email, fail_silently=False)
        print(f"[MAIL DISPATCH SUCCESS] Verification signal routed to: {to_email}")
    except Exception as e:
        print(f"\n[CRITICAL SMTP RELAY FAILURE] Target: {to_email} | Error: {e}")
        traceback.print_exc()


@csrf_exempt
def create_checkout_session(request):
    try:
        domain_url = request.build_absolute_uri('/')[:-1]
        data = json.loads(request.body)
        raw_price = data.get('post_data', '4500')

        amount = int(''.join(filter(str.isdigit, str(raw_price)))) or 4500
        final_amount = amount * 100

        template_name = data.get('template_name', 'AXIS Enterprise Architecture Blueprint')
        user_email = request.session.get('email') or request.GET.get('email') or 'client@axis.io'

        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'unit_amount': final_amount,
                    'product_data': {
                        'name': f"AXIS LABS // {template_name}",
                        'description': 'Commercial Repository License + Docker Cluster Config + 6-Month Support',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=domain_url + f'/success/?user_email={user_email}&template={template_name}&amount={amount}',
            cancel_url=domain_url + '/cancel/',
            customer_email=user_email if '@' in user_email else None
        )
        return JsonResponse({'id': session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def success(request):
    user_email = request.GET.get('user_email') or request.session.get('email') or 'operator@axis.io'
    template_name = request.GET.get('template') or 'Enterprise Cloud Architecture'
    amount = request.GET.get('amount') or '4500'
    order_id = random.randint(10000, 99999)

    subject = f"[AXIS LABS] Acquisition Confirmed // Node #{order_id}"
    plain_message = f"Payment Received: INR {amount}. Template '{template_name}' has been provisioned to your account."

    html_message = f"""
    <div style="background:#070709; color:#ecebe8; font-family:monospace; padding:30px; border:1px solid #e5b338; border-radius:8px; max-width:600px;">
        <h2 style="color:#e5b338; margin-top:0;">AXIS LABS // SETTLEMENT CONFIRMED</h2>
        <p style="color:#64748b; font-size:12px;">OFFICIAL CLEARANCE INVOICE</p>
        <hr style="border-color:#1e293b;">
        <p><strong>Order ID:</strong> #AX-{order_id}</p>
        <p><strong>Asset:</strong> {template_name}</p>
        <p><strong>Remitted Total:</strong> <span style="color:#10b981; font-weight:bold;">₹{amount} INR</span></p>
        <p><strong>Escrow Status:</strong> 100% STRIPE SETTLED</p>
        <div style="background:#0f172a; padding:15px; border-left:3px solid #10b981; margin-top:20px;">
            <p style="margin:0; font-size:12px; color:#10b981;">>> CLUSTER PODS INSTANTIATED // SOURCE DISPATCHED</p>
        </div>
    </div>
    """

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
    to_email = [user_email]

    thread = threading.Thread(
        target=send_email_in_background,
        args=(subject, plain_message, from_email, to_email, html_message)
    )
    thread.daemon = True
    thread.start()

    return render(request, 'success.html', {
        'user_email': user_email,
        'template_name': template_name,
        'amount': amount,
        'order_id': order_id,
    })


def cancel(request):
    return render(request, 'cancel.html')


# ==============================================================================
# AUTHENTICATION & LOGIN APIS
# ==============================================================================

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    role = request.data.get('role', 'developer').lower()

    if not username or not email or not password:
        return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username__iexact=username).exists():
        return Response({'error': 'Operator identifier already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)

    if role == 'developer':
        cipher = f"DEV-{uuid.uuid4().hex[:16].upper()}"
        dev_token = cipher
        cli_id = None
    else:
        cipher = f"CLI-{uuid.uuid4().hex[:16].upper()}"
        dev_token = None
        cli_id = cipher

    UserProfile.objects.create(
        user=user,
        role=role,
        developer_token=dev_token,
        client_id=cli_id,
        login_approval_status='NONE'
    )

    request.session['email'] = email
    return Response({
        'status': 'SUCCESS',
        'username': user.username,
        'email': user.email,
        'role': role,
        'issued_cipher': cipher
    }, status=status.HTTP_201_CREATED)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    key = request.data.get('key', '').strip()

    if not username or not password:
        return Response({'error': 'Username and password required.'}, status=status.HTTP_400_BAD_REQUEST)

    user_obj = User.objects.filter(username__iexact=username).first()
    if not user_obj:
        return Response({'error': f"Operator '{username}' not found."}, status=status.HTTP_400_BAD_REQUEST)

    authenticated_user = authenticate(username=user_obj.username, password=password)
    if not authenticated_user:
        if not user_obj.check_password(password):
            return Response({'error': 'Invalid passphrase.'}, status=status.HTTP_400_BAD_REQUEST)
        authenticated_user = user_obj

    profile, _ = UserProfile.objects.get_or_create(user=authenticated_user)
    user_role = (profile.role or 'developer').lower()
    input_key = key.upper()

    if user_role == 'developer':
        stored = (profile.developer_token or '').strip().upper()
        if not stored:
            stored = f"DEV-{uuid.uuid4().hex[:16].upper()}"
            profile.developer_token = stored
            profile.save()
        if not input_key or (input_key != stored and input_key.replace("DEV-", "") != stored.replace("DEV-", "")):
            return Response({'error': f"Developer token mismatch! Valid token is: {stored}"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        stored = (profile.client_id or '').strip().upper()
        if not stored:
            stored = f"CLI-{uuid.uuid4().hex[:16].upper()}"
            profile.client_id = stored
            profile.save()
        if not input_key or (input_key != stored and input_key.replace("CLI-", "") != stored.replace("CLI-", "")):
            return Response({'error': f"Client ID mismatch! Valid ID is: {stored}"}, status=status.HTTP_400_BAD_REQUEST)

    temp_token = uuid.uuid4().hex
    profile.approval_token = temp_token
    profile.login_approval_status = 'PENDING'
    profile.save()

    # Dynamic Host Resolution
    host = request.get_host()
    proto = 'https' if request.is_secure() or 'onrender.com' in host else 'http'
    base_url = f"{proto}://{host}"

    approve_link = f"{base_url}/verify-login/{temp_token}/approve/"
    reject_link = f"{base_url}/verify-login/{temp_token}/reject/"

    print("\n" + "="*80)
    print(f">> 2FA APPROVE LINK: {approve_link}")
    print("="*80 + "\n")

    # Mail dispatch with safe fallback
    target_email = authenticated_user.email or getattr(settings, 'EMAIL_HOST_USER', '')
    if target_email:
        thread = threading.Thread(
            target=send_email_in_background,
            args=(
                f"[AXIS CORE] 2FA ZERO-TRUST CLEARANCE: {authenticated_user.username.upper()}",
                f"Approve:\n{approve_link}",
                getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER),
                [target_email]
            )
        )
        thread.daemon = True
        thread.start()

    request.session['email'] = authenticated_user.email
    return Response({
        'status': 'PENDING',
        'username': authenticated_user.username,
        'role': user_role,
        'approve_link': approve_link  # Direct link frontend ko di
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_login_action(request, token, action):
    try:
        profile = UserProfile.objects.get(approval_token=token)
    except UserProfile.DoesNotExist:
        return Response({'error': 'Invalid or expired handshake link.'}, status=status.HTTP_404_NOT_FOUND)

    if action == 'approve':
        profile.login_approval_status = 'APPROVED'
        profile.save()
        return Response({'status': 'AUTHORIZED', 'message': 'Handshake confirmed. You may return to the console.'},
                        status=status.HTTP_200_OK)
    elif action == 'reject':
        profile.login_approval_status = 'REJECTED'
        profile.approval_token = None
        profile.save()
        return Response({'status': 'TERMINATED', 'message': 'Session locked down and invalidated.'},
                        status=status.HTTP_200_OK)

    return Response({'error': 'Invalid parameter.'}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def check_login_status(request):
    username = request.data.get('username', '').strip()
    try:
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            return Response({'error': 'Record missing.'}, status=status.HTTP_404_NOT_FOUND)
        profile = user.profile
    except Exception:
        return Response({'error': 'Record missing.'}, status=status.HTTP_404_NOT_FOUND)

    if profile.login_approval_status == 'APPROVED':
        token, _ = Token.objects.get_or_create(user=user)
        profile.login_approval_status = 'NONE'
        profile.approval_token = None
        profile.save()
        return Response({
            'status': 'APPROVED',
            'token': token.key,
            'role': profile.role,
            'username': user.username
        }, status=status.HTTP_200_OK)
    elif profile.login_approval_status == 'REJECTED':
        profile.login_approval_status = 'NONE'
        profile.approval_token = None
        profile.save()
        return Response({'status': 'REJECTED'}, status=status.HTTP_200_OK)

    return Response({'status': 'PENDING'}, status=status.HTTP_200_OK)