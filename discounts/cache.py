# ecommerce/cache.py

from django.core.cache import cache
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache keys
DISCOUNT_RULES_CACHE_KEY = 'discount_rules'
CACHE_TTL = getattr(settings, 'CACHE_TTL', 60 * 15)  # 15 minutes default

def get_discount_rules_from_cache():
    """
    Get discount rules from cache or database
    """
    from .models import DiscountRule
    
    # Try to get from cache first
    discount_rules = cache.get(DISCOUNT_RULES_CACHE_KEY)
    
    if discount_rules is None:
        logger.info("Cache miss for discount rules, fetching from database")
        
        # If not in cache, get from database
        discount_rules = list(DiscountRule.objects
                              .filter(is_active=True)
                              .order_by('priority'))
        
        # Store in cache
        cache.set(DISCOUNT_RULES_CACHE_KEY, discount_rules, CACHE_TTL)
    else:
        logger.info("Cache hit for discount rules")
    
    return discount_rules

def invalidate_discount_rules_cache():
    """
    Invalidate the discount rules cache
    """
    logger.info("Invalidating discount rules cache")
    cache.delete(DISCOUNT_RULES_CACHE_KEY)