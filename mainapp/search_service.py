import meilisearch
from django.conf import settings

class SearchService:
    _client = None
    _index = None

    @classmethod
    def get_index(cls):
        """Lazy load client to prevent startup errors"""
        if not cls._client:
            cls._client = meilisearch.Client(settings.MEILISEARCH['HOST'], settings.MEILISEARCH['MASTER_KEY'])
            cls._index = cls._client.index('products')
        return cls._index

    @staticmethod
    def search_products(params):
        index = SearchService.get_index()
        
        # 1. Base Query
        query_text = params.get('q', '').strip()
        
        # 2. Build Filter Strings
        # Start with base rule: Must be active
        filter_conditions = ["is_active = true"]
        
        # Map Django GET params to Meilisearch Filter Attributes
        if params.get('type') and params.get('type') != 'all':
            filter_conditions.append(f'category = "{params["type"]}"')
            
        if params.get('color') and params.get('color') != 'all':
            filter_conditions.append(f'color = "{params["color"]}"')
            
        if params.get('pattern') and params.get('pattern') != 'all':
            filter_conditions.append(f'pattern = "{params["pattern"]}"')

        if params.get('material') and params.get('material') != 'all':
            filter_conditions.append(f'material = "{params["material"]}"')
            
        if params.get('size') and params.get('size') != 'all':
            filter_conditions.append(f'sizes = "{params["size"]}"')

        # Price Range Logic (Matches your HTML select values)
        price_range = params.get('price', 'all')
        if price_range == '0-500':
            filter_conditions.append('price <= 500')
        elif price_range == '500-1000':
            filter_conditions.append('price > 500 AND price <= 1000')
        elif price_range == '1000+':
            filter_conditions.append('price > 1000')

        # Combine all filters
        filter_query = " AND ".join(filter_conditions)

        # 3. Sorting Logic
        sort_param = params.get('sort', 'relevance')
        sort_config = []
        if sort_param == 'price_low':
            sort_config = ['price:asc']
        elif sort_param == 'price_high':
            sort_config = ['price:desc']
        elif sort_param == 'newest':
            sort_config = ['created_at:desc']

        # 4. Pagination
        page = int(params.get('page', 1))
        # API calls might send page_size, default to 12
        page_size = int(params.get('page_size', 12)) 
        offset = (page - 1) * page_size

        # 5. Execute Search
        search_params = {
            'filter': filter_query,
            'sort': sort_config,
            'limit': page_size,
            'offset': offset,
        }

        # If query is empty, pass empty string (returns all documents sorted by rules)
        return index.search(query_text, search_params)