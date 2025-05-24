from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional
import yaml
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_scraping_config() -> Dict:
    """Load ScrapingBee configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), 'scraping_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def extract_price(price_str: str) -> Optional[float]:
    """Extract price from string and convert to float."""
    if not price_str:
        return None
    
    logger.info(f"Attempting to extract price from: {price_str}")
    
    # Remove currency symbols and convert to float
    price = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(price)
    except ValueError:
        logger.error(f"Failed to convert price string to float: {price}")
        return None

def save_debug_html(html_content: str, filename: str = "debug_page.html"):
    """Save HTML content to a file for debugging."""
    debug_path = os.path.join(os.path.dirname(__file__), filename)
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"Saved debug HTML to {debug_path}")

def scrape_amazon_product(url: str) -> Dict:
    """Scrape product information using ScrapingBee."""
    try:
        # Load configuration
        config = load_scraping_config()
        api_key = config['scrapingbee']['api_key']
        
        if not api_key:
            logger.error("ScrapingBee API key not configured")
            return {
                'name': None,
                'image_url': None,
                'current_price': None,
                'amazon_url': url
            }
        
        logger.info(f"Using ScrapingBee to scrape: {url}")
        
        # Initialize ScrapingBee client
        client = ScrapingBeeClient(api_key=api_key)
        
        # Configure scraping parameters
        params = {
            'render_js': True,  # Always enable JS rendering
            'premium_proxy': True,  # Always use premium proxies
            'country_code': "us",  # Use US proxies
            'wait': 5000,  # Wait 5 seconds for JavaScript to load
            'block_resources': False,  # Don't block any resources
            'block_ads': False,  # Don't block ads
        }
        
        # Make the request
        logger.info("Sending request to ScrapingBee...")
        response = client.get(url, params=params)
        
        logger.info(f"ScrapingBee response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Error from ScrapingBee: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return {
                'name': None,
                'image_url': None,
                'current_price': None,
                'amazon_url': url
            }
        
        # Save HTML for debugging
        save_debug_html(response.text)
        
        # Parse the response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get product name
        name = soup.find('span', {'id': 'productTitle'})
        name = name.text.strip() if name else None
        logger.info(f"Found product name: {name}")
        
        # Get product image
        image = soup.find('img', {'id': 'landingImage'})
        image_url = image.get('data-old-hires') if image else None
        if not image_url:
            image_url = image.get('src') if image else None
        logger.info(f"Found image URL: {image_url}")
        
        # Get price - try multiple price selectors
        price = None
        price_selectors = [
            'span.a-offscreen',
            'span.a-price span.a-offscreen',
            'span.a-price-whole',
            'span#priceblock_ourprice',
            'span#priceblock_dealprice',
            'span.a-price',
            'div.a-section span.a-price',
            'div#price',
            'div#priceblock_ourprice',
            'div#priceblock_dealprice',
            'span.a-color-price',  # Additional selector
            'span.a-color-base span.a-color-price',  # Additional selector
            'div.a-section span.a-color-price',  # Additional selector
        ]
        
        logger.info("\nSearching for price elements...")
        for selector in price_selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"\nFound elements for selector '{selector}':")
                for elem in elements:
                    logger.info(f"Text: {elem.text.strip()}")
                    if elem.get('class'):
                        logger.info(f"Classes: {elem.get('class')}")
        
        # Try to find price in the page
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price_text = price_element.text.strip()
                logger.info(f"\nTrying to extract price from element: {price_text}")
                price = extract_price(price_text)
                if price:
                    logger.info(f"Successfully extracted price: {price}")
                    break
        
        # If still no price, try to find it in the page data
        if not price:
            logger.info("\nTrying to find price in page data...")
            # Look for price in the page data
            price_data = soup.find('script', {'type': 'application/ld+json'})
            if price_data:
                try:
                    data = json.loads(price_data.string)
                    logger.info(f"Found JSON-LD data: {json.dumps(data, indent=2)}")
                    if isinstance(data, dict) and 'offers' in data:
                        if 'price' in data['offers']:
                            price = float(data['offers']['price'])
                            logger.info(f"Found price in JSON-LD: {price}")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Error parsing JSON-LD: {e}")
            
            # Try to find price in embedded JavaScript
            if not price:
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'price' in script.string.lower():
                        logger.info(f"Found script with price: {script.string[:200]}...")
                        # Look for price patterns in the script
                        price_matches = re.findall(r'price["\']?\s*:\s*["\']?(\d+\.?\d*)["\']?', script.string)
                        if price_matches:
                            try:
                                price = float(price_matches[0])
                                logger.info(f"Found price in script: {price}")
                                break
                            except ValueError:
                                continue
        
        if not name or not price:
            logger.error(f"\nCould not extract required data. Name: {name}, Price: {price}")
            return {
                'name': None,
                'image_url': None,
                'current_price': None,
                'amazon_url': url
            }
        
        return {
            'name': name,
            'image_url': image_url,
            'current_price': price,
            'amazon_url': url
        }
        
    except Exception as e:
        logger.error(f"Error scraping product: {str(e)}")
        return {
            'name': None,
            'image_url': None,
            'current_price': None,
            'amazon_url': url
        } 