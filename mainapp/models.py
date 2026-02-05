import uuid
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import FieldError, ValidationError
from django.core.validators import RegexValidator
from django.db import models,transaction
from django.db.models import Q, UniqueConstraint
from django.db.models.query import QuerySet
from django.utils import timezone
from django.conf import settings
from django.urls import reverse


class SoftDeleteQuerySet(QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def restore(self):
        return super().update(is_deleted=False, deleted_at=None)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False):
        # Soft delete by default. Use hard=True for permanent deletion.
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self, cascade=False):
        # Restore this object and optionally cascade to related soft-deleted models.
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

        if cascade:
            for rel in self._meta.related_objects:
                accessor = rel.get_accessor_name()
                try:
                    related_manager = getattr(self, accessor)
                except Exception:
                    continue
                rel_model = rel.related_model
                if issubclass(rel_model, SoftDeleteModel):
                    try:
                        related_manager.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)
                    except (ValueError, FieldError) as e:
                        import logging
                        logging.getLogger(__name__).warning(f"Failed to cascade restore for {accessor}: {e}")


class CustomerProfile(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=10, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_ban = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"


class Address(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    INDIAN_STATES = [
        ('01', 'Jammu & Kashmir'), ('02', 'Himachal Pradesh'), ('03', 'Punjab'),
        ('04', 'Chandigarh'), ('05', 'Uttarakhand'), ('06', 'Haryana'),
        ('07', 'Delhi'), ('08', 'Rajasthan'), ('09', 'Uttar Pradesh'),
        ('10', 'Bihar'), ('11', 'Sikkim'), ('12', 'Arunachal Pradesh'),
        ('13', 'Nagaland'), ('14', 'Manipur'), ('15', 'Mizoram'),
        ('16', 'Tripura'), ('17', 'Meghalaya'), ('18', 'Assam'),
        ('19', 'West Bengal'), ('20', 'Jharkhand'), ('21', 'Odisha'),
        ('22', 'Chhattisgarh'), ('23', 'Madhya Pradesh'), ('24', 'Gujarat'),
        ('25', 'Daman & Diu'), ('26', 'Dadra & Nagar Haveli'), ('27', 'Maharashtra'),
        ('28', 'Andhra Pradesh (Old)'), ('29', 'Karnataka'), ('30', 'Goa'),
        ('31', 'Lakshadweep'), ('32', 'Kerala'), ('33', 'Tamil Nadu'),
        ('34', 'Puducherry'), ('35', 'Andaman & Nicobar Islands'), ('36', 'Telangana'),
        ('37', 'Andhra Pradesh'), ('38', 'Ladakh'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50, choices=INDIAN_STATES)
    zip_code = models.CharField(
        max_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'Zip code must be a 6-digit number')]
    )
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        indexes = [
            models.Index(fields=['user', 'is_default']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.city}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
        # Ensure only one default address per user.
            if self.is_default:
                Address.all_objects.filter(
                    user=self.user,
                    is_default=True
                ).exclude(id=self.id).update(is_default=False)
            super().save(*args, **kwargs)

    def clean(self):
        super().clean()


class ShirtType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Pattern(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Material(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=9, blank=True, null=True)

    def __str__(self):
        return self.name


class Size(models.Model):
    SIZES = [('S', 'Small'), ('M', 'Medium'), ('L', 'Large'), ('XL', 'Extra Large')]
    name = models.CharField(max_length=10, choices=SIZES, unique=True)

    def __str__(self):
        return self.name


class Shirt(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=500, blank=True, unique=True)
    description = models.TextField()
    s_type = models.ForeignKey(ShirtType, on_delete=models.CASCADE)
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    search_vector = SearchVectorField(null=True, blank=True)
    hsn_code = models.CharField(
        max_length=10,
        default="6205",
        help_text="HSN code for GST classification"
    )
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        if not self.slug:
            seo_string = f"{self.pattern.name} {self.material.name} {self.s_type.name} {self.name}"

            target_slug = slugify(seo_string)

            unique_slug = target_slug
            counter = 1
            while Shirt.all_objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{target_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['id']
        indexes = [
            GinIndex(fields=['search_vector']),
        ]
        constraints = [
            UniqueConstraint(
                fields=['slug'], 
                condition=Q(is_deleted=False), 
                name='unique_active_shirt_slug'
            )
        ]


class ColorVariant(models.Model):
    shirt = models.ForeignKey(Shirt, on_delete=models.CASCADE, related_name="color_variants")
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    seo_data = models.JSONField(default=dict, blank=True, help_text="Cached SEO Data for this specific color")
    slug = models.SlugField(max_length=255, blank=True, null=True, unique=True)
    class Meta:
        ordering = ['id']
    def save(self, *args, **kwargs):
        # 2. Auto-generate slug if it doesn't exist
        if not self.slug:
            # Pattern: shirt-slug + color-name (e.g., casual-shirt-navy-blue)
            base_slug = f"{self.shirt.slug}-{self.color.name}"
            target_slug = slugify(base_slug)
            
            # 3. Handle Duplicate Slugs (Safety Check)
            counter = 1
            unique_slug = target_slug
            while ColorVariant.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{target_slug}-{counter}"
                counter += 1
            
            self.slug = unique_slug

        super().save(*args, **kwargs)

    def __str__(self):
        try:
            return f"{self.shirt.name} ({self.color.name})"
        except Exception:
            return f"Variant {self.id} (Orphaned)" 
    def get_absolute_url(self):
        """Standard Django interface for the relative path."""
        return reverse('product_detail', kwargs={'slug': self.slug})

    def get_full_url(self):
        """
        Enterprise Helper: Returns the full domain URL.
        Useful for Sitemaps, Emails, and API responses where 'request' is missing.
        """
        site_url = getattr(settings, 'SITE_URL', '')
        # Ensure no double slashes if settings has trailing slash
        return f"{site_url.rstrip('/')}{self.get_absolute_url()}"


class ShirtVariant(SoftDeleteModel):
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.CASCADE, related_name="variants")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, blank=True)
    price = models.PositiveIntegerField(help_text="Base price in INR without tax")
    stock = models.PositiveIntegerField()
    weight = models.PositiveIntegerField(default=300, help_text="Weight in grams")
    is_active = models.BooleanField(default=True)
    price_with_tax = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['price', 'id']
        indexes = [
            models.Index(fields=['sku', 'is_active']),
            models.Index(fields=['price_with_tax']),
            models.Index(fields=['color_variant']),
        ]
        constraints = [
            UniqueConstraint(
                fields=['sku'], 
                condition=Q(is_deleted=False), 
                name='unique_active_variant_sku'
            )
        ]
    def calculate_price_with_tax(self):
        # Calculate price including 5% or 18% tax based on price.
        tax_rate = 5 if self.price <= 2500 else 18
        tax_amount = (self.price * tax_rate + 99) // 100
        return self.price + tax_amount

    def generate_sku(self):
        # Generate a unique SKU.
        shirt = self.color_variant.shirt
        color = self.color_variant.color
        size = self.size
        type_code = shirt.s_type.name[:2].upper()
        pattern_code = shirt.pattern.name[:2].upper()
        material_code = shirt.material.name[:2].upper()
        color_code = color.name[:2].upper()
        size_code = size.name[0].upper()
        base_sku = f"{type_code}{pattern_code}{material_code}{color_code}{size_code}"
        sequence = 1
        sku = f"{base_sku}{sequence:03d}"
        max_iterations = 1000
        iterations = 0
        while ShirtVariant.objects.filter(sku=sku).exists() and iterations < max_iterations:
            sequence += 1
            sku = f"{base_sku}{sequence:03d}"
            iterations += 1

        if iterations >= max_iterations:
            sku = f"{base_sku}-{uuid.uuid4().hex[:8].upper()}"

        return sku

    def save(self, *args, **kwargs):
        # Auto-generate SKU and calculate price_with_tax on save.
        with transaction.atomic():
            if not self.sku:
                self.sku = self.generate_sku()

            self.price_with_tax = self.calculate_price_with_tax()

            super().save(*args, **kwargs)

    def __str__(self):
        try:
            return f"{self.color_variant} - {self.size} (₹{self.price_with_tax} incl. tax)"
        except Exception:
            return f"Variant {self.id} (Orphaned)"


class ShirtMedia(models.Model):
    MEDIA_TYPES = (('image', 'Image'), ('video', 'Video'))
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    media_file = models.FileField(upload_to='shirts', max_length=255)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.media_type} for {self.color_variant}"


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts',
        help_text="Leave blank for anonymous users."
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts',
        help_text="Coupon applied to this cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Cart for {self.user.username if self.user else 'Anonymous'} ({self.id})"

    @property
    def total_price(self):
        # Calculates total price, applying a valid coupon if one is present.
        base_total = sum(item.subtotal for item in self.items.all())

        discount = 0
        if self.coupon:
            user = self.user if self.user else None
            products = [item.variant.color_variant.shirt for item in self.items.all()]
            is_valid, reason = self.coupon.is_valid(
                user=user,
                order_total=base_total,
                products=products
            )
            if is_valid:
                if self.coupon.discount_type == 'PERCENTAGE':
                    discount = (base_total * self.coupon.discount_value + 99) // 100
                elif self.coupon.discount_type == 'FIXED':
                    discount = min(base_total, self.coupon.discount_value)
                elif self.coupon.discount_type == 'FREE_SHIPPING':
                    discount = 0
                elif self.coupon.discount_type == 'BOGO':
                    items = sorted(self.items.all(), key=lambda x: x.subtotal)
                    if len(items) >= 2:
                        discount = items[0].subtotal
            else:
                self.coupon = None
                self.save()

        return max(0, base_total - discount), discount

    class Meta:
        unique_together = (('user', 'session_key'),)
        constraints = [
            UniqueConstraint(
                fields=['user'],
                condition=models.Q(session_key__isnull=True),
                name='unique_cart_per_authenticated_user'
            )
        ]


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ShirtVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_with_tax = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.variant} in Cart {self.cart.id}"

    @property
    def subtotal(self):
        return self.quantity * self.price_with_tax

    def save(self, *args, **kwargs):
        if self.price_with_tax != self.variant.price_with_tax:
            self.price_with_tax = self.variant.price_with_tax
        super().save(*args, **kwargs)

    class Meta:
        unique_together = (('cart', 'variant'),)


