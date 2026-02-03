"""Validator utilities for scraped data."""
from typing import Any, Dict, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class PriceModel(BaseModel):
    """Price validation model."""
    amount: float | None = None
    currency: str = "GBP"
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        valid_currencies = ['GBP', 'USD', 'EUR', 'JPY']
        if v not in valid_currencies:
            return 'GBP'
        return v


class MetadataModel(BaseModel):
    """Metadata validation model."""
    scraped_at: str
    method: str
    url: str
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate scraping method."""
        if v not in ['traditional', 'llm']:
            raise ValueError("Method must be 'traditional' or 'llm'")
        return v


class ProductModel(BaseModel):
    """Product data validation model."""
    name: str | None = None
    description: str | None = None
    price: PriceModel | None = None
    ingredients: List[str] = Field(default_factory=list)
    nutrition: Dict[str, Any] = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    metadata: MetadataModel


class ScrapedDataModel(BaseModel):
    """Complete scraped data validation model."""
    product: ProductModel


def validate_scraped_data(data: Dict[str, Any], method: str, url: str) -> Dict[str, Any]:
    """
    Validate scraped data against the schema.
    
    Args:
        data: Scraped data dictionary
        method: Scraping method used ('traditional' or 'llm')
        url: Source URL
    
    Returns:
        Validated data dictionary
    
    Raises:
        ValueError: If data validation fails
    """
    # Add metadata if not present
    if 'metadata' not in data:
        data['metadata'] = {
            'scraped_at': datetime.now().isoformat(),
            'method': method,
            'url': url
        }
    
    # Wrap in product key if not present
    if 'product' not in data:
        data = {'product': data}
    
    # Validate using Pydantic
    try:
        validated = ScrapedDataModel(**data)
        return validated.model_dump()
    except Exception as e:
        raise ValueError(f"Data validation failed: {str(e)}")


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return pattern.match(url) is not None
