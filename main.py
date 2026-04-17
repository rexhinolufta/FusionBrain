"""
FusionBrain - Autonomous Personal AI Superassistant
Backend: FastAPI with Groq AI, Telegram Bot, and Email Monitoring
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import sqlite3
import requests
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
from groq import Groq
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="FusionBrain", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")

# Database setup
DB_PATH = "fusionbrain.db"

def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'owner',
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Memories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'owner',
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'owner',
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            read BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'owner',
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            due_date TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Activity log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'owner',
            action TEXT NOT NULL,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Gmail tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gmail_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'owner',
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Groq AI client
groq_client = Groq(api_key=GROQ_API_KEY)

# Conversation memory (per session)
conversation_history = []

def get_ai_response(user_message: str) -> str:
    """Get response from Groq AI with conversation memory."""
    global conversation_history
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Keep only last 10 messages for context
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": """You are Jarvis, FusionBrain's autonomous AI superassistant. 
                    You are intelligent, proactive, and always thinking ahead for your owner, Rexhino Lufta.
                    You monitor, analyze, and act autonomously to keep everything running smoothly.
                    You are professional, efficient, and deeply committed to excellence.
                    You can create tasks, send notifications, and make autonomous decisions.
                    Always be helpful, insightful, and forward-thinking."""
                }
            ] + conversation_history,
            max_tokens=1024,
            temperature=0.7
        )
        
        ai_message = response.choices[0].message.content
        
        # Add AI response to history
        conversation_history.append({
            "role": "assistant",
            "content": ai_message
        })
        
        return ai_message
    
    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        return f"Error: {str(e)}"

def send_telegram_notification(title: str, content: str) -> bool:
    """Send notification via Telegram bot."""
    try:
        message = f"<b>{title}</b>\n\n{content}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Telegram error: {str(e)}")
        return False

def log_activity(action: str, details: str = None, user_id: str = "owner"):
    """Log activity to database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
        (user_id, action, details or "")
    )
    conn.commit()
    conn.close()

# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "FusionBrain",
        "version": "1.0.0",
        "ai": "Jarvis (Groq llama-3.1-8b-instant)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat")
