"""Parser utilities for extracting and formatting scraped data."""
from typing import Any, Dict, List, Optional
import re


def clean_text(text: Optional[str]) -> str:
    """Clean and normalize text by removing extra whitespace."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())


def extract_price(price_text: str) -> Dict[str, Any]:
    """
    Extract price amount and currency from price text.
    
    Args:
        price_text: Raw price text (e.g., "£3.50", "$4.99")
    
    Returns:
        Dictionary with amount and currency
    """
    if not price_text:
        return {"amount": None, "currency": None}
    
    # Remove whitespace
    price_text = price_text.strip()
    
    # Common currency symbols
    currency_map = {
        '£': 'GBP',
        '$': 'USD',
        '€': 'EUR',
        '¥': 'JPY'
    }
    
    # Extract currency symbol
    currency = None
    for symbol, code in currency_map.items():
        if symbol in price_text:
            currency = code
            price_text = price_text.replace(symbol, '')
            break
    
    # If no symbol found, try to find currency code
    if not currency:
        for code in ['GBP', 'USD', 'EUR', 'JPY']:
            if code in price_text.upper():
                currency = code
                price_text = price_text.replace(code, '').replace(code.lower(), '')
                break
    
    # Extract numeric value
    try:
        # Remove any non-numeric characters except decimal point
        amount_str = re.sub(r'[^\d.]', '', price_text)
        amount = float(amount_str) if amount_str else None
    except (ValueError, AttributeError):
        amount = None
    
    return {
        "amount": amount,
        "currency": currency or "GBP"  # Default to GBP
    }


def parse_ingredients(ingredients_text: str) -> List[str]:
    """
    Parse ingredients from text into a list.
    
    Args:
        ingredients_text: Raw ingredients text
    
    Returns:
        List of individual ingredients
    """
    if not ingredients_text:
        return []
    
    # Split by common delimiters
    ingredients = re.split(r'[,;]|\band\b', ingredients_text)
    
    # Clean each ingredient
    return [clean_text(ing) for ing in ingredients if clean_text(ing)]


def parse_nutrition(nutrition_text: str) -> Dict[str, Any]:
    """
    Parse nutrition information from text.
    
    Args:
        nutrition_text: Raw nutrition text
    
    Returns:
        Dictionary with nutrition data
    """
    if not nutrition_text:
        return {}
    
    nutrition = {}
    
    # Common nutrition patterns
    patterns = {
        'energy': r'energy[:\s]+(\d+\.?\d*)\s*(kj|kcal)',
        'fat': r'fat[:\s]+(\d+\.?\d*)\s*g',
        'saturates': r'saturates?[:\s]+(\d+\.?\d*)\s*g',
        'carbohydrates': r'carbohydrate[s]?[:\s]+(\d+\.?\d*)\s*g',
        'sugars': r'sugars?[:\s]+(\d+\.?\d*)\s*g',
        'fibre': r'fibre[:\s]+(\d+\.?\d*)\s*g',
        'protein': r'protein[:\s]+(\d+\.?\d*)\s*g',
        'salt': r'salt[:\s]+(\d+\.?\d*)\s*g',
    }
    
    text_lower = nutrition_text.lower()
    for key, pattern in patterns.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
                unit = match.group(2) if len(match.groups()) > 1 else 'g'
                nutrition[key] = f"{value}{unit}"
            except (ValueError, IndexError):
                pass
    
    return nutrition


def extract_images(image_elements: List[Any], base_url: str = '') -> List[str]:
    """
    Extract image URLs from image elements.
    
    Args:
        image_elements: List of image elements or URLs
        base_url: Base URL for resolving relative paths (optional)
    
    Returns:
        List of image URLs
    """
    images = []
    
    for img in image_elements:
        if isinstance(img, str):
            # Already a URL
            if img.startswith('http'):
                images.append(img)
        elif hasattr(img, 'get'):
            # BeautifulSoup element
            src = img.get('src') or img.get('data-src')
            if src:
                # Make absolute URL if needed
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/') and base_url:
                    # Use base_url if provided, otherwise try to construct from context
                    src = base_url.rstrip('/') + src
                if src.startswith('http'):
                    images.append(src)
    
    return images
