from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List
import os
from pathlib import Path
from pydantic import EmailStr
from datetime import datetime

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME="nexiumiq@gmail.com",
    MAIL_PASSWORD="Krishna020706",
    MAIL_FROM="nexiumiq@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fastmail = FastMail(conf)

async def send_price_alert_email(
    recipient_email: str,
    product_name: str,
    product_image: str,
    current_price: float,
    target_price: float,
    product_url: str
) -> bool:
    """
    Send a price alert email when a product's price drops below the target price.
    Returns True if email was sent successfully, False otherwise.
    """
    try:
        message = MessageSchema(
            subject=f"Price Alert: {product_name} is now below your target price!",
            recipients=[EmailStr(recipient_email)],
            body=f"""
            <html>
                <body>
                    <h2>Price Alert!</h2>
                    <p>The price of {product_name} has dropped below your target price!</p>
                    <img src="{product_image}" alt="{product_name}" style="max-width: 300px;">
                    <p><strong>Current Price:</strong> ${current_price:.2f}</p>
                    <p><strong>Your Target Price:</strong> ${target_price:.2f}</p>
                    <p><a href="{product_url}">View Product</a></p>
                    <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </body>
            </html>
            """,
            subtype="html"
        )
        
        await fastmail.send_message(message)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False 