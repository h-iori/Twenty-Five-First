# Standard library imports
import json
import logging
import re
import random
import hashlib
import time
import os
from functools import wraps
import uuid
from datetime import datetime as dt
from decimal import Decimal
from math import ceil

# Third-party imports
import razorpay
import requests
from django_recaptcha.client import submit
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from weasyprint import HTML, CSS
from PIL import Image, UnidentifiedImageError

# Django imports
from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.cache import cache
from django.core.exceptions import (ObjectDoesNotExist, ValidationError)
from django.core.mail import BadHeaderError
from django.core.validators import validate_email
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction, IntegrityError, DatabaseError
from django.db.models import Case, F, Max, Prefetch, Sum, When, Q, Min
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from smtplib import SMTPException

# Local application imports
from . import models
from .search_service import SearchService
from .email_utils import html_email_wrapper, send_html_email_async
from .redis_utils import (can_resend, clear_otp, generate_otp, get_coupon_usage_counts, 
                          increment_coupon_counters, clear_pending_registration,
                          get_cached_cart_snapshot, cache_cart_snapshot, store_pending_registration,
                          invalidate_cart_cache, invoice_cache_get_or_compute, get_pending_registration,
                          redis_lock, store_otp, verify_otp as redis_verify_otp, decrement_resend, 
                          login_attempt_redis, get_cart_snapshot_or_db)

# Enterprise logger
logger = logging.getLogger('auth')

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def get_or_create_cart_for_request(request):
    """
    [SECURITY] Proprietary Logic Hidden
    Retrieves the cart for authenticated or anonymous users.
    Handles session-to-user cart merging logic upon login.
    """
    return models.Cart.objects.none(), False

def _get_lock_key_for_request(request, cart=None):
    """
    [SECURITY] Proprietary Logic Hidden
    Generates a unique Redis lock key based on cart ID, user ID, or session key
    to prevent race conditions during high-concurrency cart updates.
    """
    return "lock_key_placeholder"

def _calculate_coupon_discount(coupon, user, order_total, products, items_with_prices):
    """
    [SECURITY] Proprietary Logic Hidden
    Calculates discount based on coupon type (Percentage, Fixed, BOGO).
    Validates usage limits per user and total global usage.
    """
    return 0, None

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

def _products_api_helper(request, s_type_name, cache_prefix, is_new=False):
    """
    [SECURITY] Proprietary Logic Hidden
    Handles product filtering, searching (Meilisearch/Postgres), sorting, and caching.
    
    Logic flow:
    1. Parse GET parameters (q, pattern, material, color, size, price range).
    2. Generate cache key based on params hash.
    3. If cache miss: Query DB with prefetch_related for optimized media retrieval.
    4. Annotate stock and min_price for sorting.
    5. Serialize and cache response.
    """
    return Response({'status': 'demo_data_only', 'results': []})

# -----------------------------------------------------------------------------
# PRODUCT API VIEWS
# -----------------------------------------------------------------------------

@api_view(['GET'])
def formal_products_api(request):
    return _products_api_helper(request, 'Formal', 'formal')

@api_view(['GET'])
def casual_products_api(request):
    return _products_api_helper(request, 'Casual', 'casual')

@api_view(['GET'])
def kids_products_api(request):
    return _products_api_helper(request, 'Kids', 'kids')

@api_view(['GET'])
def occasional_products_api(request):
    return _products_api_helper(request, 'Occasional', 'occasional')

@api_view(['GET'])
def new_products_api(request):
    return _products_api_helper(request, 'New', 'new', is_new=True)

@api_view(['GET'])
def slim_products_api(request):
    return _products_api_helper(request, 'Slim Fit', 'slim')

@api_view(['GET'])
def search_products_api(request):
    """
    [SECURITY] Proprietary Logic Hidden
    Interfaces with SearchService (Meilisearch) to return fast, relevant product hits.
    """
    return Response({'results': [], 'count': 0})

@api_view(['GET'])
def product_reviews_api(request, slug):
    """
    [SECURITY] Proprietary Logic Hidden
    Fetches and paginates reviews for a specific product.
    Implements caching strategies based on review update timestamps.
    """
    return Response({'results': []})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def browsing_history_api(request):
    """
    [SECURITY] Proprietary Logic Hidden
    Returns the user's recently viewed products using Redis-backed history or DB.
    """
    return Response({'results': [], 'has_next': False})

# -----------------------------------------------------------------------------
# CART MANAGEMENT VIEWS
# -----------------------------------------------------------------------------

