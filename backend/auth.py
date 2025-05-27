from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin only if credentials are available
firebase_initialized = False
if all([
    os.getenv("FIREBASE_PROJECT_ID"),
    os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    os.getenv("FIREBASE_PRIVATE_KEY"),
    os.getenv("FIREBASE_CLIENT_EMAIL"),
    os.getenv("FIREBASE_CLIENT_ID"),
    os.getenv("FIREBASE_CLIENT_CERT_URL")
]):
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
    })
    try:
        firebase_admin.initialize_app(cred)
        firebase_initialized = True
    except ValueError:
        # App already initialized
        firebase_initialized = True

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Verify Firebase token and return user email. For development, returns a default email if no Firebase credentials.
    """
    if not firebase_initialized:
        return "dev@example.com"  # Default user for development
        
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token['email']
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) 