class GuestCheckout(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    INDIAN_STATES = Address.INDIAN_STATES
    email = models.EmailField(max_length=254)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, choices=INDIAN_STATES)
    pincode = models.CharField(
        max_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'Pincode must be a 6-digit number')]
    )
    phone_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'Phone number must be a 10-digit number')]
    )
    billing_address = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Guest Checkout: {self.first_name} {self.last_name} - {self.email} - {self.created_at}"


class ProductReview(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    shirt = models.ForeignKey('Shirt', on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shirt_reviews',
        help_text="The user who submitted the review."
    )
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Remove unique_together to avoid DB conflicts with soft deletes
        # Enforce via clean() instead
        indexes = [
            models.Index(fields=['shirt', 'user']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return f"{self.user.username} - {self.shirt.name} ({self.rating}/5)"

    def clean(self):
        super().clean()  # Call parent clean() for SoftDeleteModel if needed
        if not self.user:
            raise ValidationError("Reviews can only be submitted by authenticated users.")
        if self.rating not in range(1, 6):
            raise ValidationError("Rating must be between 1 and 5.")
        
        # Enforce uniqueness against active (non-deleted) reviews
        if self.shirt and self.user:
            existing = self.__class__.objects.filter(
                shirt=self.shirt, 
                user=self.user
            ).exclude(pk=self.pk)  # Exclude self during updates
            if existing.exists():
                raise ValidationError({
                    'shirt': 'You have already submitted a review for this product.',
                })

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensures clean() runs before save
        super().save(*args, **kwargs)

    @staticmethod
    def calculate_average_rating(shirt):
        reviews = ProductReview.objects.filter(shirt=shirt)
        avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
        return round(avg_rating, 2) if avg_rating else 0.0

    @classmethod
    def has_reviewed(cls, shirt, user):
        return cls.objects.filter(shirt=shirt, user=user).exists()


class Wishlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="wishlist",
        help_text="Leave blank for anonymous wishlists."
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    variant = models.ForeignKey(
        ShirtVariant,
        on_delete=models.CASCADE,
        related_name="wishlist_entries"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant', 'session_key')

    def __str__(self):
        owner = self.user.username if self.user else 'Anonymous'
        return f"{owner} - {self.variant}"


class Order(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled'), ('RETURNED', 'Returned'),
    ]
    VERIFICATION_STATUS_CHOICES = [
        ('UNVERIFIED', 'Unverified'), ('PHONE_VERIFIED', 'Phone Verified'),
        ('EMAIL_VERIFIED', 'Email Verified'), ('FULLY_VERIFIED', 'Fully Verified'),
        ('SUSPICIOUS', 'Suspicious'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='orders',
        help_text="Authenticated user who placed the order. Null for guest orders."
    )
    guest_checkout = models.OneToOneField(
        'GuestCheckout', on_delete=models.SET_NULL, null=True, blank=True, related_name='order',
        help_text="Guest checkout details for non-authenticated users."
    )
    cart = models.OneToOneField(
        'Cart', on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Cart associated with this order."
    )
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', help_text="Coupon applied to this order, if any."
    )
    discount_amount = models.PositiveIntegerField(default=0, help_text="Total discount applied from coupon in INR.")
    order_number = models.CharField(max_length=20, editable=False, help_text="Unique order identifier (e.g., TFF-20250513-1A2B3C).")
    total_amount = models.PositiveIntegerField(help_text="Total order amount in INR including items, tax, shipping, and discounts.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', help_text="Current status of the order.")
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('PAID', 'Paid'), ('UNPAID', 'Unpaid'), ('FAILED', 'Failed'),
            ('REFUND_INITIATED', 'Refund Initiated'), ('REFUNDED', 'Refunded'),
            ('REFUND_FAILED', 'Refund Failed'),
        ],
        default='UNPAID', help_text="Status of the payment for this order."
    )
    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='UNVERIFIED',
        help_text="Verification status of the order (e.g., phone/email verified)."
    )
    shipping_address = models.ForeignKey(
        'Address', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', help_text="The address used for shipping this order (for authenticated users)."
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the order was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the order was last updated.")
    cancelled_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the order was cancelled.")

    shipping_address_line = models.TextField(null=True, blank=True, help_text="Shipping address line stored at order creation.")
    shipping_city = models.CharField(max_length=100, null=True, blank=True, help_text="Shipping city stored at order creation.")
    shipping_state = models.CharField(max_length=2, choices=Address.INDIAN_STATES, null=True, blank=True, help_text="Shipping state stored at order creation.")
    shipping_zip_code = models.CharField(max_length=6, null=True, blank=True, help_text="Shipping zip code stored at order creation.")
    shipping_phone_number = models.CharField(max_length=10, null=True, blank=True, help_text="Shipping phone number stored at order creation.")
    shipping_email = models.EmailField(max_length=254, null=True, blank=True, help_text="Shipping email stored at order creation.")
    shipping_recipient = models.CharField(max_length=200, null=True, blank=True, help_text="Recipient name stored at order creation.")

    def __str__(self):
        owner = self.user.username if self.user else 'Anonymous'
        return f"Order {self.order_number} - {owner}"

    def save(self, *args, **kwargs):
        # Generate unique order number and update shipping timestamp if status changes to SHIPPED.
        with transaction.atomic():
            # Generate unique order number and update shipping timestamp if status changes to SHIPPED.
            date_str = timezone.now().strftime("%Y%m%d")

            if not self.order_number:
                unique_id = uuid.uuid4().hex[:6].upper()
                self.order_number = f"TFF-{date_str}-{unique_id}"
                # Loop to ensure uniqueness inside the transaction
                while Order.objects.filter(order_number=self.order_number).exists():
                    unique_id = uuid.uuid4().hex[:6].upper()
                    self.order_number = f"TFF-{date_str}-{unique_id}"

            if self.pk:
                old_order = Order.all_objects.get(pk=self.pk)
                if old_order.status != self.status and self.status == 'SHIPPED':
                    if hasattr(self, 'shipping') and self.shipping and not self.shipping.shipped_at:
                        self.shipping.shipped_at = timezone.now()
                        self.shipping.save()
            super().save(*args, **kwargs)

    @property
    def shipping_address_details(self):
        # Get shipping details, prioritizing stored fields over relations.
        if self.shipping_address_line:
            return {
                'address_line': self.shipping_address_line, 'city': self.shipping_city,
                'state': [name for code, name in Address.INDIAN_STATES if code == self.shipping_state][0] if self.shipping_state in [code for code, _ in Address.INDIAN_STATES] else self.shipping_state,
                'zip_code': self.shipping_zip_code, 'phone_number': self.shipping_phone_number,
                'email': self.shipping_email, 'recipient': self.shipping_recipient
            }
        elif self.guest_checkout:
            return {
                'address_line': self.guest_checkout.address, 'city': self.guest_checkout.city,
                'state': [name for code, name in Address.INDIAN_STATES if code == self.guest_checkout.state][0] if self.guest_checkout.state in [code for code, _ in Address.INDIAN_STATES] else self.guest_checkout.state,
                'zip_code': self.guest_checkout.pincode, 'phone_number': self.guest_checkout.phone_number,
                'email': self.guest_checkout.email, 'recipient': f"{self.guest_checkout.first_name} {self.guest_checkout.last_name}"
            }
        elif self.shipping_address:
            return {
                'address_line': self.shipping_address.address_line, 'city': self.shipping_address.city,
                'state': [name for code, name in Address.INDIAN_STATES if code == self.shipping_address.state][0] if self.shipping_address.state in [code for code, _ in Address.INDIAN_STATES] else self.shipping_address.state,
                'zip_code': self.shipping_address.zip_code, 'phone_number': self.user.profile.phone_number if hasattr(self.user, 'profile') and self.user.profile.phone_number else '',
                'email': self.user.email, 'recipient': f"{self.user.first_name} {self.user.last_name}"
            }
        return None

    @property
    def calculated_total(self):
        # Calculate final total including items, discount, and shipping.
        base_total = sum(item.subtotal for item in self.items.all())
        discount = self.discount_amount or 0
        is_free_shipping = self.coupon and self.coupon.discount_type == 'FREE_SHIPPING'
        shipping_cost = self.shipping.shipping_cost if hasattr(self, 'shipping') and self.shipping and not is_free_shipping else 0
        return max(0, base_total - discount + shipping_cost)

    @property
    def delivered_at(self):
        if self.status == 'DELIVERED' and hasattr(self, 'shipping') and self.shipping.shipped_at:
            return self.shipping.shipped_at
        return None

    @property
    def is_within_return_period(self):
        if self.delivered_at:
            return (timezone.now() - self.delivered_at).days <= 10
        return False

    @property
    def has_pending_return_request(self):
        return self.return_requests.filter(status='PENDING').exists()

    @property
    def has_approved_return_request(self):
        return self.return_requests.filter(status='APPROVED').exists()

    @property
    def has_rejected_return_request(self):
        return self.return_requests.filter(status='REJECTED').exists()

    def update_total(self):
        self.total_amount = self.calculated_total
        super().save(update_fields=['total_amount'])

    def clean(self):
        if self.guest_checkout and self.payment and self.payment.payment_method == 'COD':
            raise ValidationError("Cash on Delivery is not available for guest checkouts.")
        if self.total_amount < 0:
            raise ValidationError("Total amount cannot be negative.")

    class Meta:
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        constraints = [
            UniqueConstraint(
                fields=['order_number'],
                condition=Q(is_deleted=False),
                name='unique_active_order_number'
            )
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ShirtVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_with_tax = models.PositiveIntegerField(default=0)

    @property
    def subtotal(self):
        return self.quantity * self.variant.price

    def save(self, *args, **kwargs):
        if self.price_with_tax != self.variant.price_with_tax:
            self.price_with_tax = self.variant.price_with_tax
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.variant} in Order {self.order.order_number}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('CREDIT_CARD', 'Credit Card'), ('DEBIT_CARD', 'Debit Card'),
        ('UPI', 'UPI'), ('NET_BANKING', 'Net Banking'), ('COD', 'Cash on Delivery'),
    ]
    order = models.OneToOneField(
        'Order', on_delete=models.CASCADE, related_name='payment',
        null=True, blank=True, help_text="Order associated with this payment. May be null until payment verified."
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    amount = models.PositiveIntegerField()
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    status = models.CharField(max_length=20, choices=[('SUCCESS', 'Success'), ('FAILED', 'Failed'), ('PENDING', 'Pending')], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.order:
            return f"Payment for Order {self.order.order_number} - {self.status}"
        ref = self.razorpay_payment_id or self.razorpay_order_id or self.transaction_id or f"ID {self.id}"
        return f"Payment {ref} - {self.status}"


class ShippingMethod(models.Model):
    name = models.CharField(max_length=100, help_text="Name of the shipping courier or method (e.g., Shiprocket Express)")
    price = models.PositiveIntegerField(help_text="Base price for shipping in INR")
    estimated_delivery_days = models.PositiveIntegerField(help_text="Estimated delivery time in days")
    is_active = models.BooleanField(default=True, help_text="Whether this shipping method is currently available")

    def __str__(self):
        return f"{self.name} - ₹{self.price}"

    class Meta:
        indexes = [models.Index(fields=['name', 'is_active']), ]
        verbose_name = "Shipping Method"
        verbose_name_plural = "Shipping Methods"


class OrderShipping(models.Model):
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='shipping',
        help_text="The order associated with this shipping record."
    )
    shipping_method = models.ForeignKey(
        ShippingMethod, on_delete=models.CASCADE,
        help_text="The shipping method used for this order."
    )
    shipping_cost = models.PositiveIntegerField(help_text="Actual shipping cost charged for the order in INR.")
    estimated_delivery_days = models.PositiveIntegerField(help_text="Estimated number of days for delivery.", )
    tracking_number = models.CharField(max_length=100, blank=True, null=True, help_text="Tracking number for the shipment, if available.")
    shipped_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the order was shipped.")

    def __str__(self):
        return f"Shipping for Order {self.order.order_number}"

    def clean(self):
        if self.shipping_cost < 0:
            raise ValidationError("Shipping cost cannot be negative.")
        if self.estimated_delivery_days <= 0:
            raise ValidationError("Estimated delivery days must be positive.")

    class Meta:
        verbose_name = "Order Shipping"
        verbose_name_plural = "Order Shippings"


class SupportTicket(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    STATUS_CHOICES = [('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('RESOLVED', 'Resolved'), ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True,
        related_name='tickets', help_text="Leave blank for anonymous users."
    )
    ticket_id = models.CharField(max_length=20, editable=False, default=None)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['ticket_id'],
                condition=Q(is_deleted=False),
                name='unique_active_ticket_id'
            )
        ]

    def __str__(self):
        identifier = self.user.username if self.user else 'Anonymous'
        return f"Ticket {self.ticket_id} - {identifier}"

    def generate_ticket_id(self):
        prefix = "SUP"
        date_str = timezone.now().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:6].upper()
        ticket_id = f"{prefix}-{date_str}-{unique_id}"

        while SupportTicket.objects.filter(ticket_id=ticket_id).exists():
            unique_id = uuid.uuid4().hex[:6].upper()
            ticket_id = f"{prefix}-{date_str}-{unique_id}"

        return ticket_id

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.pk and not self.ticket_id:
                self.ticket_id = self.generate_ticket_id()
            super().save(*args, **kwargs)


class LoginAttempt(models.Model):
    ip_address = models.GenericIPAddressField(help_text="Client IP address for tracking attempts.")
    email = models.EmailField(max_length=254, help_text="Email used in the login attempt.")
    successful = models.BooleanField(default=False, help_text="Whether the login attempt was successful.")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="When the login attempt occurred.")

    class Meta:
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['email', 'timestamp']),
        ]
        verbose_name = "Login Attempt"
        verbose_name_plural = "Login Attempts"

    def __str__(self):
        return f"Login attempt for {self.email} from {self.ip_address} - {'Success' if self.successful else 'Failed'}"

    @classmethod
    def is_rate_limited(cls, ip_address, max_attempts=10, window_minutes=60):
        # Check for rate limiting based on IP.
        cutoff_time = timezone.now() - timezone.timedelta(minutes=window_minutes)
        attempt_count = cls.objects.filter(ip_address=ip_address, timestamp__gte=cutoff_time).count()
        return attempt_count >= max_attempts

    @classmethod
    def log_attempt(cls, ip_address, email, successful=False):
        cls.objects.create(ip_address=ip_address, email=email, successful=successful)


