from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
import json
import asyncio

app = FastAPI(
    title="Universal AI API",
    description="Multi-service AI API with credit limits and admin controls",
    version="3.0.0"
)

# In-memory storage for serverless compatibility
API_KEYS_STORAGE = {}
ADMIN_USERS_STORAGE = {}
REQUEST_LOGS_STORAGE = []

# Initialize storage with default admin
def init_storage():
    """Initialize in-memory storage for serverless environment"""
    global API_KEYS_STORAGE, ADMIN_USERS_STORAGE, REQUEST_LOGS_STORAGE
    
    # Default admin
    password_hash = hashlib.sha256("mk123".encode()).hexdigest()
    ADMIN_USERS_STORAGE['mk'] = password_hash
    
    # Create a default API key for testing
    default_key = generate_api_key()
    API_KEYS_STORAGE[default_key] = {
        'id': 1,
        'key': default_key,
        'name': 'Test Key',
        'created_at': datetime.utcnow(),
        'is_active': True,
        'total_requests': 0,
        'daily_requests': 0,
        'daily_limit': 30,
        'credits': 50,  # Give more credits for testing
        'last_reset': datetime.utcnow(),
        'last_used': None,
        'expires_at': datetime.utcnow() + timedelta(days=365)
    }

# Initialize on import
init_storage()

# Utility functions
def generate_api_key():
    return f"api_{secrets.token_urlsafe(24)}"

def verify_admin(username: str, password: str) -> bool:
    """Verify admin credentials"""
    if username in ADMIN_USERS_STORAGE:
        stored_hash = ADMIN_USERS_STORAGE[username]
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash
    return False

def check_credits(api_key: str, credits_needed: int = 0) -> bool:
    """Check if user has enough credits"""
    if api_key not in API_KEYS_STORAGE:
        return False
    
    key_data = API_KEYS_STORAGE[api_key]
    if not key_data['is_active']:
        return False
    
    return key_data['credits'] >= credits_needed

def use_credits(api_key: str, credits_used: int):
    """Deduct credits from user's balance"""
    if api_key in API_KEYS_STORAGE:
        API_KEYS_STORAGE[api_key]['credits'] -= credits_used

def log_request(api_key: str, endpoint: str, prompt: str = None, response_time: float = None, credits_used: int = 0):
    """Log API request for analytics"""
    REQUEST_LOGS_STORAGE.append({
        'id': len(REQUEST_LOGS_STORAGE) + 1,
        'api_key': api_key,
        'endpoint': endpoint,
        'prompt': prompt,
        'response_time': response_time,
        'credits_used': credits_used,
        'created_at': datetime.utcnow()
    })
    
    # Keep only last 1000 logs to prevent memory issues
    if len(REQUEST_LOGS_STORAGE) > 1000:
        REQUEST_LOGS_STORAGE.pop(0)

def update_usage(api_key: str):
    """Update usage statistics"""
    if api_key in API_KEYS_STORAGE:
        key_data = API_KEYS_STORAGE[api_key]
        key_data['total_requests'] += 1
        key_data['daily_requests'] += 1
        key_data['last_used'] = datetime.utcnow()

# API Routes
@app.get("/")
async def root():
    """Redirect to API documentation"""
    return RedirectResponse("/docs")

