"""Tests for web scrapers."""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scrapers.traditional import TraditionalScraper
from scrapers.llm_based import LLMScraper
from utils.parser import clean_text, extract_price, parse_ingredients
from utils.validator import validate_scraped_data, is_valid_url


@pytest.fixture
def config():
    """Test configuration."""
    return {
        'scraping': {
            'user_agent': 'TestAgent/1.0',
            'timeout': 10,
            'max_retries': 2,
            'retry_delay': 1
        }
    }


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <html>
        <head>
            <title>Test Product</title>
        </head>
        <body>
            <h1>Flora Plant Unsalted</h1>
            <div class="description">
                A delicious plant-based spread made with plant oils.
            </div>
            <span class="price">£3.50</span>
            <div class="ingredients">
                Plant oils (rapeseed, palm, sunflower), water, salt
            </div>
            <div class="nutrition">
                Energy: 615kJ, Fat: 70g, Saturates: 20g, Carbohydrates: 1g
            </div>
            <img class="product-image" src="/images/flora-unsalted.jpg" alt="Product">
        </body>
    </html>
    """


class TestUtils:
    """Test utility functions."""
    
    def test_clean_text(self):
        """Test text cleaning."""
        assert clean_text("  Hello   World  ") == "Hello World"
        assert clean_text("\n\tTest\n") == "Test"
        assert clean_text(None) == ""
    
    def test_extract_price(self):
        """Test price extraction."""
        # GBP
        price = extract_price("£3.50")
        assert price['amount'] == 3.50
        assert price['currency'] == 'GBP'
        
        # USD
        price = extract_price("$4.99")
        assert price['amount'] == 4.99
        assert price['currency'] == 'USD'
        
        # EUR
        price = extract_price("€5.00")
        assert price['amount'] == 5.00
        assert price['currency'] == 'EUR'
        
        # No currency
        price = extract_price("")
        assert price['amount'] is None
    
    def test_parse_ingredients(self):
        """Test ingredient parsing."""
        text = "Water, Plant oils, Salt, Vitamin A"
        ingredients = parse_ingredients(text)
        assert len(ingredients) == 4
        assert "Water" in ingredients
        assert "Salt" in ingredients
    
    def test_is_valid_url(self):
        """Test URL validation."""
        assert is_valid_url("https://www.example.com") is True
        assert is_valid_url("http://localhost:8000") is True
        assert is_valid_url("not-a-url") is False
        assert is_valid_url("ftp://example.com") is False


class TestTraditionalScraper:
    """Test traditional scraper."""
    
    def test_init(self, config):
        """Test scraper initialization."""
        scraper = TraditionalScraper(config)
        assert scraper.timeout == 10
        assert scraper.max_retries == 2
    
    @patch('scrapers.traditional.requests.Session.get')
    def test_fetch_with_retry_success(self, mock_get, config):
        """Test successful fetch."""
        mock_response = Mock()
        mock_response.text = "<html>Test</html>"
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        scraper = TraditionalScraper(config)
        html = scraper._fetch_with_retry("https://example.com")
        
        assert html == "<html>Test</html>"
        assert mock_get.call_count == 1
    
    @patch('scrapers.traditional.requests.Session.get')
    def test_fetch_with_retry_failure(self, mock_get, config):
        """Test fetch with all retries failing."""
        mock_get.side_effect = Exception("Network error")
        
        scraper = TraditionalScraper(config)
        
        with pytest.raises(Exception, match="Failed to fetch URL"):
            scraper._fetch_with_retry("https://example.com")
        
        assert mock_get.call_count == 2  # max_retries = 2
    
    @patch('scrapers.traditional.requests.Session.get')
    def test_scrape_product(self, mock_get, config, sample_html):
        """Test scraping product data."""
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        scraper = TraditionalScraper(config)
        result = scraper.scrape("https://example.com/product")
        
        assert 'product' in result
        product = result['product']
        
        # Check metadata
        assert product['metadata']['method'] == 'traditional'
        assert product['metadata']['url'] == "https://example.com/product"
        
        # Check extracted data
        assert product['name'] == "Flora Plant Unsalted"
        assert 'plant' in product['description'].lower()
        assert product['price']['amount'] == 3.50
        assert product['price']['currency'] == 'GBP'


class TestLLMScraper:
    """Test LLM-based scraper."""
    
    def test_init_with_api_key(self, config):
        """Test scraper initialization with API key."""
        scraper = LLMScraper(config, api_key="test-key")
        assert scraper.api_key == "test-key"
    
    def test_init_without_api_key(self, config):
        """Test scraper initialization without API key."""
        with patch.dict('os.environ', {}, clear=True):
            scraper = LLMScraper(config)
            assert scraper.api_key is None
    
    def test_scrape_without_api_key(self, config):
        """Test scraping without API key raises error."""
        scraper = LLMScraper(config, api_key=None)
        
        with pytest.raises(ValueError, match="API key is required"):
            scraper.scrape("https://example.com")
    
    @patch('scrapers.llm_based.FirecrawlApp')
    def test_scrape_with_firecrawl(self, mock_firecrawl, config):
        """Test scraping with Firecrawl."""
        # Mock Firecrawl response
        mock_app = Mock()
        mock_app.scrape_url.return_value = {
            'extract': {
                'name': 'Test Product',
                'description': 'Test description',
                'price': {'amount': 5.99, 'currency': 'GBP'},
                'ingredients': ['ingredient1', 'ingredient2'],
                'nutrition': {'energy': '100kJ'},
                'images': ['https://example.com/image.jpg']
            }
        }
        mock_firecrawl.return_value = mock_app
        
        scraper = LLMScraper(config, api_key="test-key")
        
        with patch.dict('sys.modules', {'firecrawl': MagicMock()}):
            # We need to mock the import
            with patch('scrapers.llm_based.FirecrawlApp', mock_firecrawl):
                result = scraper.scrape("https://example.com/product")
        
        assert 'product' in result
        product = result['product']
        assert product['name'] == 'Test Product'
        assert product['metadata']['method'] == 'llm'


class TestDataValidation:
    """Test data validation."""
    
    def test_validate_complete_data(self):
        """Test validation of complete data."""
        data = {
            'name': 'Test Product',
            'description': 'Test description',
            'price': {'amount': 3.50, 'currency': 'GBP'},
            'ingredients': ['water', 'salt'],
            'nutrition': {'energy': '100kJ'},
            'images': ['https://example.com/image.jpg']
        }
        
        validated = validate_scraped_data(data, method='traditional', url='https://example.com')
        
        assert 'product' in validated
        assert validated['product']['metadata']['method'] == 'traditional'
    
    def test_validate_minimal_data(self):
        """Test validation of minimal data."""
        data = {
            'name': 'Test Product',
        }
        
        validated = validate_scraped_data(data, method='traditional', url='https://example.com')
        
        assert 'product' in validated
        assert validated['product']['name'] == 'Test Product'
    
    def test_validate_invalid_method(self):
        """Test validation with invalid method."""
        data = {'name': 'Test'}
        
        with pytest.raises(ValueError, match="validation failed"):
            validate_scraped_data(data, method='invalid', url='https://example.com')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