class BrowsingHistory(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='browsing_history', help_text="The authenticated user who viewed the product."
    )
    variant = models.ForeignKey(
        ShirtVariant, on_delete=models.CASCADE,
        related_name='browsing_history', help_text="The specific shirt variant viewed by the user."
    )
    viewed_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the variant was viewed.")
    view_count = models.PositiveIntegerField(default=1, help_text="Number of times this variant was viewed by the user.")

    class Meta:
        unique_together = [('user', 'variant')]
        indexes = [
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['variant', 'viewed_at']),
        ]
        verbose_name = "Browsing History"
        verbose_name_plural = "Browsing Histories"

    def __str__(self):
        return f"{self.user.username} viewed {self.variant} ({self.view_count}x)"


class CancellationRequest(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    STATUS_CHOICES = [('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ]
    REFUND_STATUS_CHOICES = [('NA', 'Not Applicable'), ('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed'), ]
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='cancellation_requests', help_text="The order to be cancelled."
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        blank=True, help_text="Authenticated user requesting cancellation. Null for guest."
    )
    guest_email = models.EmailField(
        max_length=254, null=True, blank=True,
        help_text="Email for guest users requesting cancellation."
    )
    reason = models.TextField(help_text="Reason for cancellation.")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='PENDING', help_text="Status of the cancellation request."
    )
    refund_status = models.CharField(
        max_length=20, choices=REFUND_STATUS_CHOICES,
        default='NA', help_text="Status of the refund for this cancellation."
    )
    refund_id = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="Unique ID for the refund transaction from the payment gateway."
    )
    admin_notes = models.TextField(blank=True, null=True, help_text="Notes from admin for approval/rejection.")
    requested_at = models.DateTimeField(auto_now_add=True, help_text="When the cancellation was requested.")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        identifier = self.user.username if self.user else self.guest_email or 'Anonymous'
        return f"Cancellation Request for Order {self.order.order_number} - {identifier} - {self.status}"

    def clean(self):
        if self.order.status not in ['PENDING', 'PROCESSING']:
            raise ValidationError("Order is not eligible for cancellation.")

    class Meta:
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['requested_at']),
        ]
        verbose_name = "Cancellation Request"
        verbose_name_plural = "Cancellation Requests"