class CartView(View):
    def get(self, request):
        """
        [SECURITY] Proprietary Logic Hidden
        Renders the cart HTML fragment and calculates totals (subtotal, tax, grand total).
        Triggers an async cache update for the cart snapshot.
        """
        return JsonResponse({'cart_html': '', 'total': 0})

    def _get_or_create_cart(self, request):
        return get_or_create_cart_for_request(request)

class AddToCartView(View):
    def post(self, request, variant_id):
        """
        [SECURITY] Critical Logic Hidden
        
        Logic Flow:
        1. Validates stock availability.
        2. Acquires Redis Distributed Lock to prevent race conditions (overselling).
        3. Updates CartItem within a database transaction.
        4. Refreshes Cart Snapshot Cache.
        """
        return JsonResponse({'success': True, 'message': 'Item added (Demo)'})

class UpdateCartView(View):
    def post(self, request, item_id):
        """
        [SECURITY] Critical Logic Hidden
        Updates item quantity with lock protection.
        Handles atomic updates and cache invalidation.
        """
        return JsonResponse({'success': True})

class RemoveFromCartView(View):
    def post(self, request, item_id):
        """
        [SECURITY] Critical Logic Hidden
        Removes item from cart safely and recalculates tax/totals.
        """
        return JsonResponse({'success': True})

def get_cart_summary(request):
    """
    [SECURITY] Performance Logic Hidden
    Retrieves lightweight cart summary from Redis snapshot to avoid DB hits on every page load.
    Falls back to DB calculation if cache is cold.
    """
    return JsonResponse({'item_count': 0, 'total': 0})

# -----------------------------------------------------------------------------
# PAGE RENDERING VIEWS
# -----------------------------------------------------------------------------

