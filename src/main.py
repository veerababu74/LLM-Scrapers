"""Main CLI application for web scraping."""
import click
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.traditional import TraditionalScraper
from scrapers.llm_based import LLMScraper
from utils.validator import is_valid_url


# Load environment variables
load_dotenv()


def setup_logging(log_level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )


def load_config() -> dict:
    """Load configuration from config file."""
    config_path = Path(__file__).parent.parent / 'config' / 'config.json'
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    
    # Return default config if file doesn't exist
    return {
        'scraping': {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 2
        },
        'rate_limiting': {
            'requests_per_minute': 10,
            'delay_between_requests': 1
        },
        'output': {
            'default_format': 'json',
            'output_directory': 'output'
        },
        'logging': {
            'level': 'INFO'
        }
    }


def save_output(data: dict, output_path: Optional[str], format: str = 'json'):
    """
    Save scraped data to file.
    
    Args:
        data: Scraped data dictionary
        output_path: Output file path (optional)
        format: Output format ('json' or 'csv')
    """
    if output_path:
        output_file = Path(output_path)
    else:
        # Create output directory if it doesn't exist
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        method = data.get('product', {}).get('metadata', {}).get('method', 'unknown')
        output_file = output_dir / f'scraped_data_{method}_{timestamp}.{format}'
    
    if format == 'json':
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif format == 'csv':
        # Flatten the data for CSV
        import csv
        flattened = flatten_dict(data)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if flattened:
                writer = csv.DictWriter(f, fieldnames=flattened.keys())
                writer.writeheader()
                writer.writerow(flattened)
    
    click.echo(f"Output saved to: {output_file}")
    return str(output_file)


def flatten_dict(d: dict, parent_key: str = '', sep: str = '_') -> dict:
    """Flatten nested dictionary for CSV export."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, ', '.join(str(x) for x in v)))
        else:
            items.append((new_key, v))
    
    return dict(items)


def compare_results(traditional_data: dict, llm_data: dict) -> dict:
    """
    Compare results from traditional and LLM scrapers.
    
    Args:
        traditional_data: Data from traditional scraper
        llm_data: Data from LLM scraper
    
    Returns:
        Comparison dictionary
    """
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'traditional': traditional_data,
        'llm': llm_data,
        'differences': {}
    }
    
    # Extract product data
    trad_product = traditional_data.get('product', {})
    llm_product = llm_data.get('product', {})
    
    # Compare fields
    fields = ['name', 'description', 'price', 'ingredients', 'nutrition', 'images']
    
    for field in fields:
        trad_value = trad_product.get(field)
        llm_value = llm_product.get(field)
        
        if trad_value != llm_value:
            comparison['differences'][field] = {
                'traditional': trad_value,
                'llm': llm_value
            }
    
    return comparison


@click.command()
@click.option('--url', default='https://www.flora.com/en-gb/our-products/flora-plant-unsalted',
              help='URL to scrape')
@click.option('--method', type=click.Choice(['traditional', 'llm', 'both']),
              default='traditional', help='Scraping method to use')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', type=click.Choice(['json', 'csv']),
              default='json', help='Output format')
@click.option('--compare', is_flag=True, help='Compare traditional and LLM methods')
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              help='Logging level')
def main(url: str, method: str, output: Optional[str], format: str,
         compare: bool, log_level: str):
    """
    Web scraping CLI tool.
    
    Scrape product information using traditional or LLM-based methods.
    """
    # Setup logging
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    # Validate URL
    if not is_valid_url(url):
        click.echo(f"Error: Invalid URL: {url}", err=True)
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    click.echo(f"Scraping URL: {url}")
    click.echo(f"Method: {method}")
    
    try:
        if method == 'traditional' or (method == 'both' and not compare):
            # Traditional scraping
            click.echo("\n=== Traditional Scraping ===")
            scraper = TraditionalScraper(config)
            data = scraper.scrape(url)
            
            # Save output
            output_path = save_output(data, output, format)
            
            # Display summary
            product = data.get('product', {})
            click.echo(f"\nProduct: {product.get('name', 'N/A')}")
            click.echo(f"Price: {product.get('price', {}).get('amount', 'N/A')} "
                      f"{product.get('price', {}).get('currency', '')}")
            click.echo(f"Images: {len(product.get('images', []))} found")
            
        elif method == 'llm':
            # LLM scraping
            click.echo("\n=== LLM-based Scraping ===")
            
            api_key = os.getenv('FIRECRAWL_API_KEY')
            if not api_key:
                click.echo("Error: FIRECRAWL_API_KEY not set in environment", err=True)
                click.echo("Please set it in .env file or environment variables", err=True)
                sys.exit(1)
            
            scraper = LLMScraper(config, api_key)
            data = scraper.scrape(url)
            
            # Save output
            output_path = save_output(data, output, format)
            
            # Display summary
            product = data.get('product', {})
            click.echo(f"\nProduct: {product.get('name', 'N/A')}")
            click.echo(f"Price: {product.get('price', {}).get('amount', 'N/A')} "
                      f"{product.get('price', {}).get('currency', '')}")
            click.echo(f"Images: {len(product.get('images', []))} found")
            
        elif method == 'both' or compare:
            # Run both and compare
            click.echo("\n=== Running Both Methods ===")
            
            # Traditional
            click.echo("\n1. Traditional scraping...")
            trad_scraper = TraditionalScraper(config)
            trad_data = trad_scraper.scrape(url)
            
            # LLM
            click.echo("\n2. LLM-based scraping...")
            api_key = os.getenv('FIRECRAWL_API_KEY')
            if not api_key:
                click.echo("Warning: FIRECRAWL_API_KEY not set. Skipping LLM scraping.", err=True)
                llm_data = {'product': {}}
            else:
                llm_scraper = LLMScraper(config, api_key)
                llm_data = llm_scraper.scrape(url)
            
            # Compare results
            comparison = compare_results(trad_data, llm_data)
            
            # Save comparison
            if output:
                comparison_path = output
            else:
                output_dir = Path('output')
                output_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                comparison_path = output_dir / f'comparison_{timestamp}.json'
            
            with open(comparison_path, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, indent=2, ensure_ascii=False)
            
            click.echo(f"\nComparison saved to: {comparison_path}")
            
            # Display differences
            if comparison['differences']:
                click.echo("\n=== Differences Found ===")
                for field, diff in comparison['differences'].items():
                    click.echo(f"\n{field}:")
                    click.echo(f"  Traditional: {diff['traditional']}")
                    click.echo(f"  LLM: {diff['llm']}")
            else:
                click.echo("\nNo differences found between methods!")
        
        click.echo("\n✓ Scraping completed successfully!")
        
    except Exception as e:
        logger.exception("Scraping failed")
        click.echo(f"\n✗ Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
