"""LLM-based web scraper using Firecrawl."""
import os
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..utils.validator import validate_scraped_data
from ..utils.parser import clean_text, extract_price


logger = logging.getLogger(__name__)


class LLMScraper:
    """LLM-based web scraper using Firecrawl API."""
    
    def __init__(self, config: Dict[str, Any], api_key: Optional[str] = None):
        """
        Initialize the LLM scraper.
        
        Args:
            config: Configuration dictionary
            api_key: Firecrawl API key (optional, can be set via env var)
        """
        self.config = config
        self.api_key = api_key or os.getenv('FIRECRAWL_API_KEY')
        
        if not self.api_key:
            logger.warning("Firecrawl API key not set. LLM scraping may fail.")
        
        self.timeout = config.get('scraping', {}).get('timeout', 30)
        self.max_retries = config.get('scraping', {}).get('max_retries', 3)
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape product information using Firecrawl.
        
        Args:
            url: URL to scrape
        
        Returns:
            Dictionary containing scraped product data
        
        Raises:
            Exception: If scraping fails
        """
        logger.info(f"Starting LLM scraping for URL: {url}")
        
        if not self.api_key:
            raise ValueError("Firecrawl API key is required for LLM scraping")
        
        try:
            # Import Firecrawl
            from firecrawl import FirecrawlApp
            
            # Initialize Firecrawl
            app = FirecrawlApp(api_key=self.api_key)
            
            # Define schema for extraction
            schema = {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Product name or title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Product description or details"
                    },
                    "price": {
                        "type": "object",
                        "properties": {
                            "amount": {
                                "type": "number",
                                "description": "Price amount as a number"
                            },
                            "currency": {
                                "type": "string",
                                "description": "Currency code (e.g., GBP, USD)"
                            }
                        }
                    },
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of product ingredients"
                    },
                    "nutrition": {
                        "type": "object",
                        "description": "Nutritional information per serving"
                    },
                    "images": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Product image URLs"
                    }
                },
                "required": ["name"]
            }
            
            # Scrape with extraction
            logger.debug("Calling Firecrawl API...")
            result = app.scrape_url(
                url,
                params={
                    'formats': ['extract'],
                    'extract': {
                        'schema': schema,
                        'systemPrompt': '''You are a web scraping assistant. Extract product information from the webpage.
                        Focus on finding: product name, description, price, ingredients, nutritional information, and images.
                        Be thorough and extract all available information.'''
                    }
                }
            )
            
            # Extract data from result
            product_data = self._process_firecrawl_result(result, url)
            
            # Add metadata
            product_data['metadata'] = {
                'scraped_at': datetime.now().isoformat(),
                'method': 'llm',
                'url': url
            }
            
            # Validate data
            try:
                validated_data = validate_scraped_data(
                    product_data,
                    method='llm',
                    url=url
                )
                logger.info("LLM scraping completed successfully")
                return validated_data
            except Exception as e:
                logger.warning(f"Data validation failed: {e}")
                # Return unvalidated data with warning
                return {'product': product_data}
            
        except ImportError:
            logger.error("Firecrawl library not installed. Install with: pip install firecrawl-py")
            raise Exception("Firecrawl library not installed")
        except Exception as e:
            logger.error(f"LLM scraping failed: {e}")
            raise
    
    def _process_firecrawl_result(self, result: Dict[str, Any], url: str) -> Dict[str, Any]:
        """
        Process Firecrawl API result into product data.
        
        Args:
            result: Firecrawl API result
            url: Source URL
        
        Returns:
            Processed product data dictionary
        """
        # Extract data from Firecrawl result
        if 'extract' in result:
            extracted_data = result['extract']
        elif 'data' in result:
            extracted_data = result['data']
        else:
            extracted_data = result
        
        # Ensure proper structure
        product_data = {
            'name': extracted_data.get('name'),
            'description': extracted_data.get('description'),
            'price': extracted_data.get('price', {'amount': None, 'currency': 'GBP'}),
            'ingredients': extracted_data.get('ingredients', []),
            'nutrition': extracted_data.get('nutrition', {}),
            'images': extracted_data.get('images', [])
        }
        
        # Clean text fields
        if product_data['name']:
            product_data['name'] = clean_text(product_data['name'])
        
        if product_data['description']:
            product_data['description'] = clean_text(product_data['description'])
        
        # Ensure price has correct structure
        if not isinstance(product_data['price'], dict):
            product_data['price'] = {'amount': None, 'currency': 'GBP'}
        
        if 'currency' not in product_data['price']:
            product_data['price']['currency'] = 'GBP'
        
        # Ensure ingredients is a list
        if not isinstance(product_data['ingredients'], list):
            product_data['ingredients'] = []
        
        # Ensure nutrition is a dict
        if not isinstance(product_data['nutrition'], dict):
            product_data['nutrition'] = {}
        
        # Ensure images is a list
        if not isinstance(product_data['images'], list):
            product_data['images'] = []
        
        return product_data
