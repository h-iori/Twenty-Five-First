import meilisearch
from django.conf import settings

class MeiliIndexer:
    """
    Handles converting Django Models -> Meilisearch JSON.
    """
    def __init__(self):
        self.client = meilisearch.Client(settings.MEILISEARCH['HOST'], settings.MEILISEARCH['MASTER_KEY'])
        self.index = self.client.index('products')

    def _prepare_document(self, color_variant):
        """
        Flattens a ColorVariant + Parent Shirt + Variants into a single search document.
        """
        shirt = color_variant.shirt
        # Get active sizes (variants) for this specific color
        variants = color_variant.variants.filter(is_active=True, is_deleted=False)
        
        # 1. Calculate Aggregates (Price, Stock, Sizes)
        if variants.exists():
            # Index the lowest base price (User usually filters by base price)
            min_price = min(v.price for v in variants) 
            total_stock = sum(v.stock for v in variants)
            sizes = [v.size.name for v in variants]
        else:
            min_price = 0
            total_stock = 0
            sizes = []

        # 2. Get Primary Image
        primary_media = color_variant.media.filter(is_primary=True).first()
        # Fallback to first image if no primary is set
        if not primary_media:
            primary_media = color_variant.media.first()
            
        image_url = primary_media.media_file.url if (primary_media and primary_media.media_file) else ""

        # 3. Construct the Document
        return {
            'id': color_variant.id,           # PRIMARY KEY
            'sku': color_variant.slug,        # Human readable ID
            'name': shirt.name,
            'description': shirt.description,
            'slug': color_variant.slug,
            
            # --- Searchable Attributes (Text) ---
            'color': color_variant.color.name,
            'category': shirt.s_type.name,    # ShirtType
            'material': shirt.material.name,
            'pattern': shirt.pattern.name,
            
            # --- Filterable Attributes (Facets) ---
            'price': min_price,
            'total_stock': total_stock,
            'sizes': sizes,                   # Array: ["M", "L", "XL"]
            'is_active': (shirt.is_active and not shirt.is_deleted),
            'created_at': shirt.created_at.timestamp(), # UNIX timestamp for sorting
            
            # --- Display Data ---
            'image': image_url
        }

    def update_document(self, color_variant):
        """Updates or Creates a single document in Meilisearch"""
        if not color_variant:
            return
        
        try:
            # Only index if the parent shirt is active/not deleted
            if color_variant.shirt.is_deleted or not color_variant.shirt.is_active:
                self.delete_document(color_variant.id)
                return

            doc = self._prepare_document(color_variant)
            self.index.add_documents([doc])
        except Exception as e:
            print(f"Error indexing {color_variant}: {e}")

    def delete_document(self, color_variant_id):
        """Removes a document from Meilisearch"""
        try:
            self.index.delete_document(color_variant_id)
        except Exception as e:
            print(f"Error deleting {color_variant_id}: {e}")