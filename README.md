# LLM-Scrapers

A comprehensive web scraping solution that demonstrates both traditional and LLM-based approaches to extract product information from websites.

## Features

- **Dual Scraping Methods**:
  - Traditional scraping using BeautifulSoup4 and requests
  - LLM-based intelligent scraping using Firecrawl API
  
- **Robust Data Extraction**:
  - Product name, description, and pricing
  - Ingredients and nutritional information
  - Product images
  - Structured JSON output
  
- **Advanced Capabilities**:
  - Retry logic and error handling
  - Rate limiting to avoid blocking
  - Data validation using Pydantic
  - Comparison mode to compare both methods
  - Multiple output formats (JSON, CSV)
  - Comprehensive logging

## Project Structure

```
LLM-Scrapers/
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── traditional.py      # BeautifulSoup-based scraper
│   │   └── llm_based.py        # Firecrawl LLM-based scraper
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── parser.py           # Data parsing utilities
│   │   └── validator.py        # Data validation with Pydantic
│   └── main.py                 # CLI application
├── config/
│   └── config.json             # Configuration settings
├── tests/
│   └── test_scrapers.py        # Unit tests
├── examples/
│   └── flora_product_example.json  # Example output
├── .env.example                # Environment variables template
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone the repository**:
```bash
git clone https://github.com/veerababu74/LLM-Scrapers.git
cd LLM-Scrapers
```

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
LOG_LEVEL=INFO
RATE_LIMIT=10
```

## Getting API Keys

### Firecrawl API