def category_view(s_type_name, template_name, context_name, url_name):
    """
    Decorator for category pages to standardize context injection and caching.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # [SECURITY] Query logic hidden
            return render(request, template_name, {})
        return wrapper
    return decorator

@cache_page(120, key_prefix="page:formal")
@category_view('Formal', 'formals.html', 'formal_products', 'formal')
def formal(request): pass

@cache_page(120, key_prefix="page:casual")
@category_view('Casual', 'casuals.html', 'casual_products', 'casual')
def casual(request): pass

@cache_page(120, key_prefix="page:kids")
@category_view('Kids', 'kids.html', 'kids_products', 'kid')
def kid(request): pass

@cache_page(120, key_prefix="page:occasional")
@category_view('Occasional', 'occasionals.html', 'occasional_products', 'occasional')
def occasional(request): pass

@cache_page(120, key_prefix="page:slimfit")
@category_view('Slim Fit', 'slim_fit.html', 'slim_products', 'slimfit')
def slimfit(request): pass

@cache_page(120, key_prefix="page:index")
def index(request):
    # [SECURITY] Landing page logic hidden
    return render(request, 'index.html', {})

@cache_page(120, key_prefix="page:explore")
def explore(request):
    # [SECURITY] Catalog exploration logic hidden
    return render(request, 'explore.html', {})

@cache_page(120, key_prefix="page:new_arrival")
def new_arrival(request):
    # [SECURITY] New arrivals logic hidden
    return render(request, 'new_arrivals.html', {})

# -----------------------------------------------------------------------------
# AUTHENTICATION VIEWS
# -----------------------------------------------------------------------------

def login_view(request):
    """
    [SECURITY] Logic Hidden
    Handles user login with Rate Limiting via Redis.
    Checks for banned users and active status.
    """
    return render(request, 'login.html')

@csrf_protect
@ensure_csrf_cookie
def signup(request):
    """
    [SECURITY] Logic Hidden
    Handles new user registration.
    
    Features hidden:
    1. reCAPTCHA validation.
    2. Input sanitization.
    3. Temporary storage of registration data in Redis (TTL).
    4. Async OTP email dispatch via SMTP.
    """
    return render(request, 'signup.html')

@csrf_protect
@ensure_csrf_cookie
def verify_otp(request, email):
    """
    [SECURITY] Logic Hidden
    Verifies OTP from Redis.
    On success: Migrates any Guest Checkout data (orders, addresses) to the new account.
    Creates CustomerProfile and logs user in.
    """
    return render(request, 'verify_otp.html')

@require_http_methods(["POST"])
@csrf_protect
def resend_otp(request):
    # [SECURITY] Resend logic with rate limiting hidden
    return JsonResponse({'success': True})

@login_required(login_url='login')
def logout_all(request):
    """
    [SECURITY] Session Management Hidden
    Iterates through session backend to flush all active sessions for the user.
    """
    logout(request)
    return redirect('login')

# -----------------------------------------------------------------------------
# USER DASHBOARD & SETTINGS
# -----------------------------------------------------------------------------

@login_required(login_url='login')
def user_dashboard(request):
    # [SECURITY] Dashboard data aggregation hidden (Orders, Wishlist, History)
    return render(request, 'dashboard.html')

@login_required(login_url='login')
def user_orders(request):
    # [SECURITY] Order fetching logic hidden
    return render(request, 'orders.html')

@login_required(login_url='login')
@require_POST
@csrf_protect
@transaction.atomic
def cancel_order(request):
    """
    [SECURITY] Critical Logic Hidden
    Handles order cancellation.
    1. Validates order status.
    2. Restocks inventory.
    3. Triggers refund via Razorpay API if eligible.
    """
    return JsonResponse({'success': True, 'message': 'Order cancelled (Demo)'})

@login_required(login_url='login')
@csrf_protect
@require_POST
@transaction.atomic
def return_order(request):
    """
    [SECURITY] Logic Hidden
    Validates return window and creates return request.
    Handles secure image upload validation (size/format checks).
    """
    return JsonResponse({'success': True})

@login_required(login_url='login')
def wishlist(request):
    return render(request, 'wishlist.html')

@login_required(login_url='login')
def addresses(request):
    # [SECURITY] CRUD operations for User Addresses hidden
    return render(request, 'addresses.html')

@login_required(login_url='login')
def account_settings(request):
    # [SECURITY] Profile update and Password change logic hidden
    return render(request, 'account_settings.html')

@login_required(login_url='login')
def verify_email_change(request):
    # [SECURITY] Email change verification flow hidden
    return render(request, 'verify_email_change.html')

@login_required(login_url='login')
def reviews(request):
    return render(request, 'reviews.html')

@login_required(login_url='login')
def support(request):
    # [SECURITY] Support ticket creation logic hidden
    return render(request, 'support.html')

# -----------------------------------------------------------------------------
# PRODUCT INTERACTION VIEWS
# -----------------------------------------------------------------------------

def details(request, slug):
    """
    [SECURITY] Logic Hidden
    Renders product detail page.
    - Fetches variant data.
    - Tracks browsing history (async).
    - Checks wishlist/cart status.
    - Loads related products via cache.
    """
    return render(request, 'product_details.html', {})

@api_view(['GET'])
def variant_details_api(request, variant_id):
    # [SECURITY] JSON API for variant switching hidden
    return JsonResponse({'success': True})

@require_POST
@login_required
@csrf_protect
def submit_review(request, slug):
    # [SECURITY] Review submission with transaction locking hidden
    return JsonResponse({'success': True})

@require_POST
@login_required
@csrf_protect
def delete_review(request, slug):
    return JsonResponse({'success': True})

@require_POST
@login_required
@csrf_protect
def add_to_wishlist(request, variant_id):
    # [SECURITY] Wishlist addition hidden
    return JsonResponse({'success': True})

@require_POST
@login_required
@csrf_protect
def remove_from_wishlist(request, variant_id):
    return JsonResponse({'success': True})

class ForgetPasswordView(View):
    # [SECURITY] Password reset flow (OTP generation + Verification) hidden
    def get(self, request):
        return render(request, 'forget_password.html')
    def post(self, request):
        return render(request, 'forget_password.html')

def search_products(request):
    return render(request, 'search_results.html')

def bulk_order(request):
    # [SECURITY] Bulk order submission with IP-based rate limiting hidden
    return render(request, 'bulk_order.html')

# -----------------------------------------------------------------------------
# SHIPPING INTEGRATION (SHIPROCKET)
# -----------------------------------------------------------------------------

# [SECURITY] Shiprocket configuration hidden
BASE_URL = "https://api.shiprocket.in/v1/external"

def authenticate_shiprocket():
    """
    [SECURITY] Third-Party Integration Hidden
    Authenticates with Shiprocket API and caches the bearer token.
    Uses Redis locks to prevent concurrent authentication requests.
    """
    return "demo_token"

def get_cheapest_courier(token, pickup_pincode, delivery_pincode, weight, cod=0, declared_value=1000):
    """
    [SECURITY] Algorithm Hidden
    Queries shipping API for serviceability.
    Selects the most cost-effective courier based on weight and service zone.
    """
    return "Demo Courier", 100, "2024-01-01", None

@require_POST
@csrf_protect
def get_delivery_estimate(request):
    """
    [SECURITY] Logic Hidden
    Calculates estimated delivery time and shipping cost based on cart weight and destination.
    """
    return JsonResponse({"success": True, "shipping_cost": 0})

def validate_pincode_serviceability(token, pickup_pincode, delivery_pincode, weight, cod, declared_value):
    return True, None

# -----------------------------------------------------------------------------
# CHECKOUT & ORDER PROCESSING
# -----------------------------------------------------------------------------

@require_POST
@csrf_protect
def prepare_checkout(request):
    """
    [SECURITY] Logic Hidden
    Prepares a temporary checkout session for "Buy Now" functionality.
    """
    return JsonResponse({"success": True})

class CheckoutView(View):
    def get(self, request, variant_id=None):
        """
        [SECURITY] Proprietary Logic Hidden
        Prepares the checkout page context:
        - Calculates final totals (Items + Tax + Shipping).
        - Fetches saved user addresses.
        - Validates stock one last time before rendering.
        """
        return render(request, "checkout.html", {})

    def post(self, request, variant_id=None):
        """
        [SECURITY] CRITICAL TRANSACTION LOGIC HIDDEN
        
        This method handles the core order placement logic:
        1. Form Validation (Address, Phone, Email).
        2. Stock Reservation: Locks DB rows to prevent overselling.
        3. Shipping Validation: Re-verifies serviceability with API.
        4. Payment Initialization: Creates Order/Payment records (Pending state).
        5. Snapshot Creation: Caches the exact state of the order for payment verification.
        
        Code removed for security and portfolio demonstration.
        """
        return JsonResponse({"success": True})

    def _get_or_create_cart(self, request):
        return get_or_create_cart_for_request(request)

@require_http_methods(['GET', 'POST'])
@csrf_protect
def apply_coupon(request):
    """
    [SECURITY] Logic Hidden
    Applies or removes coupons.
    Validates rules (expiry, min order value, category restrictions) via _calculate_coupon_discount.
    """
    return JsonResponse({'success': True})

# -----------------------------------------------------------------------------
# PAYMENT INTEGRATION (RAZORPAY)
# -----------------------------------------------------------------------------

@require_POST
@csrf_protect
def create_razorpay_order(request):
    """
    [SECURITY] Payment Gateway Integration Hidden
    Creates a corresponding order on Razorpay server to initiate payment flow.
    """
    return JsonResponse({'success': True, 'razorpay_order_id': 'order_demo_123'})

@require_POST
@csrf_protect
def verify_razorpay_payment(request):
    """
    [SECURITY] CRITICAL FINANCIAL LOGIC HIDDEN
    
    Verifies the payment signature returned by Razorpay.
    On Success:
    1. Converts 'Pending' order to 'Confirmed'.
    2. Deducts Inventory permanently.
    3. Generates Invoice.
    4. Clears Cart and Checkout Session.
    
    Includes idempotency checks and signature validation.
    """
    return JsonResponse({'success': True, 'redirect_url': '/'})

class OrderConfirmationView(View):
    def get(self, request, order_number):
        # [SECURITY] Renders confirmation page with security checks for guest/user access
        return render(request, 'order_confirmation.html', {})

# -----------------------------------------------------------------------------
# INVOICE GENERATION
# -----------------------------------------------------------------------------

@login_required
def invoice_view(request, order_number):
    """
    [SECURITY] Logic Hidden
    Generates HTML invoice dynamically based on Order data.
    Calculates tax breakdowns (CGST/SGST/IGST).
    """
    return HttpResponse("Invoice HTML")

@login_required
def invoice_pdf_view(request, order_number):
    """
    [SECURITY] Logic Hidden
    Converts Invoice HTML to PDF using WeasyPrint for download.
    """
    return HttpResponse("PDF Content", content_type='application/pdf')

# -----------------------------------------------------------------------------
# STATIC PAGES & ROBOTS
# -----------------------------------------------------------------------------

@cache_page(86400)
def terms(request): return render(request, 'terms.html')

@cache_page(86400)
def privacy_view(request): return render(request, 'privacy.html')

@cache_page(86400)
def about(request): return render(request, 'about.html')

@cache_page(86400)
def contact(request): return render(request, 'contact.html')

@cache_page(86400)
def sizefaq(request): return render(request, 'size_faq.html')

@require_GET
@cache_page(60 * 60 * 24) 
def robots_txt(request):
    # Standard robots.txt generation
    return HttpResponse("User-agent: *\nDisallow: /api/", content_type="text/plain")