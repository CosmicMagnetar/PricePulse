from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from datetime import datetime
import os
from . import models, scraper
from .database import SessionLocal
from .email_service import send_price_alert_email
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()

scheduler = AsyncIOScheduler()

async def get_multi_platform_prices(product_data: dict) -> dict:
    """Get price comparison from multiple platforms using OpenRouter API."""
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set")
    
    # Extract metadata for search query
    title = product_data.get('title', '')
    brand = product_data.get('brand', '')
    model = product_data.get('model', '')
    
    search_query = f"{brand} {model} {title}"
    
    # Prepare the prompt for OpenRouter
    prompt = f"""
    Search for this product on Flipkart, Meesho, and BigBasket:
    Product: {search_query}
    Return a JSON with prices from each platform in this format:
    {{
        "flipkart": {{"price": float, "url": "string"}},
        "meesho": {{"price": float, "url": "string"}},
        "bigbasket": {{"price": float, "url": "string"}}
    }}
    """
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3-opus-20240229",
                "messages": [{"role": "user", "content": prompt}]
            }
        ) as response:
            if response.status == 200:
                result = await response.json()
                try:
                    # Extract the JSON from the response
                    price_data = json.loads(result['choices'][0]['message']['content'])
                    return price_data
                except:
                    return {}
            return {}

async def check_price_alerts(db: Session):
    """Check and process price alerts."""
    alerts = db.query(models.PriceAlert).filter(models.PriceAlert.is_sent == False).all()
    
    for alert in alerts:
        product = db.query(models.Product).filter(models.Product.id == alert.product_id).first()
        if product and product.current_price <= alert.target_price:
            # Get multi-platform prices
            product_data = scraper.scrape_amazon_product(product.amazon_url)
            price_comparison = await get_multi_platform_prices(product_data)
            
            # Send email with price comparison
            email_sent = await send_price_alert_email(
                alert.email,
                product.name,
                product.image_url,
                product.current_price,
                alert.target_price,
                product.amazon_url
            )
            
            if email_sent:
                alert.is_sent = True
                db.commit()

async def update_product_prices():
    """Update prices for all products in the database."""
    db = SessionLocal()
    try:
        products = db.query(models.Product).all()
        for product in products:
            # Scrape current price
            product_data = scraper.scrape_amazon_product(product.amazon_url)
            if product_data['current_price']:
                # Update current price
                product.current_price = product_data['current_price']
                
                # Add to price history
                price_history = models.PriceHistory(
                    product_id=product.id,
                    price=product_data['current_price']
                )
                db.add(price_history)
        
        db.commit()
        
        # Check price alerts after updating prices
        await check_price_alerts(db)
        
    except Exception as e:
        print(f"Error updating prices: {str(e)}")
        db.rollback()
    finally:
        db.close()

def start_scheduler():
    """Start the price update scheduler."""
    scheduler.add_job(update_product_prices, 'interval', minutes=30)
    scheduler.start() 