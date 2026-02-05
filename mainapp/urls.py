from django.urls import path
from . import views
from django.contrib.sitemaps.views import sitemap, index
from .sitemaps import StaticViewSitemap, ProductSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
}

urlpatterns = [
    # Core Website URLs
    path('', views.index, name='home'),
    path('explore/', views.explore, name='explore'),
    path('new-arrival/', views.new_arrival, name='new-arrival'),
    path('about/', views.about, name='about'),
    path('terms-and-condition/', views.terms, name='terms-and-condition'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('verify-otp/<str:email>/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('formal/', views.formal, name='formal'),
    path('casual/', views.casual, name='casual'),
    path('occasional/', views.occasional, name='occasional'),
    path('kid/', views.kid, name='kid'),
    path('slimfit/', views.slimfit, name='slimfit'),
    path('sizefaq/', views.sizefaq, name='sizefaq'),
    path('p/<slug:slug>/', views.details, name='product_detail'),
    path('submit-review/<slug:slug>/', views.submit_review, name='submit_review'),
    path('delete-review/<slug:slug>/', views.delete_review, name='delete_review'),
    path('search/', views.search_products, name='search_products'),
    path('forget-password/', views.ForgetPasswordView.as_view(), name='forget_password'),
    path('bulk-order/', views.bulk_order, name='bulk_order'),
    
    # Cart URLs
    path('cart/add/<int:variant_id>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.UpdateCartView.as_view(), name='update_cart'),
    path('cart/remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/data/', views.CartView.as_view(), name='cart_data'),
    path('cart/summary/', views.get_cart_summary, name='cart_summary'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),

    # Checkout URLs
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('checkout/<int:variant_id>/', views.CheckoutView.as_view(), name='checkout_single'),
    path('checkout/prepare/', views.prepare_checkout, name='prepare_checkout'),
    path('order/confirmation/<str:order_number>/', views.OrderConfirmationView.as_view(), name='order_confirmation'),
    path('get_delivery_estimate/', views.get_delivery_estimate, name='get_delivery_estimate'),    
    path('checkout/create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('checkout/verify-razorpay-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),

    # Wishlist URLs
    path('wishlist/add/<int:variant_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:variant_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # API Endpoints
    path('api/search-products/', views.search_products_api, name='search_products_api'),
    path('api/formal-products/', views.formal_products_api, name='formal-products-api'),
    path('api/casual-products/', views.casual_products_api, name='casual-products-api'),
    path('api/kids-products/', views.kids_products_api, name='kids-products-api'),
    path('api/occasional-products/', views.occasional_products_api, name='occasional-products-api'),
    path('api/new-products/', views.new_products_api, name='new-products-api'),
    path('api/slim-products/', views.slim_products_api, name='slim-products-api'),
    path('api/product-reviews/<slug:slug>/', views.product_reviews_api, name='product-reviews-api'),
    path('api/browsing-history/', views.browsing_history_api, name='browsing_history_api'),
    path('api/variant-details/<int:variant_id>/', views.variant_details_api, name='variant_details_api'),
    
    # Dashboard URLs
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/orders/', views.user_orders, name='user_orders'),
    path('dashboard/wishlist/', views.wishlist, name='wishlist'),
    path('dashboard/addresses/', views.addresses, name='addresses'),
    path('dashboard/account-settings/', views.account_settings, name='account_settings'),
    path('verify-email-change/', views.verify_email_change, name='verify_email_change'),
    path('dashboard/reviews/', views.reviews, name='reviews'),
    path('dashboard/support/', views.support, name='support'),
    path('dashboard/logout-all/', views.logout_all, name='logout_all'),
    path('cancel-order/', views.cancel_order, name='cancel_order'),
    path('return-order/', views.return_order, name='return_order'),
    path('invoice/<str:order_number>/', views.invoice_view, name='invoice_view'),
    path('invoice/<str:order_number>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),

# --- SEO INFRASTRUCTURE ---
    
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', index, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.index'),
    path('sitemap-<section>.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]