from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    CustomerProfile, Address, ShirtType, Shirt, Size, Pattern, Material, 
    Color, ColorVariant, ShirtVariant, ShirtMedia, ProductReview, 
    Wishlist, Cart, CartItem, Order, OrderItem, Payment, 
    ShippingMethod, OrderShipping, SupportTicket, 
    GuestCheckout, LoginAttempt,
    BrowsingHistory, ReturnRequest, ReturnRequestImage, BulkOrderRequest, 
    Coupon, CouponUsage, CancellationRequest, InvoiceItem, Invoice
)


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    fields = ('phone_number', 'is_verified')
    verbose_name_plural = 'Customer Profile'

class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ('address_line', 'city', 'state', 'zip_code', 'is_default')

class ShirtVariantInline(admin.TabularInline):
    model = ShirtVariant
    extra = 1
    fields = ('size', 'sku', 'price', 'price_with_tax', 'stock', 'weight', 'is_active')
    readonly_fields = ('price_with_tax',)

class ShirtMediaInline(admin.TabularInline):
    model = ShirtMedia
    extra = 1
    fields = ('media_type', 'media_file', 'is_primary', 'order')

class ColorVariantInline(admin.TabularInline):
    model = ColorVariant
    extra = 1
    fields = ('color', 'seo_data') 

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('variant', 'quantity', 'price_with_tax', 'subtotal')
    readonly_fields = ('subtotal',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('variant', 'quantity', 'price_with_tax', 'subtotal')
    readonly_fields = ('subtotal',)

class OrderShippingInline(admin.StackedInline):
    model = OrderShipping
    can_delete = False
    fields = ('shipping_method', 'tracking_number', 'shipped_at')
    verbose_name_plural = 'Order Shipping'

class PaymentInline(admin.StackedInline):
    model = Payment
    can_delete = False
    fields = ('payment_method', 'amount', 'status', 'transaction_id', 'created_at')
    readonly_fields = ('created_at',)
    verbose_name_plural = 'Payment Details'

class ReturnRequestImageInline(admin.TabularInline):
    model = ReturnRequestImage
    extra = 1
    fields = ('image',)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = ('order_item', 'hsn_code', 'description', 'quantity', 'unit', 'unit_price', 'discount', 'taxable_value', 'cgst_rate', 'cgst_amount', 'sgst_rate', 'sgst_amount', 'igst_rate', 'igst_amount', 'total_amount')
    readonly_fields = ('taxable_value', 'cgst_amount', 'sgst_amount', 'igst_amount', 'total_amount')


# --- ADMIN CLASSES ---

class UserAdmin(BaseUserAdmin):
    inlines = (CustomerProfileInline, AddressInline)

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'is_verified', 'created_at', 'updated_at', 'is_ban')
    list_filter = ('is_verified', 'created_at', 'is_ban')
    search_fields = ('user__username', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_line', 'city', 'state', 'zip_code', 'is_default', 'created_at')
    list_filter = ('state', 'is_default', 'created_at')
    search_fields = ('user__username', 'address_line', 'city', 'zip_code')
    ordering = ('-created_at',)
    list_per_page = 20
    
    fieldsets = (
        (None, {
            'fields': ('user', 'address_line', 'city', 'state', 'zip_code', 'is_default')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ShirtType)
class ShirtTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Shirt)
class ShirtAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 's_type', 'pattern', 'material', 'hsn_code', 'is_active', 'created_at')
    list_filter = ('s_type', 'pattern', 'material', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ColorVariantInline]
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'hex_code')
    search_fields = ('name', 'hex_code')
    ordering = ('name',)

@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ('shirt', 'color')
    list_filter = ('shirt', 'color')
    search_fields = ('shirt__name', 'color__name')
    inlines = [ShirtVariantInline, ShirtMediaInline]
    ordering = ('shirt',)
    # This ensures you can view/edit the JSON SEO data
    fields = ('shirt', 'color', 'seo_data') 

@admin.register(ShirtVariant)
class ShirtVariantAdmin(admin.ModelAdmin):
    list_display = ('sku', 'color_variant', 'size', 'price', 'price_with_tax', 'stock', 'weight', 'is_active')
    list_filter = ('color_variant__shirt', 'size', 'is_active')
    search_fields = ('sku', 'color_variant__shirt__name')
    ordering = ('color_variant__shirt', 'sku')
    readonly_fields = ('price_with_tax', 'sku')
    list_per_page = 20

