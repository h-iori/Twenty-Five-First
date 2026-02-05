import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from .models import (
    CustomerProfile, SupportTicket, BulkOrderRequest, OrderItem, Order,
    CancellationRequest, ReturnRequest, Invoice, InvoiceItem, Cart, CartItem,
    Shirt, ShirtVariant, ColorVariant, ProductReview, ShirtMedia
)
from .indexer import MeiliIndexer
from .redis_utils import invoice_cache_invalidate
from .email_utils import send_html_email_async

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# USER PROFILE SIGNALS
# -----------------------------------------------------------------------------

@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    """
    Automatically creates a CustomerProfile whenever a new User is registered.
    """
    if created:
        CustomerProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_customer_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Exception:
        pass

# -----------------------------------------------------------------------------
# NOTIFICATION SIGNALS (EMAILS)
# -----------------------------------------------------------------------------

@receiver(post_save, sender=SupportTicket)
def send_ticket_notifications(sender, instance, created, **kwargs):
    """
    [SECURITY] Logic Hidden
    Triggers transactional email notifications:
    1. Acknowledgment email to the Customer.
    2. Alert email to the Admin team.
    """
    if created:
        # Email dispatch logic masked
        pass

@receiver(post_save, sender=BulkOrderRequest)
def send_bulk_order_notifications(sender, instance, created, **kwargs):
    # [SECURITY] Bulk order notification logic hidden
    pass

@receiver(post_save, sender=User)
def send_welcome_email_on_activation(sender, instance, created, **kwargs):
    """
    [SECURITY] Logic Hidden
    Sends a welcome email upon account activation.
    Uses Redis caching to ensure the email is sent only once (idempotency).
    """
    if not created and instance.is_active:
        # Welcome email dispatch logic masked
        pass

# -----------------------------------------------------------------------------
# ORDER & CHECKOUT SIGNALS
# -----------------------------------------------------------------------------

@receiver(post_save, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """
    [SECURITY] Financial Logic Hidden
    Recalculates the Order total whenever an OrderItem is modified.
    """
    order = instance.order
    # Logic to sum sub-totals masked
    order.save(update_fields=['total_amount'])

@receiver(post_save, sender=Order)
def send_order_confirmation(sender, instance, created, **kwargs):
    """
    [SECURITY] Logic Hidden
    Queues the Order Confirmation email using `transaction.on_commit`
    to ensure the DB transaction is complete before the worker picks up the task.
    """
    if created:
        # Async task triggering masked
        pass

@receiver(post_save, sender=Order)
def send_order_status_update_email(sender, instance, created, **kwargs):
    """
    [SECURITY] Logic Hidden
    Monitors Order status changes (SHIPPED, DELIVERED) and triggers
    appropriate customer notifications.
    """
    if created:
        return
    # Status check and email logic masked

@receiver([post_save, post_delete], sender=CartItem)
def update_cart_timestamp_on_item_change(sender, instance, **kwargs):
    """
    Updates the parent Cart's `updated_at` timestamp for cache invalidation strategies.
    """
    try:
        Cart.objects.filter(pk=instance.cart.pk).update(updated_at=timezone.now())
    except Exception as e:
        logger.error(f"Failed to update timestamp for Cart ID {instance.cart.pk}: {e}")

# -----------------------------------------------------------------------------
# CANCELLATION & RETURNS
# -----------------------------------------------------------------------------

@receiver(post_save, sender=CancellationRequest)
def send_cancellation_notification(sender, instance, created, **kwargs):
    # [SECURITY] Cancellation approval/rejection logic hidden
    pass

@receiver(post_save, sender=ReturnRequest)
def send_return_request_notifications(sender, instance, created, **kwargs):
    """
    [SECURITY] Logic Hidden
    Handles notifications for:
    1. New Return Request submission.
    2. Status updates (Approved/Rejected) with instructions.
    """
    pass

# -----------------------------------------------------------------------------
# INVOICING SIGNALS
# -----------------------------------------------------------------------------

@receiver(post_save, sender=Order)
def manage_invoice_creation_and_updates(sender, instance, **kwargs):
    """
    [SECURITY] Logic Hidden
    1. Automatically generates an Invoice record when Order status reaches 'SHIPPED'.
    2. Invalidates Invoice PDF cache on updates.
    """
    pass

@receiver([post_save, post_delete], sender=Invoice)
def invoice_cache_management(sender, instance, **kwargs):
    # [SECURITY] Cache invalidation logic masked
    pass

# -----------------------------------------------------------------------------
# ENTERPRISE SEO GENERATION (SCHEMA.ORG)
# -----------------------------------------------------------------------------

def generate_enterprise_seo(color_variant):
    """
    [SECURITY] Proprietary SEO Strategy Hidden.
    
    Generates dynamic 2026-Compliant JSON-LD payloads including:
    1. Product Metadata (Title, Description).
    2. Breadcrumb Navigation.
    3. Aggregate Offers (Inventory & Pricing per size).
    4. Merchant Return Policy & Shipping Details.
    5. Rich Media & Review Aggregates.
    """
    return {}

@receiver(post_save, sender=ColorVariant)
def update_self_seo(sender, instance, **kwargs):
    # Updates SEO payload for the specific variant
    pass

@receiver(post_save, sender=ShirtVariant)
def update_parent_color_seo(sender, instance, **kwargs):
    # Propagates size/price changes to the parent ColorVariant's SEO
    pass

@receiver(post_save, sender=Shirt)
def update_all_colors_seo(sender, instance, **kwargs):
    # Propagates global product changes to all child variants
    pass

@receiver([post_save, post_delete], sender=ProductReview)
def update_reviews_seo(sender, instance, **kwargs):
    # Updates AggregateRating schema on new reviews
    pass

# -----------------------------------------------------------------------------
# SEARCH INDEXING (MEILISEARCH)
# -----------------------------------------------------------------------------

indexer = MeiliIndexer()

@receiver(post_save, sender=ColorVariant)
def index_color_variant(sender, instance, **kwargs):
    """
    [SECURITY] Search Logic Hidden
    Real-time index update when a product is modified.
    """
    indexer.update_document(instance)

@receiver(post_delete, sender=ColorVariant)
def remove_color_variant(sender, instance, **kwargs):
    indexer.delete_document(instance.id)

@receiver(post_save, sender=ShirtVariant)
def update_parent_variant_stock(sender, instance, **kwargs):
    if instance.color_variant:
        indexer.update_document(instance.color_variant)

@receiver(post_save, sender=Shirt)
def update_all_shirt_variants(sender, instance, **kwargs):
    # Bulk re-indexing logic masked
    pass