# mainapp/management/commands/init_search.py
import meilisearch
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Initializes Meilisearch indices with User-Centric ranking rules'

    def handle(self, *args, **options):
        self.stdout.write("Connecting to Meilisearch...")
        
        client = meilisearch.Client(settings.MEILISEARCH['HOST'], settings.MEILISEARCH['MASTER_KEY'])
        
        # 1. Create/Get the Index
        index_name = 'products'
        client.create_index(index_name, {'primaryKey': 'id'})
        index = client.index(index_name)

        # 2. Configure Filterable Attributes (The Sidebar Filters)
        # These are strictly for checkboxes and range sliders.
        filterable_attributes = [
            'is_active',
            'is_deleted',
            'category',     # e.g., "Casual Shirt"
            'pattern',      # e.g., "Checkered"
            'material',     # e.g., "Cotton"
            'color',        # e.g., "Blue"
            'sizes',        # e.g., ["M", "L"]
            'price',        # For "Under ₹500"
            'slug'
        ]
        
        # 3. Configure Sortable Attributes (The "Sort By" Dropdown)
        sortable_attributes = [
            'price',
            'created_at',
            'total_stock',
        ]

        # 4. Configure Searchable Attributes (The "Human Logic" Priority)
        # Meilisearch checks the top field first. 
        # If I search "Blue Cotton", it looks for "Blue" in Color and "Cotton" in Material first.
        searchable_attributes = [
            'name',         # Priority 1: The Product Name (e.g., "Classic Oxford Shirt")
            'color',        # Priority 2: Visuals (e.g., "Navy Blue")
            'category',     # Priority 3: Type (e.g., "Formal")
            'material',     # Priority 4: Fabric (e.g., "Linen")
            'pattern',      # Priority 5: Style (e.g., "Striped")
            'description',  # Priority 6: The long text (lowest priority to reduce noise)
        ]

        # 5. Ranking Rules (Enterprise Tuning)
        # We stick to the defaults, but we ensure "Typo" and "Words" are first
        # to catch "Coton shirt" (typo) or "Shirt Blue" (word order).
        ranking_rules = [
            "words",
            "typo",
            "proximity",
            "attribute",
            "sort",
            "exactness"
        ]

        self.stdout.write("Applying settings... (this may take a few seconds)")

        index.update_settings({
            'filterableAttributes': filterable_attributes,
            'sortableAttributes': sortable_attributes,
            'searchableAttributes': searchable_attributes,
            'rankingRules': ranking_rules,
            
            # Enterprise Tuning:
            # Stop words: Common words that add no value to search.
            'stopWords': ['a', 'an', 'the', 'of', 'in', 'for', 'with', 'is', 'to', 'and'],
            
            # Typo Tolerance: 
            # We allow typos on long words (description), but maybe stricter on short ones?
            # Default is usually fine, but let's be explicit.
            'typoTolerance': {
                'minWordSizeForTypos': {
                    'oneTypo': 4,   # "blue" -> "bloue" (match)
                    'twoTypos': 8   # "polyester" -> "pollester" (match)
                }
            }
        })

        self.stdout.write(self.style.SUCCESS(f"Successfully configured index: {index_name}"))