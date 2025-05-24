from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from . import models, scraper
from .database import SessionLocal

scheduler = AsyncIOScheduler()

def send_price_alert_email(email: str, product_name: str, current_price: float, target_price: float):
    """Send price alert email using Gmail SMTP."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("GMAIL_USER")
    sender_password = os.getenv("GMAIL_APP_PASSWORD")

    if not all([sender_email, sender_password]):
        print("Gmail credentials not configured")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = f"Price Alert: {product_name} has reached your target price!"

    body = f"""
    Good news! The price of {product_name} has dropped to ${current_price:.2f}, 
    which is below your target price of ${target_price:.2f}.

    You can check the product here: https://www.amazon.com/dp/{product_name.split('/')[-1]}
    """

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Price alert email sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

async def check_price_alerts(db: Session):
    """Check and process price alerts."""
    alerts = db.query(models.PriceAlert).filter(models.PriceAlert.is_sent == False).all()
    
    for alert in alerts:
        product = db.query(models.Product).filter(models.Product.id == alert.product_id).first()
        if product and product.current_price <= alert.target_price:
            send_price_alert_email(
                alert.email,
                product.name,
                product.current_price,
                alert.target_price
            )
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