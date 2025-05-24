from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import sqlite3
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
from backend.routes import router
from backend.scheduler import start_scheduler
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

app = FastAPI(title="PricePulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

class ProductURL(BaseModel):
    url: str

class AlertRequest(BaseModel):
    url: str
    email: EmailStr
    target_price: float

# Mock data for testing
MOCK_PRODUCTS = {
    "B08N5KWB9H": {
        "name": "Apple AirPods Pro (2nd Generation)",
        "current_price": 249.99,
        "image_url": "https://m.media-amazon.com/images/I/61SUj2aKoEL._AC_SL1500_.jpg"
    },
    "B0CHWRXH8M": {
        "name": "Apple AirPods Pro (2nd Generation) with USB-C",
        "current_price": 199.99,
        "image_url": "https://m.media-amazon.com/images/I/61SUj2aKoEL._AC_SL1500_.jpg"
    },
    "B0CHFM8N75": {
        "name": "Haier 242 L 3 Star Convertible Refrigerator",
        "current_price": 24990.00,
        "image_url": "https://m.media-amazon.com/images/I/61SUj2aKoEL._AC_SL1500_.jpg"
    },
    "B004IF24XE": {
        "name": "Kurkure Namkeen Masala Munch",
        "current_price": 20.00,
        "image_url": "https://m.media-amazon.com/images/I/61SUj2aKoEL._AC_SL1500_.jpg"
    },
    "B009GIUZNE": {
        "name": "Kurkure Green Chutney Rajasthani Style",
        "current_price": 20.00,
        "image_url": "https://m.media-amazon.com/images/I/71QKQ9mwV7L._SX522_.jpg"
    }
}

# Default email configuration for testing
email_conf = ConnectionConfig(
    MAIL_USERNAME="test@example.com",
    MAIL_PASSWORD="test_password",
    MAIL_FROM="test@example.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

fastmail = FastMail(email_conf)

def init_db():
    conn = sqlite3.connect('prices.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  url TEXT UNIQUE,
                  name TEXT,
                  current_price REAL,
                  image_url TEXT,
                  last_updated TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS price_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER,
                  price REAL,
                  timestamp TIMESTAMP,
                  FOREIGN KEY (product_id) REFERENCES products (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS price_alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER,
                  email TEXT,
                  target_price REAL,
                  created_at TIMESTAMP,
                  FOREIGN KEY (product_id) REFERENCES products (id))''')
    
    conn.commit()
    conn.close()

init_db()

def extract_product_info(url: str):
    # Extract product ID from URL
    product_id = re.search(r'/dp/([A-Z0-9]{10})', url)
    if not product_id:
        raise HTTPException(status_code=400, detail="Invalid Amazon product URL")
    
    product_id = product_id.group(1)
    print(f"Extracted product ID: {product_id}")  # Debug log
    
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        # Initialize the Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            print(f"Fetching URL: {url}")  # Debug log
            driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
            
            # Add random delay
            time.sleep(random.uniform(2, 4))
            
            # Check for CAPTCHA
            if "Robot Check" in driver.page_source or "Enter the characters you see below" in driver.page_source:
                print("Amazon is blocking our requests")  # Debug log
                raise HTTPException(status_code=403, detail="Amazon is blocking our requests. Please try again later.")
            
            # Extract product information
            try:
                name = driver.find_element(By.ID, "productTitle").text.strip()
            except:
                try:
                    name = driver.find_element(By.CSS_SELECTOR, "h1#title").text.strip()
                except:
                    raise HTTPException(status_code=400, detail="Could not find product name")
            
            # Try multiple price selectors
            price = None
            price_selectors = [
                "span.a-offscreen",
                "span.a-price-whole",
                "span.a-price",
                "span.a-price a-text-price",
                "span.a-price.aok-align-center",
                "span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay",
                "div#priceblock_ourprice",
                "div#priceblock_dealprice",
                "span.a-color-price",
                "span.a-price.a-text-price.a-size-medium",
                "span.a-price.a-text-price.a-size-medium.apexPriceToPay"
            ]
            
            for selector in price_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        price_text = element.text.strip()
                        print(f"Found price text using selector {selector}: {price_text}")  # Debug log
                        
                        # Handle Indian price format (₹ symbol and commas)
                        price_text = price_text.replace('₹', '').replace(',', '')
                        # Remove any non-numeric characters except decimal point
                        price_text = re.sub(r'[^\d.]', '', price_text)
                        
                        try:
                            price = float(price_text)
                            if price > 0:  # Ensure price is valid
                                print(f"Successfully parsed price: {price}")  # Debug log
                                break
                        except ValueError:
                            continue
                    
                    if price:
                        break
                except Exception as e:
                    print(f"Error with selector {selector}: {str(e)}")  # Debug log
                    continue
            
            if not price:
                print("Could not find or parse price")  # Debug log
                raise HTTPException(status_code=400, detail="Could not find or parse product price")
            
            # Try to find the image
            image_url = None
            image_selectors = [
                "img#landingImage",
                "img#imgBlkFront",
                "img.a-dynamic-image",
                "img.a-dynamic-image.a-stretch-vertical",
                "img.a-dynamic-image.a-stretch-horizontal",
                "img.a-dynamic-image.a-stretch-horizontal.a-stretch-vertical",
                "div#imageBlock img",
                "div#main-image-container img"
            ]
            
            for selector in image_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        image_url = element.get_attribute("src") or element.get_attribute("data-old-hires")
                        if image_url:
                            print(f"Found image URL using selector {selector}: {image_url}")  # Debug log
                            break
                    if image_url:
                        break
                except Exception as e:
                    print(f"Error with image selector {selector}: {str(e)}")  # Debug log
                    continue
            
            if not image_url:
                print("Could not find image URL")  # Debug log
                image_url = "https://via.placeholder.com/300"
            
            print(f"Extracted - Name: {name}, Price: {price}, Image: {image_url}")  # Debug log
            
            return {
                'name': name,
                'current_price': price,
                'image_url': image_url
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def save_product_info(url: str, product_info: dict):
    conn = sqlite3.connect('prices.db')
    c = conn.cursor()
    
    try:
        print(f"Saving product info: {product_info}")  # Debug log
        
        # First check if product exists
        c.execute('SELECT id FROM products WHERE url = ?', (url,))
        result = c.fetchone()
        
        if result:
            product_id = result[0]
            print(f"Updating existing product: {product_id}")  # Debug log
            c.execute('''UPDATE products 
                        SET name = ?, current_price = ?, image_url = ?, last_updated = ?
                        WHERE id = ?''',
                     (product_info['name'], product_info['current_price'],
                      product_info['image_url'], datetime.now(), product_id))
        else:
            print("Creating new product")  # Debug log
            c.execute('''INSERT INTO products (url, name, current_price, image_url, last_updated)
                        VALUES (?, ?, ?, ?, ?)''',
                     (url, product_info['name'], product_info['current_price'],
                      product_info['image_url'], datetime.now()))
            product_id = c.lastrowid
        
        # Add price to history
        c.execute('''INSERT INTO price_history (product_id, price, timestamp)
                    VALUES (?, ?, ?)''',
                 (product_id, product_info['current_price'], datetime.now()))
        
        conn.commit()
        return product_id
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")  # Debug log
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def get_price_history(product_id: int):
    conn = sqlite3.connect('prices.db')
    c = conn.cursor()
    
    try:
        c.execute('''SELECT price, timestamp FROM price_history
                     WHERE product_id = ? ORDER BY timestamp DESC''', (product_id,))
        history = [{'price': row[0], 'timestamp': row[1]} for row in c.fetchall()]
        return history
    except sqlite3.Error as e:
        print(f"Error fetching price history: {str(e)}")  # Debug log
        return []  # Return empty list on error
    finally:
        conn.close()

async def check_price_alerts():
    conn = sqlite3.connect('prices.db')
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT p.id, p.name, p.current_price, pa.email, pa.target_price
            FROM products p
            JOIN price_alerts pa ON p.id = pa.product_id
            WHERE p.current_price <= pa.target_price
        ''')
        
        alerts = c.fetchall()
        for alert in alerts:
            product_id, name, current_price, email, target_price = alert
            
            message = MessageSchema(
                subject="Price Alert!",
                recipients=[email],
                body=f"""
                Price Alert for {name}!
                
                The price has dropped to ${current_price}, which is below your target price of ${target_price}.
                
                Check it out here: {url}
                """,
                subtype="html"
            )
            
            await fastmail.send_message(message)
            
            # Remove the alert after sending
            c.execute('DELETE FROM price_alerts WHERE product_id = ? AND email = ?',
                     (product_id, email))
        
        conn.commit()
    except Exception as e:
        print(f"Error checking price alerts: {str(e)}")
    finally:
        conn.close()

async def update_all_prices():
    conn = sqlite3.connect('prices.db')
    c = conn.cursor()
    
    try:
        c.execute('SELECT id, url FROM products')
        products = c.fetchall()
        
        for product_id, url in products:
            try:
                product_info = extract_product_info(url)
                c.execute('''UPDATE products 
                            SET current_price = ?, last_updated = ?
                            WHERE id = ?''',
                         (product_info['current_price'], datetime.now(), product_id))
                
                c.execute('''INSERT INTO price_history (product_id, price, timestamp)
                            VALUES (?, ?, ?)''',
                         (product_id, product_info['current_price'], datetime.now()))
                
            except Exception as e:
                print(f"Error updating product {product_id}: {str(e)}")
        
        conn.commit()
    except Exception as e:
        print(f"Error updating prices: {str(e)}")
    finally:
        conn.close()

scheduler = AsyncIOScheduler()
scheduler.add_job(update_all_prices, 'interval', minutes=30)
scheduler.add_job(check_price_alerts, 'interval', minutes=30)
scheduler.start()

@app.post("/track")
async def track_product(product: ProductURL):
    try:
        print(f"Received URL: {product.url}")  # Debug log
        
        # Extract product ID from URL
        product_id = re.search(r'/dp/([A-Z0-9]{10})', product.url)
        if not product_id:
            print("Invalid URL format - no product ID found")  # Debug log
            raise HTTPException(status_code=400, detail="Invalid Amazon product URL")
        
        product_id = product_id.group(1)
        print(f"Extracted product ID: {product_id}")  # Debug log
        
        # Try to get real product info
        try:
            product_info = extract_product_info(product.url)
            print(f"Extracted product info: {product_info}")  # Debug log
            product_id = save_product_info(product.url, product_info)
            price_history = get_price_history(product_id)
            
            return {
                "product": product_info,
                "price_history": price_history
            }
        except Exception as e:
            print(f"Error scraping product: {str(e)}")  # Debug log
            raise HTTPException(status_code=500, detail=f"Failed to fetch product information: {str(e)}")
        
    except HTTPException as e:
        print(f"HTTP Exception: {str(e)}")  # Debug log
        raise e
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/alerts")
async def create_alert(alert: AlertRequest):
    try:
        product_info = extract_product_info(alert.url)
        product_id = save_product_info(alert.url, product_info)
        
        conn = sqlite3.connect('prices.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO price_alerts (product_id, email, target_price, created_at)
                     VALUES (?, ?, ?, ?)''',
                  (product_id, alert.email, alert.target_price, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return {"message": "Price alert created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "PricePulse API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    start_scheduler()  # Start the price update scheduler
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 