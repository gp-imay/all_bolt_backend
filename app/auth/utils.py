# app/auth/utils.py
from datetime import datetime
from typing import Dict, Any
from app.schemas.user import UserCreate

def process_supabase_token(token_data: Dict[str, Any]) -> UserCreate:
    """
    Process Supabase JWT token data and convert it to UserCreate schema
    
    Args:
        token_data: Decoded JWT token data from Supabase
        
    Returns:
        UserCreate instance with user data
    """
    return UserCreate.from_jwt_payload(token_data)

def get_user_from_token(token_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant user information from token data
    
    Args:
        token_data: Decoded JWT token data
        
    Returns:
        Dictionary containing user information
    """
    return {
        "email": token_data["email"],
        "sub": token_data["sub"],
        "full_name": token_data["user_metadata"]["full_name"],
        "email_verified": token_data["user_metadata"]["email_verified"],
        "phone_verified": token_data["user_metadata"].get("phone_verified", False),
        "auth_provider": token_data["app_metadata"]["provider"],
        "role": token_data["role"],
        "last_sign_in": datetime.fromtimestamp(token_data["iat"])
    }