class ReturnRequest(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'), ('COMPLETED', 'Completed'),
    ]
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='return_requests', help_text="Order associated with the return."
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Authenticated user requesting return.")
    reason = models.TextField(help_text="Reason for return.")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='PENDING', help_text="Status of the return request."
    )
    admin_notes = models.TextField(blank=True, null=True, help_text="Notes from admin for approval/rejection.")
    requested_at = models.DateTimeField(auto_now_add=True, help_text="When the return was requested.")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return Request for Order {self.order.order_number} - {self.user.username} - {self.status}"

    def clean(self):
        if self.order.status != 'DELIVERED':
            raise ValidationError("Order must be delivered to request a return.")
        if not self.order.is_within_return_period:
            raise ValidationError("Return window has expired.")

    class Meta:
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['requested_at']),
        ]
        verbose_name = "Return Request"
        verbose_name_plural = "Return Requests"


class ReturnRequestImage(models.Model):
    return_request = models.ForeignKey('ReturnRequest', on_delete=models.CASCADE, related_name='images')
    image = models.FileField(upload_to='returns', help_text="Image file for the return request.")

    def __str__(self):
        return f"Image for Return Request {self.return_request.id}"


class BulkOrderRequest(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ]

    full_name = models.CharField(max_length=100, null=False, blank=False)
    contact_method = models.CharField(max_length=20, choices=[('email', 'Email'), ('phone', 'Phone Call'), ('whatsapp', 'WhatsApp')], default='email')
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.CharField(max_length=10, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    ticket_id = models.CharField(max_length=20, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['created_at', 'status']), ]
        verbose_name = "Bulk Order Request"
        verbose_name_plural = "Bulk Order Requests"
        constraints = [
            UniqueConstraint(
                fields=['ticket_id'],
                condition=Q(is_deleted=False),
                name='unique_active_bulk_ticket_id'
            )
        ]

    def __str__(self):
        return f"Bulk Order {self.ticket_id} - {self.full_name}"

    def generate_ticket_id(self):
        prefix = "BULK"
        date_str = timezone.now().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:6].upper()
        ticket_id = f"{prefix}-{date_str}-{unique_id}"

        while BulkOrderRequest.objects.filter(ticket_id=ticket_id).exists():
            unique_id = uuid.uuid4().hex[:6].upper()
            ticket_id = f"{prefix}-{date_str}-{unique_id}"

        return ticket_id

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.ticket_id:
                self.ticket_id = self.generate_ticket_id()
            super().save(*args, **kwargs)