1. Visit [Firecrawl.dev](https://www.firecrawl.dev/)
2. Sign up for an account
3. Navigate to your dashboard
4. Copy your API key
5. Add it to your `.env` file

**Note**: Firecrawl offers a free tier with limited requests per month. Check their pricing page for details.

## Usage

### Command Line Interface

The scraper provides a CLI with multiple options:

#### Basic Usage

**Traditional scraping** (no API key required):
```bash
python src/main.py --method traditional
```

**LLM-based scraping** (requires Firecrawl API key):
```bash
python src/main.py --method llm
```

**Compare both methods**:
```bash
python src/main.py --method both
```

#### Advanced Options

**Scrape a custom URL**:
```bash
python src/main.py --url "https://example.com/product" --method traditional
```

**Save output to specific file**:
```bash
python src/main.py --output results.json --method traditional
```

**Export as CSV**:
```bash
python src/main.py --format csv --method traditional
```

**Enable debug logging**:
```bash
python src/main.py --log-level DEBUG --method traditional
```

**Full comparison with custom output**:
```bash
python src/main.py --method both --compare --output comparison.json
```

### CLI Options Reference

```
Options:
  --url TEXT                  URL to scrape (default: Flora product page)
  --method [traditional|llm|both]  Scraping method to use (default: traditional)
  --output, -o PATH           Output file path
  --format [json|csv]         Output format (default: json)
  --compare                   Compare traditional and LLM methods
  --log-level [DEBUG|INFO|WARNING|ERROR]  Logging level (default: INFO)
  --help                      Show this message and exit
```

## Python API Usage

You can also use the scrapers programmatically:

```python
from src.scrapers.traditional import TraditionalScraper
from src.scrapers.llm_based import LLMScraper
import json

# Load configuration
with open('config/config.json', 'r') as f:
    config = json.load(f)

# Traditional scraping
traditional_scraper = TraditionalScraper(config)
result = traditional_scraper.scrape('https://www.flora.com/en-gb/our-products/flora-plant-unsalted')
print(json.dumps(result, indent=2))

# LLM-based scraping
llm_scraper = LLMScraper(config, api_key='your-api-key')
result = llm_scraper.scrape('https://www.flora.com/en-gb/our-products/flora-plant-unsalted')
print(json.dumps(result, indent=2))
```

## Output Format

Both scrapers produce consistent JSON output:

```json
{
  "product": {
    "name": "Flora Plant Unsalted",
    "description": "A delicious plant-based spread...",
    "price": {
      "amount": 3.50,
      "currency": "GBP"
    },
    "ingredients": [
      "Plant oils (rapeseed, palm, sunflower) 65%",
      "water",
      "salt 0.3%"
    ],
    "nutrition": {
      "per_serving": {
        "energy": "615kJ/150kcal",
        "fat": "70g"
      },
      "serving_size": "10g"
    },
    "images": [
      "https://www.flora.com/images/product.jpg"
    ],
    "metadata": {
      "scraped_at": "2026-02-03T12:00:00",
      "method": "traditional",
      "url": "https://www.flora.com/en-gb/our-products/flora-plant-unsalted"
    }
  }
}
```

See `examples/flora_product_example.json` for a complete example.

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_scrapers.py -v
```

## Comparison: Traditional vs LLM-based Scraping

### Traditional Scraping

**Pros**:
- ✅ No API costs
- ✅ Fast and predictable
- ✅ Full control over parsing logic
- ✅ Works offline (with cached HTML)
- ✅ No rate limits beyond HTTP requests

**Cons**:
- ❌ Breaks when HTML structure changes
- ❌ Requires manual selector maintenance
- ❌ Difficult with dynamic/JavaScript-heavy sites
- ❌ Time-consuming to develop parsers
- ❌ Limited understanding of context

### LLM-based Scraping

**Pros**:
- ✅ Adapts to HTML structure changes
- ✅ Understands context and semantics
- ✅ Handles dynamic content better
- ✅ Less maintenance required
- ✅ Can extract complex relationships

**Cons**:
- ❌ API costs per request
- ❌ Slower than traditional methods
- ❌ Requires API key management
- ❌ Subject to rate limits
- ❌ Less predictable results

### When to Use Each Method

**Use Traditional** when:
- Budget is a concern
- Site structure is stable
- You need maximum speed
- You require offline capability
- Data schema is well-defined

**Use LLM-based** when:
- Site structure changes frequently
- Working with complex layouts
- Need semantic understanding
- Budget allows for API costs
- Dealing with diverse data formats

## Configuration

Edit `config/config.json` to customize behavior:

```json
{
  "scraping": {
    "user_agent": "Your User Agent String",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 2
  },
  "rate_limiting": {
    "requests_per_minute": 10,
    "delay_between_requests": 1
  },
  "output": {
    "default_format": "json",
    "output_directory": "output"
  },
  "logging": {
    "level": "INFO"
  }
}
```

## Error Handling

The scrapers include robust error handling:

- **Network errors**: Automatic retry with exponential backoff
- **Parsing errors**: Graceful degradation with partial data
- **Validation errors**: Warning logs with unvalidated output
- **API errors**: Clear error messages with troubleshooting hints

## Rate Limiting

To avoid being blocked:

1. Configure `delay_between_requests` in `config.json`
2. Set `requests_per_minute` limit
3. Use appropriate `User-Agent` headers
4. Respect `robots.txt` directives

## Logging

Logs are configured via environment variable or CLI:

```bash
# Set in .env
LOG_LEVEL=DEBUG

# Or via CLI
python src/main.py --log-level DEBUG
```

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`

## Troubleshooting

### "Firecrawl API key not set"
- Ensure `.env` file exists with `FIRECRAWL_API_KEY`
- Check environment variable is loaded: `echo $FIRECRAWL_API_KEY`

### "Failed to fetch URL after retries"
- Check internet connection
- Verify URL is accessible
- Check firewall/proxy settings
- Increase timeout in config.json

### "Data validation failed"
- Check scraped data structure
- Review HTML selectors in traditional.py
- Verify site HTML hasn't changed

### Import errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python version is 3.8+

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is for educational purposes. Always:
- Respect website terms of service
- Follow robots.txt directives
- Implement appropriate rate limiting
- Don't overload servers with requests

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review example outputs in `examples/`

## Acknowledgments

- BeautifulSoup4 for HTML parsing
- Firecrawl for LLM-powered scraping
- Pydantic for data validation
- Click for CLI interface

## Roadmap

Future enhancements:
- [ ] Support for additional LLM scraping services (Serper, etc.)
- [ ] Selenium integration for JavaScript-heavy sites
- [ ] Database storage options
- [ ] Scheduling and automation
- [ ] Web UI dashboard
- [ ] Docker containerization
- [ ] API server mode

---

**Target URL**: https://www.flora.com/en-gb/our-products/flora-plant-unsalted

For more examples and documentation, see the `examples/` directory.