@admin.register(ShirtMedia)
class ShirtMediaAdmin(admin.ModelAdmin):
    list_display = ('color_variant', 'media_type', 'media_file', 'is_primary', 'order')
    list_filter = ('media_type', 'is_primary')
    search_fields = ('color_variant__shirt__name', 'media_file')
    ordering = ('color_variant', 'order')

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('shirt', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('shirt__name', 'user__username', 'review_text')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'variant', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'variant__color_variant__shirt__name', 'variant__sku')
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'total_price', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'session_key')
    inlines = [CartItemInline]
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'variant', 'quantity', 'price_with_tax', 'subtotal')
    list_filter = ('cart__user',)
    search_fields = ('cart__user__username', 'variant__sku')
    ordering = ('cart',)
    readonly_fields = ('subtotal', 'price_with_tax')

@admin.register(GuestCheckout)
class GuestCheckoutAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'city', 'state', 'pincode', 'created_at')
    list_filter = ('state', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'pincode')
    ordering = ('-created_at',)
    readonly_fields = ('ip_address', 'created_at')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'guest_checkout', 'total_amount', 'status', 'payment_status', 'verification_status', 'shipping_address_summary', 'created_at')
    list_filter = ('status', 'payment_status', 'verification_status', 'created_at')
    search_fields = ('order_number', 'user__username', 'guest_checkout__email')
    inlines = [OrderItemInline, OrderShippingInline, PaymentInline]
    ordering = ('-created_at',)
    list_per_page = 20
    
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'discount_amount', 'shipping_address_summary')
    
    fieldsets = (
        (None, {
            'fields': ('order_number', 'user', 'guest_checkout', 'cart', 'coupon', 'discount_amount', 'total_amount', 'shipping_address')
        }),
        ('Status', {
            'fields': ('status', 'payment_status', 'verification_status')
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_address_summary',
                'shipping_address_line',
                'shipping_city',
                'shipping_state',
                'shipping_zip_code',
                'shipping_phone_number',
                'shipping_email',
                'shipping_recipient'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )

    def shipping_address_summary(self, obj):
        address_details = obj.shipping_address_details
        if address_details:
            return (f"{address_details['recipient']}, {address_details['address_line']}, "
                    f"{address_details['city']}, {address_details['state']} {address_details['zip_code']}, "
                    f"Phone: {address_details['phone_number']}, Email: {address_details['email']}")
        return "No address available"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'variant', 'quantity', 'price_with_tax', 'subtotal')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'variant__sku')
    ordering = ('order',)
    readonly_fields = ('subtotal', 'price_with_tax')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_number', 'status', 'amount', 'payment_method', 'created_at')
    search_fields = ('razorpay_payment_id', 'razorpay_order_id', 'transaction_id', 'order__order_number')
    list_filter = ('status', 'payment_method', 'created_at')

    def order_number(self, obj):
        return obj.order.order_number if obj.order_id else '—'
    order_number.short_description = 'Order'
    order_number.admin_order_field = 'order__order_number'

@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'estimated_delivery_days', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(OrderShipping)
class OrderShippingAdmin(admin.ModelAdmin):
    list_display = ('order', 'shipping_method', 'tracking_number', 'shipped_at')
    list_filter = ('shipping_method', 'shipped_at')
    search_fields = ('order__order_number', 'tracking_number')
    ordering = ('-shipped_at',)

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('ticket_id', 'user__username', 'subject')
    ordering = ('-created_at',)
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'ip_address', 'successful', 'timestamp')
    list_filter = ('successful', 'timestamp')
    search_fields = ('email', 'ip_address')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

@admin.register(BrowsingHistory)
class BrowsingHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'variant', 'viewed_at', 'view_count')
    list_filter = ('viewed_at',)
    search_fields = ('user__username', 'variant__color_variant__shirt__name', 'variant__sku')
    ordering = ('-viewed_at',)
    readonly_fields = ('viewed_at',)