@app.get("/ffinfo")
async def ffinfo_redirect(
    uid: str = Query(..., description="User ID"),
    api_key: str = Query(..., description="Your API key")
):
    """Redirect to danger info service - COST: 1 credit per request"""
    start_time = datetime.utcnow()
    
    try:
        # Check if user has enough credits (1 credit needed)
        if not check_credits(api_key, 1):
            raise HTTPException(status_code=402, detail="Insufficient credits. This service costs 1 credit.")
        
        # Validate API key
        if api_key not in API_KEYS_STORAGE:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Replace the dangerous text with developer info
        redirect_url = f"https://danger-info-alpha.vercel.app/accinfo?uid={uid}&key=MK_DEVELOPER"
        
        # Deduct credits and log request
        response_time = (datetime.utcnow() - start_time).total_seconds()
        use_credits(api_key, 1)
        update_usage(api_key)
        log_request(api_key, "/ffinfo", f"uid={uid}", response_time, 1)
        
        return RedirectResponse(redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")

@app.get("/api_key")
async def check_api_usage(api_key: str = Query(..., description="Your API key")):
    """Check API key usage and credits"""
    try:
        if api_key not in API_KEYS_STORAGE:
            raise HTTPException(status_code=404, detail="API key not found")
        
        key_data = API_KEYS_STORAGE[api_key]
        
        # Get today's usage from logs
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_requests = sum(1 for log in REQUEST_LOGS_STORAGE 
                           if log['api_key'] == api_key and log['created_at'] >= today_start)
        
        # Get total credits used
        total_credits_used = sum(log['credits_used'] for log in REQUEST_LOGS_STORAGE if log['api_key'] == api_key)
        
        return {
            "api_key": f"{api_key[:8]}...{api_key[-4:]}",
            "name": key_data['name'],
            "is_active": key_data['is_active'],
            "usage": {
                "total_requests": key_data['total_requests'],
                "daily_used": today_requests,
                "daily_limit": key_data['daily_limit'],
                "remaining_today": max(0, key_data['daily_limit'] - today_requests)
            },
            "credits": {
                "available": key_data['credits'],
                "total_used": total_credits_used
            },
            "created_at": key_data['created_at'].isoformat(),
            "last_used": key_data['last_used'].isoformat() if key_data['last_used'] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking usage: {str(e)}")

# Free endpoints (0 credits)
@app.get("/text")
async def text_generation(
    prompt: str = Query(..., description="Text to send to AI"),
    api_key: str = Query(..., description="Your API key")
):
    """Text generation using Pollinations.ai - FREE (0 credits)"""
    start_time = datetime.utcnow()
    
    try:
        # Validate API key
        if api_key not in API_KEYS_STORAGE:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Call Pollinations.ai
        async with httpx.AsyncClient(timeout=30.0) as client:
            pollinations_url = f"https://text.pollinations.ai/prompt/{prompt}"
            response = await client.get(pollinations_url)
            response.raise_for_status()
            ai_response = response.text
            
        # Update usage and log request (0 credits)
        response_time = (datetime.utcnow() - start_time).total_seconds()
        update_usage(api_key)
        log_request(api_key, "/text", prompt, response_time, 0)
        
        # Return ONLY the AI response
        return ai_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@app.get("/image")
async def image_generation(
    prompt: str = Query(..., description="Image generation prompt"),
    api_key: str = Query(..., description="Your API key"),
    width: int = Query(512, description="Image width"),
    height: int = Query(512, description="Image height")
):
    """Image generation using Pollinations.ai - FREE (0 credits)"""
    start_time = datetime.utcnow()
    
    try:
        # Validate API key
        if api_key not in API_KEYS_STORAGE:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Return direct image URL
        direct_image_url = f"https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&nologo=true"
        
        # Update usage and log request (0 credits)
        response_time = (datetime.utcnow() - start_time).total_seconds()
        update_usage(api_key)
        log_request(api_key, "/image", prompt, response_time, 0)
        
        return direct_image_url
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image service error: {str(e)}")

@app.get("/qr")
async def qr_generation(
    text: str = Query(..., description="Text to encode in QR code"),
    api_key: str = Query(..., description="Your API key"),
    size: str = Query("150x150", description="QR code size")
):
    """QR code generation - FREE (0 credits)"""
    start_time = datetime.utcnow()
    
    try:
        # Validate API key
        if api_key not in API_KEYS_STORAGE:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Return direct QR code URL
        direct_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size={size}&data={text}"
        
        # Update usage and log request (0 credits)
        response_time = (datetime.utcnow() - start_time).total_seconds()
        update_usage(api_key)
        log_request(api_key, "/qr", text, response_time, 0)
        
        return direct_qr_url
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR code service error: {str(e)}")

@app.get("/voice")
async def voice_generation(
    text: str = Query(..., description="Text to convert to speech"),
    api_key: str = Query(..., description="Your API key"),
    voice: str = Query("alloy", description="Voice type")
):
    """Text-to-speech generation - FREE (0 credits)"""
    start_time = datetime.utcnow()
    
    try:
        # Validate API key
        if api_key not in API_KEYS_STORAGE:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Return direct voice URL
        voice_url = f"https://api.soundoftext.com/sounds/{text.lower().replace(' ', '+')}?voice={voice}"
        
        # Update usage and log request (0 credits)
        response_time = (datetime.utcnow() - start_time).total_seconds()
        update_usage(api_key)
        log_request(api_key, "/voice", text, response_time, 0)
        
        return voice_url
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice service error: {str(e)}")

# Paid endpoints (require credits)
@app.get("/num")
async def number_service(
    mobile: str = Query(..., description="Mobile number"),
    api_key: str = Query(..., description="Your API key")
):
    """Number service - COST: 5 credits"""
    start_time = datetime.utcnow()
    
    try:
        # Check if user has enough credits (5 credits needed)
        if not check_credits(api_key, 5):
            raise HTTPException(status_code=402, detail="Insufficient credits. This service costs 5 credits.")
        
        # Validate API key
        if api_key not in API_KEYS_STORAGE:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Call number service API
        async with httpx.AsyncClient(timeout=30.0) as client:
            num_url = f"https://nixonsmmapi.s77134867.workers.dev/?mobile={mobile}"
            response = await client.get(num_url)
            response.raise_for_status()
            num_response = response.text
            
        # Deduct credits and log request
        response_time = (datetime.utcnow() - start_time).total_seconds()
        use_credits(api_key, 5)
        update_usage(api_key)
        log_request(api_key, "/num", mobile, response_time, 5)
        
        return num_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Number service error: {str(e)}")

@app.get("/video")
async def video_generation(
    prompt: str = Query(..., description="Video generation prompt"),
    api_key: str = Query(..., description="Your API key")
):
    """Video generation - COST: 2 credits"""
    start_time = datetime.utcnow()
    
    try:
        # Check if user has enough credits (2 credits needed)
        if not check_credits(api_key, 2):
            raise HTTPException(status_code=402, detail="Insufficient credits. This service costs 2 credits.")
        
        # Validate API key
        if api_key not in API_KEYS_STORAGE:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Call video generation API
        async with httpx.AsyncClient(timeout=60.0) as client:
            video_url = f"https://api.yabes-desu.workers.dev/ai/tool/txt2video?prompt={prompt}"
            response = await client.get(video_url)
            response.raise_for_status()
            video_response = response.json()
            
        # Deduct credits and log request
        response_time = (datetime.utcnow() - start_time).total_seconds()
        use_credits(api_key, 2)
        update_usage(api_key)
        log_request(api_key, "/video", prompt, response_time, 2)
        
        # Process video response to match the desired format
        if isinstance(video_response, dict):
            # If response contains video_url, use it directly
            if 'video_url' in video_response:
                video_response_formatted = {
                    "video_url": video_response['video_url'],
                    "prompt": prompt,
                    "note": "Visit the URL to see your generated video"
                }
            elif 'url' in video_response:
                video_response_formatted = {
                    "video_url": video_response['url'],
                    "prompt": prompt,
                    "note": "Visit the URL to see your generated video"
                }
            else:
                # If response contains other video-related data
                video_response_formatted = {
                    "video_data": video_response,
                    "prompt": prompt,
                    "note": "Video generated successfully"
                }
        else:
            # If response is not JSON, wrap it
            video_response_formatted = {
                "video_response": str(video_response),
                "prompt": prompt,
                "note": "Video generated successfully"
            }
        
        return video_response_formatted
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video service error: {str(e)}")

# Admin Routes
@app.get("/admin/generateapi")
async def admin_generate_key(
    admin_username: str = Query(..., description="Admin username"),
    admin_password: str = Query(..., description="Admin password"),
    key_name: str = Query("User Key", description="Name for the key"),
    daily_limit: int = Query(30, description="Daily request limit"),
    initial_credits: int = Query(30, description="Initial credits")
):
    """Admin: Generate new API key"""
    try:
        if not verify_admin(admin_username, admin_password):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        new_key = generate_api_key()
        expires_at = datetime.utcnow() + timedelta(days=365)
        
        API_KEYS_STORAGE[new_key] = {
            'id': len(API_KEYS_STORAGE) + 1,
            'key': new_key,
            'name': key_name,
            'created_at': datetime.utcnow(),
            'is_active': True,
            'total_requests': 0,
            'daily_requests': 0,
            'daily_limit': daily_limit,
            'credits': initial_credits,
            'last_reset': datetime.utcnow(),
            'last_used': None,
            'expires_at': expires_at
        }
        
        return {
            "success": True,
            "api_key": new_key,
            "key_name": key_name,
            "daily_limit": daily_limit,
            "initial_credits": initial_credits,
            "expires_at": expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Key generation error: {str(e)}")

@app.get("/admin/listapi")
async def admin_list_keys(
    admin_username: str = Query(..., description="Admin username"),
    admin_password: str = Query(..., description="Admin password")
):
    """Admin: List all API keys with detailed information"""
    try:
        if not verify_admin(admin_username, admin_password):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        # Get today's usage from logs
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        keys_with_stats = []
        for api_key, key_data in API_KEYS_STORAGE.items():
            today_requests = sum(1 for log in REQUEST_LOGS_STORAGE 
                               if log['api_key'] == api_key and log['created_at'] >= today_start)
            
            total_credits_used = sum(log['credits_used'] for log in REQUEST_LOGS_STORAGE if log['api_key'] == api_key)
            
            keys_with_stats.append({
                "id": key_data['id'],
                "name": key_data['name'],
                "key": key_data['key'],
                "is_active": key_data['is_active'],
                "total_requests": key_data['total_requests'],
                "daily_used": today_requests,
                "daily_limit": key_data['daily_limit'],
                "credits_available": key_data['credits'],
                "credits_used": total_credits_used,
                "created_at": key_data['created_at'].isoformat(),
                "last_used": key_data['last_used'].isoformat() if key_data['last_used'] else None,
                "expires_at": key_data['expires_at'].isoformat()
            })
        
        return {
            "total_keys": len(keys_with_stats),
            "keys": keys_with_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List keys error: {str(e)}")

@app.get("/admin/addcredits")
async def admin_add_credits(
    admin_username: str = Query(..., description="Admin username"),
    admin_password: str = Query(..., description="Admin password"),
    api_key: str = Query(..., description="API key to modify"),
    credits_to_add: int = Query(10, description="Credits to add")
):
    """Admin: Add credits to an API key"""
    try:
        if not verify_admin(admin_username, admin_password):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        if api_key not in API_KEYS_STORAGE:
            raise HTTPException(status_code=404, detail="API key not found")
        
        old_balance = API_KEYS_STORAGE[api_key]['credits']
        API_KEYS_STORAGE[api_key]['credits'] += credits_to_add
        
        return {
            "success": True,
            "message": f"Added {credits_to_add} credits to key {api_key[:8]}...",
            "new_credit_balance": API_KEYS_STORAGE[api_key]['credits']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Add credits error: {str(e)}")

@app.get("/admin/stats")
async def admin_stats(
    admin_username: str = Query(..., description="Admin username"),
    admin_password: str = Query(..., description="Admin password")
):
    """Admin: Overall system statistics"""
    try:
        if not verify_admin(admin_username, admin_password):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        # Basic stats
        total_keys = len(API_KEYS_STORAGE)
        active_keys = sum(1 for key_data in API_KEYS_STORAGE.values() if key_data['is_active'])
        total_requests = sum(key_data['total_requests'] for key_data in API_KEYS_STORAGE.values())
        total_credits_used = sum(log['credits_used'] for log in REQUEST_LOGS_STORAGE)
        
        # Today's stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_requests = sum(1 for log in REQUEST_LOGS_STORAGE if log['created_at'] >= today_start)
        
        # Top users
        from collections import defaultdict
        user_requests = defaultdict(int)
        for log in REQUEST_LOGS_STORAGE:
            if log['created_at'] >= today_start:
                user_requests[log['api_key']] += 1
        
        top_users = sorted(user_requests.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "system_stats": {
                "total_api_keys": total_keys,
                "active_keys": active_keys,
                "total_requests_all_time": total_requests,
                "total_credits_used": total_credits_used,
                "requests_today": today_requests
            },
            "top_users_today": [
                {"api_key": user[0][:8] + "...", "requests": user[1]}
                for user in top_users
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "api_keys_count": len(API_KEYS_STORAGE),
        "logs_count": len(REQUEST_LOGS_STORAGE)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)