class Coupon(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    DISCOUNT_TYPES = [
        ('PERCENTAGE', 'Percentage'), ('FIXED', 'Fixed Amount'),
        ('FREE_SHIPPING', 'Free Shipping'), ('BOGO', 'Buy One Get One'),
    ]

    code = models.CharField(max_length=50, help_text="Unique coupon code")
    description = models.TextField(blank=True, help_text="Description of the coupon")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='PERCENTAGE')
    discount_value = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Discount amount in INR for FIXED, percentage for PERCENTAGE"
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(
        null=True, blank=True, help_text="Maximum total uses (null for unlimited)"
    )
    max_uses_per_user = models.PositiveIntegerField(
        null=True, blank=True, help_text="Maximum uses per user (null for unlimited)"
    )
    min_order_value = models.PositiveIntegerField(
        null=True, blank=True, help_text="Minimum order value in INR to apply coupon"
    )
    applies_to_all = models.BooleanField(default=True, help_text="If true, applies to all products")
    products = models.ManyToManyField(
        'Shirt', blank=True, related_name='coupons',
        help_text="Specific products this coupon applies to"
    )
    categories = models.ManyToManyField(
        'ShirtType', blank=True, related_name='coupons',
        help_text="Specific shirt types this coupon applies to"
    )
    users = models.ManyToManyField(
        'auth.User', blank=True, related_name='coupons',
        help_text="Specific users this coupon applies to (null for all users)"
    )
    can_stack = models.BooleanField(default=False, help_text="Can this coupon be combined with other coupons?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
        constraints = [
            UniqueConstraint(
                fields=['code'], 
                condition=Q(is_deleted=False), 
                name='unique_active_coupon_code'
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.discount_type} ({self.discount_value})"

    def is_valid(self, user=None, order_total=0, products=None):
        # Validate coupon against all rules (dates, usage, products, user).
        from .redis_utils import get_coupon_usage_counts
        try:
            now = timezone.now()
            if not self.is_active:
                return False, "Coupon is inactive"
            if self.valid_from and self.valid_from > now:
                return False, "Coupon is not yet valid"
            if self.valid_until and self.valid_until < now:
                return False, "Coupon has expired"
            if getattr(self, 'min_order_value', None) and order_total < self.min_order_value:
                return False, f"Order total must be at least ₹{self.min_order_value}"

            if not getattr(self, 'applies_to_all', True):
                if products:
                    valid_products = set(self.products.all())
                    valid_products |= set(Shirt.objects.filter(s_type__in=self.categories.all()))
                    if not any(p in valid_products for p in products):
                        return False, "Coupon does not apply to any products in the cart"
                else:
                    return False, "No products provided to validate coupon"

            if self.users.exists() and user and user not in self.users.all():
                return False, "Coupon not applicable to this user"

            if getattr(self, 'max_uses', None) or (getattr(self, 'max_uses_per_user', None) and user):
                counts = get_coupon_usage_counts(self.code, user.id if user else None)
                total_uses = counts.get('total', 0)
                user_uses = counts.get('user', 0)
                if getattr(self, 'max_uses', None) and total_uses >= self.max_uses:
                    return False, "Coupon has reached maximum usage limit"
                if getattr(self, 'max_uses_per_user', None) and user and user_uses >= self.max_uses_per_user:
                    return False, "You have reached the maximum usage limit for this coupon"

            return True, "Coupon is valid"
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Coupon.is_valid error for %s: %s", getattr(self, 'code', None), e)
            return False, "Coupon validation failed"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coupon_usages', help_text="User who used the coupon (null for guest)"
    )
    order = models.ForeignKey(
        'Order', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coupon_usages', help_text="Order where coupon was applied"
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    discount_amount = models.PositiveIntegerField(help_text="Discount amount applied in INR")

    class Meta:
        indexes = [
            models.Index(fields=['coupon', 'user']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"{self.coupon.code} used by {self.user or 'Guest'} on {self.applied_at}"


class Invoice(SoftDeleteModel):
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled'), ('RETURNED', 'Returned'),
    ]

    supplier_name = models.CharField(max_length=200,  help_text="Legal name of the supplier")
    supplier_address = models.TextField( help_text="Complete address of the supplier ")
    supplier_gstin = models.CharField(max_length=15,  help_text="GSTIN of the supplier ")
    supplier_state_code = models.CharField(max_length=2, default="27", help_text="State code of the supplier ")

    invoice_number = models.CharField(max_length=16, editable=False, help_text="Unique invoice number for the financial year (e.g., INV-2025-12345)")
    date_of_issue = models.DateField(default=timezone.now, help_text="Date of invoice issuance")
    financial_year = models.CharField(max_length=9, editable=False, help_text="Financial year of the invoice (e.g., 2025-26)")

    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='invoice', help_text="Associated order for this invoice")
    recipient_name = models.CharField(max_length=200, help_text="Name of the recipient (from user or guest checkout)")
    recipient_gstin = models.CharField(max_length=15, null=True, blank=True, help_text="GSTIN or UIN of the recipient, if registered")
    recipient_address = models.TextField(help_text="Billing address of the recipient")
    recipient_state_code = models.CharField(max_length=2, help_text="State code of the recipient (e.g., 27 for Maharashtra)")

    place_of_supply_code = models.CharField(max_length=2, help_text="State code for place of supply")
    is_inter_state = models.BooleanField(default=False, help_text="True if the supply is inter-state (IGST applies)")

    total_taxable_value = models.PositiveIntegerField(help_text="Total taxable value of goods before taxes in INR")
    cgst_rate = models.PositiveIntegerField(default=0)
    cgst_amount = models.PositiveIntegerField(default=0, help_text="CGST amount charged in INR")
    sgst_rate = models.PositiveIntegerField(default=0)
    sgst_amount = models.PositiveIntegerField(default=0, help_text="SGST amount charged in INR")
    igst_rate = models.PositiveIntegerField(default=0)
    igst_amount = models.PositiveIntegerField(default=0, help_text="IGST amount charged in INR")
    total_amount = models.PositiveIntegerField(help_text="Total invoice amount including taxes, discounts, and shipping in INR")
    reverse_charge = models.BooleanField(default=False, editable=False, help_text="Reverse charge is always False")

    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', help_text="Status of the associated order")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['financial_year', 'invoice_number']),
            models.Index(fields=['order']),
        ]
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        constraints = [
            UniqueConstraint(
                fields=['invoice_number', 'financial_year'],
                condition=Q(is_deleted=False),
                name='unique_active_invoice_number'
            )
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number} for Order {self.order.order_number}"

    def generate_invoice_number(self):
        # Generate a unique invoice number for the financial year.
        current_date = timezone.now().date()
        financial_year = self.get_financial_year(current_date)
        prefix = f"INV-{financial_year[:4]}"
        sequence = 1
        invoice_number = f"{prefix}-{sequence:05d}"

        while Invoice.objects.filter(invoice_number=invoice_number, financial_year=financial_year).exists():
            sequence += 1
            invoice_number = f"{prefix}-{sequence:05d}"
            if len(invoice_number) > 16:
                raise ValidationError("Invoice number exceeds 16 characters")

        return invoice_number, financial_year

    def get_financial_year(self, date):
        year = date.year
        month = date.month
        if month >= 4:
            return f"{year}-{year + 1}"
        return f"{year - 1}-{year}"

    def calculate_tax_details(self):
        # Calculate taxes based on items and inter-state status.
        items = self.order.items.all()
        total_taxable_value = 0
        cgst_amount = 0
        sgst_amount = 0
        igst_amount = 0

        for item in items:
            variant = item.variant
            quantity = item.quantity
            base_price = variant.price
            total_taxable_value += base_price * quantity

            tax_rate = 5 if base_price <= 2500 else 18

            if self.is_inter_state:
                igst_amount += (base_price * quantity * tax_rate + 99) // 100
            else:
                cgst_rate = tax_rate / 2
                sgst_rate = tax_rate / 2
                cgst_amount += (base_price * quantity * cgst_rate + 99) // 100
                sgst_amount += (base_price * quantity * sgst_rate + 99) // 100

        return total_taxable_value, cgst_amount, sgst_amount, igst_amount

    def save(self, *args, **kwargs):
        with transaction.atomic():
        # Populate invoice details from order, calculate taxes, and set totals.
            if not self.invoice_number:
                self.invoice_number, self.financial_year = self.generate_invoice_number()

            shipping_details = self.order.shipping_address_details
            if shipping_details:
                self.recipient_name = shipping_details['recipient']
                self.recipient_address = (
                    f"{shipping_details['address_line']}, {shipping_details['city']}, "
                    f"{shipping_details['state']} - {shipping_details['zip_code']}"
                )
                self.recipient_state_code = [
                    code for code, name in Address.INDIAN_STATES
                    if name == shipping_details['state']
                ][0]
                self.place_of_supply_code = self.recipient_state_code
                self.is_inter_state = self.supplier_state_code != self.recipient_state_code

            (
                self.total_taxable_value, self.cgst_amount,
                self.sgst_amount, self.igst_amount,
            ) = self.calculate_tax_details()
            self.cgst_rate = 2.5 if not self.is_inter_state and self.total_taxable_value <= 2500 else 9 if not self.is_inter_state else 0
            self.sgst_rate = self.cgst_rate
            self.igst_rate = 5 if self.is_inter_state and self.total_taxable_value <= 2500 else 18 if self.is_inter_state else 0

            discount = self.order.discount_amount or 0
            shipping_cost = self.order.shipping.shipping_cost if hasattr(self.order, 'shipping') and self.order.shipping else 0
            self.total_amount = self.total_taxable_value + self.cgst_amount + self.sgst_amount + self.igst_amount - discount + shipping_cost

            super().save(*args, **kwargs)

    def clean(self):
        if len(self.supplier_gstin) != 15:
            raise ValidationError("Supplier GSTIN must be 15 characters")
        if self.recipient_gstin and len(self.recipient_gstin) != 15:
            raise ValidationError("Recipient GSTIN must be 15 characters")
        if self.total_amount < 0:
            raise ValidationError("Total invoice amount cannot be negative")
        if len(self.invoice_number) > 16:
            raise ValidationError("Invoice number exceeds 16 characters")
        if self.order_status not in [choice[0] for choice in self.STATUS_CHOICES]:
            raise ValidationError("Invalid order status")


class InvoiceItem(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='items', help_text="Associated invoice")
    order_item = models.OneToOneField('OrderItem', on_delete=models.CASCADE, help_text="Associated order item")
    hsn_code = models.CharField(max_length=10, help_text="HSN code of the goods (e.g., 6205 for shirts)")
    description = models.TextField(help_text="Description of goods (e.g., Men's Cotton Shirt)")
    quantity = models.PositiveIntegerField(help_text="Quantity of goods")
    unit = models.CharField(max_length=10, default='NOS', help_text="Unit of measurement (e.g., NOS for numbers)")
    unit_price = models.PositiveIntegerField(help_text="Unit price before tax in INR")
    discount = models.PositiveIntegerField(default=0, help_text="Discount applied to this item in INR, if any")
    taxable_value = models.PositiveIntegerField(help_text="Taxable value after discount in INR")
    cgst_rate = models.PositiveIntegerField(default=0)
    cgst_amount = models.PositiveIntegerField(default=0, help_text="CGST amount charged in INR")
    sgst_rate = models.PositiveIntegerField(default=0)
    sgst_amount = models.PositiveIntegerField(default=0, help_text="SGST amount charged in INR")
    igst_rate = models.PositiveIntegerField(default=0)
    igst_amount = models.PositiveIntegerField(default=0, help_text="IGST amount charged in INR")
    total_amount = models.PositiveIntegerField(help_text="Total amount for this item including taxes in INR")

    class Meta:
        indexes = [models.Index(fields=['invoice', 'order_item']), ]
        verbose_name = "Invoice Item"
        verbose_name_plural = "Invoice Items"

    def __str__(self):
        return f"{self.description} in Invoice {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        # Populate item details from OrderItem and calculate item-specific taxes.
        variant = self.order_item.variant
        self.hsn_code = variant.color_variant.shirt.hsn_code
        self.description = (f"{variant.color_variant.shirt.name} ({variant.color_variant.color.name}, {variant.size.name})")
        self.quantity = self.order_item.quantity
        self.unit_price = variant.price

        order_discount = self.invoice.order.discount_amount or 0
        order_taxable_value = sum(item.unit_price * item.quantity for item in self.invoice.items.all() if item.pk != self.pk) + (self.unit_price * self.quantity)
        order_taxable_value = max(1, order_taxable_value) # Avoid division by zero
        
        item_taxable_value = self.unit_price * self.quantity
        
        # Distribute discount proportionally
        self.discount = (item_taxable_value * order_discount + order_taxable_value // 2) // order_taxable_value
        self.taxable_value = item_taxable_value - self.discount

        tax_rate = 5 if self.unit_price <= 2500 else 18
        if self.invoice.is_inter_state:
            self.igst_rate = tax_rate
            self.igst_amount = (self.taxable_value * tax_rate + 99) // 100
            self.cgst_rate = 0
            self.cgst_amount = 0
            self.sgst_rate = 0
            self.sgst_amount = 0
        else:
            self.cgst_rate = tax_rate / 2
            self.sgst_rate = tax_rate / 2
            self.cgst_amount = (self.taxable_value * self.cgst_rate + 99) // 100
            self.sgst_amount = (self.taxable_value * self.sgst_rate + 99) // 100
            self.igst_rate = 0
            self.igst_amount = 0

        self.total_amount = self.taxable_value + self.cgst_amount + self.sgst_amount + self.igst_amount

        super().save(*args, **kwargs)

    def clean(self):
        if self.quantity <= 0: raise ValidationError("Quantity must be positive")
        if self.unit_price < 0: raise ValidationError("Unit price cannot be negative")
        if self.discount < 0: raise ValidationError("Discount cannot be negative")
        if self.taxable_value < 0: raise ValidationError("Taxable value cannot be negative")
        if self.total_amount < 0: raise ValidationError("Total amount cannot be negative")