@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'guest_email', 'status', 'requested_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('order__order_number', 'user__username', 'guest_email', 'reason')
    ordering = ('-requested_at',)
    readonly_fields = ('requested_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('order', 'user', 'guest_email', 'reason', 'status', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'status', 'requested_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('order__order_number', 'user__username', 'reason')
    ordering = ('-requested_at',)
    readonly_fields = ('requested_at', 'updated_at')
    inlines = [ReturnRequestImageInline]
    fieldsets = (
        (None, {
            'fields': ('order', 'user', 'reason', 'status', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ReturnRequestImage)
class ReturnRequestImageAdmin(admin.ModelAdmin):
    list_display = ('return_request', 'image')
    list_filter = ('return_request',)
    search_fields = ('return_request__order__order_number',)
    ordering = ('return_request',)

@admin.register(BulkOrderRequest)
class BulkOrderRequestAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'full_name', 'contact_method', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status', 'contact_method', 'created_at')
    search_fields = ('ticket_id', 'full_name', 'email', 'phone', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'valid_from', 'valid_until', 'applies_to_all')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('code', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'discount_type', 'discount_value', 'is_active')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Usage Restrictions', {
            'fields': ('max_uses', 'max_uses_per_user', 'min_order_value')
        }),
        ('Applicability', {
            'fields': ('applies_to_all', 'products', 'categories', 'users')
        }),
        ('Stacking', {
            'fields': ('can_stack',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'order', 'discount_amount', 'applied_at')
    list_filter = ('coupon', 'applied_at')
    search_fields = ('coupon__code', 'user__username', 'order__order_number')
    ordering = ('-applied_at',)
    readonly_fields = ('applied_at',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'order', 'recipient_name', 'total_taxable_value', 'cgst_amount', 'sgst_amount', 'igst_amount', 'total_amount', 'order_status', 'date_of_issue')
    list_filter = ('order_status', 'date_of_issue', 'is_inter_state')
    search_fields = ('invoice_number', 'order__order_number', 'recipient_name', 'recipient_gstin')
    inlines = [InvoiceItemInline]
    ordering = ('-date_of_issue',)
    
    readonly_fields = (
        'invoice_number', 'financial_year', 'total_taxable_value', 'cgst_rate', 'cgst_amount',
        'sgst_rate', 'sgst_amount', 'igst_rate', 'igst_amount', 'total_amount', 'created_at', 'updated_at',
        'reverse_charge'
    )
    
    fieldsets = (
        (None, {
            'fields': ('order', 'invoice_number', 'date_of_issue', 'financial_year')
        }),
        ('Supplier Details', {
            'fields': ('supplier_name', 'supplier_address', 'supplier_gstin', 'supplier_state_code')
        }),
        ('Recipient Details', {
            'fields': ('recipient_name', 'recipient_address', 'recipient_state_code', 'recipient_gstin')
        }),
        ('Tax Details', {
            'fields': (
                'total_taxable_value', 'cgst_rate', 'cgst_amount', 'sgst_rate', 'sgst_amount',
                'igst_rate', 'igst_amount', 'total_amount', 'reverse_charge', 'is_inter_state'
            )
        }),
        ('Place of Supply', {
            'fields': ('place_of_supply_code',)
        }),
        ('Status', {
            'fields': ('order_status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 20

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'hsn_code', 'quantity', 'unit_price', 'taxable_value', 'total_amount')
    list_filter = ('invoice__order_status',)
    search_fields = ('invoice__invoice_number', 'order_item__variant__sku', 'description', 'hsn_code')
    ordering = ('invoice',)
    readonly_fields = (
        'taxable_value', 'cgst_rate', 'cgst_amount', 'sgst_rate', 'sgst_amount',
        'igst_rate', 'igst_amount', 'total_amount'
    )
    fieldsets = (
        (None, {
            'fields': ('invoice', 'order_item', 'description', 'hsn_code', 'quantity', 'unit', 'unit_price', 'discount')
        }),
        ('Tax Details', {
            'fields': (
                'taxable_value', 'cgst_rate', 'cgst_amount', 'sgst_rate', 'sgst_amount',
                'igst_rate', 'igst_amount', 'total_amount'
            )
        }),
    )
    list_per_page = 20

# Re-register User with customized admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)