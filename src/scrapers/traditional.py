"""Traditional web scraper using BeautifulSoup."""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime

from ..utils.parser import (
    clean_text,
    extract_price,
    parse_ingredients,
    parse_nutrition,
    extract_images
)
from ..utils.validator import validate_scraped_data


logger = logging.getLogger(__name__)


class TraditionalScraper:
    """Traditional web scraper using BeautifulSoup and requests."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the traditional scraper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('scraping', {}).get(
                'user_agent',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
        })
        self.timeout = config.get('scraping', {}).get('timeout', 30)
        self.max_retries = config.get('scraping', {}).get('max_retries', 3)
        self.retry_delay = config.get('scraping', {}).get('retry_delay', 2)
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape product information from the given URL.
        
        Args:
            url: URL to scrape
        
        Returns:
            Dictionary containing scraped product data
        
        Raises:
            Exception: If scraping fails after retries
        """
        logger.info(f"Starting traditional scraping for URL: {url}")
        
        # Fetch HTML content with retries
        html_content = self._fetch_with_retry(url)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract product data
        product_data = self._extract_product_data(soup, url)
        
        # Add metadata
        product_data['metadata'] = {
            'scraped_at': datetime.now().isoformat(),
            'method': 'traditional',
            'url': url
        }
        
        # Validate data
        try:
            validated_data = validate_scraped_data(
                product_data,
                method='traditional',
                url=url
            )
            logger.info("Traditional scraping completed successfully")
            return validated_data
        except Exception as e:
            logger.warning(f"Data validation failed: {e}")
            # Return unvalidated data with warning
            return {'product': product_data}
    
    def _fetch_with_retry(self, url: str) -> str:
        """
        Fetch URL content with retry logic.
        
        Args:
            url: URL to fetch
        
        Returns:
            HTML content as string
        
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetch attempt {attempt + 1}/{self.max_retries}")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        raise Exception(f"Failed to fetch URL after {self.max_retries} attempts: {last_exception}")
    
    def _extract_product_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract product data from BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup parsed HTML
            url: Source URL
        
        Returns:
            Dictionary with product data
        """
        product_data = {
            'name': self._extract_name(soup),
            'description': self._extract_description(soup),
            'price': self._extract_price(soup),
            'ingredients': self._extract_ingredients(soup),
            'nutrition': self._extract_nutrition(soup),
            'images': self._extract_images(soup)
        }
        
        return product_data
    
    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product name."""
        # Try common selectors for product name
        selectors = [
            'h1.product-name',
            'h1.product-title',
            'h1[class*="product"]',
            '.product-detail h1',
            'h1',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                name = clean_text(element.get_text())
                if name:
                    logger.debug(f"Found product name: {name}")
                    return name
        
        logger.warning("Could not find product name")
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product description."""
        # Try common selectors for product description
        selectors = [
            '.product-description',
            '.description',
            '[class*="description"]',
            '.product-detail p',
            'meta[name="description"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    description = element.get('content', '')
                else:
                    description = clean_text(element.get_text())
                
                if description and len(description) > 20:
                    logger.debug(f"Found description: {description[:100]}...")
                    return description
        
        logger.warning("Could not find product description")
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract product price."""
        # Try common selectors for price
        selectors = [
            '.price',
            '.product-price',
            '[class*="price"]',
            'span[itemprop="price"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = clean_text(element.get_text())
                if price_text:
                    price_data = extract_price(price_text)
                    if price_data['amount']:
                        logger.debug(f"Found price: {price_data}")
                        return price_data
        
        logger.warning("Could not find product price")
        return {'amount': None, 'currency': 'GBP'}
    
    def _extract_ingredients(self, soup: BeautifulSoup) -> list:
        """Extract product ingredients."""
        # Try common selectors for ingredients
        selectors = [
            '.ingredients',
            '[class*="ingredient"]',
            '#ingredients',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                ingredients_text = clean_text(element.get_text())
                if ingredients_text:
                    ingredients = parse_ingredients(ingredients_text)
                    if ingredients:
                        logger.debug(f"Found {len(ingredients)} ingredients")
                        return ingredients
        
        logger.warning("Could not find ingredients")
        return []
    
    def _extract_nutrition(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract nutritional information."""
        # Try common selectors for nutrition
        selectors = [
            '.nutrition',
            '.nutritional-information',
            '[class*="nutrition"]',
            '#nutrition',
            'table.nutrition',
        ]
        
        nutrition_data = {}
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Try to extract from table
                if element.name == 'table':
                    nutrition_data = self._parse_nutrition_table(element)
                else:
                    # Parse from text
                    nutrition_text = clean_text(element.get_text())
                    nutrition_data = parse_nutrition(nutrition_text)
                
                if nutrition_data:
                    logger.debug(f"Found nutrition data: {nutrition_data}")
                    return nutrition_data
        
        logger.warning("Could not find nutritional information")
        return {}
    
    def _parse_nutrition_table(self, table) -> Dict[str, Any]:
        """Parse nutrition data from HTML table."""
        nutrition = {}
        
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = clean_text(cells[0].get_text()).lower()
                value = clean_text(cells[1].get_text())
                if key and value:
                    nutrition[key] = value
        
        return nutrition
    
    def _extract_images(self, soup: BeautifulSoup) -> list:
        """Extract product images."""
        images = []
        
        # Try to find product images
        selectors = [
            '.product-image img',
            '.product-gallery img',
            '[class*="product"] img',
            'img[itemprop="image"]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                # Extract base URL from the canonical link or current page
                base_url = ''
                canonical = soup.find('link', {'rel': 'canonical'})
                if canonical and canonical.get('href'):
                    canonical_url = canonical.get('href')
                    # Extract base URL (scheme + domain)
                    from urllib.parse import urlparse
                    parsed = urlparse(canonical_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                
                extracted = extract_images(elements, base_url=base_url)
                if extracted:
                    images.extend(extracted)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        if unique_images:
            logger.debug(f"Found {len(unique_images)} product images")
        else:
            logger.warning("Could not find product images")
        
        return unique_images