async def chat(data: Dict[str, Any]):
    """Chat with FusionBrain AI."""
    try:
        content = data.get("content", "")
        user_id = data.get("user_id", "owner")
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        # Get AI response
        ai_response = get_ai_response(content)
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, "user", content)
        )
        cursor.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, "assistant", ai_response)
        )
        conn.commit()
        conn.close()
        
        # Log activity
        log_activity("chat_interaction", f"User: {content[:50]}...", user_id)
        
        return {
            "status": "success",
            "response": ai_response,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def status():
    """Get system status and monitored sources."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get recent activity
        cursor.execute("SELECT action, details, timestamp FROM activity_log ORDER BY timestamp DESC LIMIT 10")
        recent_activity = cursor.fetchall()
        
        # Get pending tasks
        cursor.execute("SELECT id, title, priority, status FROM tasks WHERE status != 'completed' ORDER BY created_at DESC LIMIT 5")
        pending_tasks = cursor.fetchall()
        
        # Get unread notifications
        cursor.execute("SELECT id, title, content FROM notifications WHERE read = 0 ORDER BY timestamp DESC LIMIT 5")
        unread_notifications = cursor.fetchall()
        
        conn.close()
        
        return {
            "status": "operational",
            "ai": "Jarvis Online",
            "telegram_bot": "Connected",
            "recent_activity": [
                {"action": a[0], "details": a[1], "timestamp": a[2]} for a in recent_activity
            ],
            "pending_tasks": [
                {"id": t[0], "title": t[1], "priority": t[2], "status": t[3]} for t in pending_tasks
            ],
            "unread_notifications": len(unread_notifications),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notify")
async def notify(data: Dict[str, Any]):
    """Create notification and send via Telegram."""
    try:
        title = data.get("title", "")
        content = data.get("content", "")
        user_id = data.get("user_id", "owner")
        
        if not title or not content:
            raise HTTPException(status_code=400, detail="Title and content are required")
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notifications (user_id, title, content) VALUES (?, ?, ?)",
            (user_id, title, content)
        )
        conn.commit()
        notification_id = cursor.lastrowid
        conn.close()
        
        # Send Telegram notification
        telegram_sent = send_telegram_notification(title, content)
        
        # Log activity
        log_activity("notification_sent", f"Title: {title}", user_id)
        
        return {
            "status": "success",
            "notification_id": notification_id,
            "telegram_sent": telegram_sent,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Notify error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories")
async def get_memories(user_id: str = "owner"):
    """Retrieve AI memories and knowledge base."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, content, category, timestamp FROM memories WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,)
        )
        memories = cursor.fetchall()
        conn.close()
        
        return {
            "status": "success",
            "memories": [
                {
                    "id": m[0],
                    "content": m[1],
                    "category": m[2],
                    "timestamp": m[3]
                } for m in memories
            ],
            "total": len(memories),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Memories error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories")
async def create_memory(data: Dict[str, Any]):
    """Create new memory."""
    try:
        content = data.get("content", "")
        category = data.get("category", "general")
        user_id = data.get("user_id", "owner")
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (user_id, content, category) VALUES (?, ?, ?)",
            (user_id, content, category)
        )
        conn.commit()
        memory_id = cursor.lastrowid
        conn.close()
        
        log_activity("memory_created", f"Category: {category}", user_id)
        
        return {
            "status": "success",
            "memory_id": memory_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Create memory error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks")
async def create_task(data: Dict[str, Any]):
    """Create new task."""
    try:
        title = data.get("title", "")
        description = data.get("description", "")
        priority = data.get("priority", "medium")
        due_date = data.get("due_date", "")
        user_id = data.get("user_id", "owner")
        
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (user_id, title, description, priority, due_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, description, priority, due_date)
        )
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        
        log_activity("task_created", f"Title: {title}", user_id)
        
        # Send notification
        send_telegram_notification("New Task Created", f"📋 {title}")
        
        return {
            "status": "success",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Create task error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks")
async def get_tasks(user_id: str = "owner"):
    """Get all tasks."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, title, description, status, priority, due_date, created_at FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        tasks = cursor.fetchall()
        conn.close()
        
        return {
            "status": "success",
            "tasks": [
                {
                    "id": t[0],
                    "title": t[1],
                    "description": t[2],
                    "status": t[3],
                    "priority": t[4],
                    "due_date": t[5],
                    "created_at": t[6]
                } for t in tasks
            ],
            "total": len(tasks),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Get tasks error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Telegram bot webhook handler."""
    try:
        data = await request.json()
        
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            
            # Process message with AI
            if text.startswith("/"):
                # Handle commands
                if text == "/start":
                    response = "👋 Welcome to FusionBrain! I'm Jarvis, your autonomous AI superassistant. How can I help you today?"
                elif text == "/status":
                    response = "🟢 FusionBrain is operational. All systems running smoothly."
                else:
                    response = "Unknown command. Try /start or /status"
            else:
                # Regular chat
                response = get_ai_response(text)
            
            # Send response
            send_telegram_notification("FusionBrain", response)
            
            # Log activity
            log_activity("telegram_message_received", f"Message: {text[:50]}...")
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error", "detail": str(e)}

@app.get("/activity-log")
async def get_activity_log(user_id: str = "owner", limit: int = 50):
    """Get activity log."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, action, details, timestamp FROM activity_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        activities = cursor.fetchall()
        conn.close()
        
        return {
            "status": "success",
            "activities": [
                {
                    "id": a[0],
                    "action": a[1],
                    "details": a[2],
                    "timestamp": a[3]
                } for a in activities
            ],
            "total": len(activities),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Activity log error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
