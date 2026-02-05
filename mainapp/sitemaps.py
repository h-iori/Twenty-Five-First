from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import ColorVariant

class StaticViewSitemap(Sitemap):
    """
    Explicitly lists ONLY high-value static pages.
    Excludes: Login, Dashboard, Cart, Search, Actions.
    """
    priority = 0.6
    changefreq = 'weekly'
    protocol = 'https'  

    def items(self):
        return [
            'home',
            'about',
            'contact',
            'explore',
            'new-arrival',
            'formal',
            'casual',
            'occasional',
            'kid',
            'slimfit',
            'sizefaq',
            'terms-and-condition',
            'privacy',
            'bulk_order', 
        ]

    def location(self, item):
        return reverse(item)

class ProductSitemap(Sitemap):
    """
    The Product Feed.
    Optimized for DB performance using select_related.
    """
    priority = 1.0  
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        return ColorVariant.objects.filter(
            shirt__is_active=True,
            shirt__is_deleted=False,
            slug__isnull=False
        ).select_related('shirt', 'color').order_by('-shirt__updated_at')

    def lastmod(self, obj):
        return obj.shirt.updated_at

    def location(self, obj):
        return obj.get_absolute_url()