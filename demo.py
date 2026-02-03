#!/usr/bin/env python
"""Demo script to showcase the scraper functionality with mock data."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.parser import clean_text, extract_price, parse_ingredients, parse_nutrition
from src.utils.validator import validate_scraped_data
from datetime import datetime

def demo_parser_functions():
    """Demonstrate parser utility functions."""
    print("=" * 60)
    print("DEMO: Parser Utility Functions")
    print("=" * 60)
    
    # Clean text
    print("\n1. Clean Text:")
    raw_text = "  Flora   Plant   Unsalted  \n"
    cleaned = clean_text(raw_text)
    print(f"   Input: {repr(raw_text)}")
    print(f"   Output: {repr(cleaned)}")
    
    # Extract price
    print("\n2. Extract Price:")
    prices = ["£3.50", "$4.99", "€5.00"]
    for price_text in prices:
        result = extract_price(price_text)
        print(f"   {price_text} -> {result}")
    
    # Parse ingredients
    print("\n3. Parse Ingredients:")
    ingredients_text = "Water, Plant oils (rapeseed, palm), Salt, Vitamin A"
    result = parse_ingredients(ingredients_text)
    print(f"   Input: {ingredients_text}")
    print(f"   Output: {json.dumps(result, indent=4)}")
    
    # Parse nutrition
    print("\n4. Parse Nutrition:")
    nutrition_text = "Energy: 615kJ, Fat: 70g, Saturates: 20g, Carbohydrates: 1g, Sugars: 0g, Protein: 0g, Salt: 0.3g"
    result = parse_nutrition(nutrition_text)
    print(f"   Input: {nutrition_text}")
    print(f"   Output: {json.dumps(result, indent=4)}")


def demo_data_validation():
    """Demonstrate data validation."""
    print("\n" + "=" * 60)
    print("DEMO: Data Validation")
    print("=" * 60)
    
    # Valid data
    print("\n1. Validating complete product data:")
    product_data = {
        'name': 'Flora Plant Unsalted',
        'description': 'A delicious plant-based spread',
        'price': {'amount': 3.50, 'currency': 'GBP'},
        'ingredients': ['Water', 'Plant oils', 'Salt'],
        'nutrition': {'energy': '615kJ', 'fat': '70g'},
        'images': ['https://example.com/image.jpg']
    }
    
    validated = validate_scraped_data(
        product_data,
        method='traditional',
        url='https://www.flora.com/product'
    )
    
    print(f"   ✓ Validation successful!")
    print(f"   Product name: {validated['product']['name']}")
    print(f"   Method: {validated['product']['metadata']['method']}")
    
    # Minimal data
    print("\n2. Validating minimal product data:")
    minimal_data = {'name': 'Test Product'}
    
    validated = validate_scraped_data(
        minimal_data,
        method='llm',
        url='https://example.com'
    )
    
    print(f"   ✓ Validation successful!")
    print(f"   Product name: {validated['product']['name']}")
    print(f"   Has ingredients: {len(validated['product']['ingredients'])} items")


def demo_complete_scraping_output():
    """Demonstrate complete scraping output structure."""
    print("\n" + "=" * 60)
    print("DEMO: Complete Scraping Output Structure")
    print("=" * 60)
    
    output = {
        "product": {
            "name": "Flora Plant Unsalted",
            "description": "Flora Plant Unsalted is a delicious plant-based spread made with nutritious plant oils.",
            "price": {
                "amount": 3.50,
                "currency": "GBP"
            },
            "ingredients": [
                "Plant oils (rapeseed, palm, sunflower) 65%",
                "water",
                "salt 0.3%",
                "plant based emulsifier (sunflower lecithin)",
                "vitamins A and D"
            ],
            "nutrition": {
                "per_serving": {
                    "energy": "615kJ/150kcal",
                    "fat": "70g",
                    "saturates": "20g",
                    "carbohydrates": "1g",
                    "sugars": "0g",
                    "protein": "0g",
                    "salt": "0.3g"
                },
                "serving_size": "10g"
            },
            "images": [
                "https://www.flora.com/images/flora-plant-unsalted.jpg"
            ],
            "metadata": {
                "scraped_at": datetime.now().isoformat(),
                "method": "traditional",
                "url": "https://www.flora.com/en-gb/our-products/flora-plant-unsalted"
            }
        }
    }
    
    print("\nGenerated output structure:")
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    print("\n🚀 LLM-Scrapers Demo\n")
    
    try:
        demo_parser_functions()
        demo_data_validation()
        demo_complete_scraping_output()
        
        print("\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)
        print("\nFor actual scraping, use:")
        print("  python src/main.py --method traditional")
        print("  python src/main.py --method llm  (requires API key)")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
