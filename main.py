"""
FusionBrain - Autonomous Personal AI Superassistant
Backend: Flask with Groq AI, Telegram Bot, Memory Management
"""

from flask import Flask, request, jsonify
import os
import json
import sqlite3
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from groq import Groq
import logging
from memory import MemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")

# Initialize Memory Manager
memory_manager = MemoryManager()

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

@app.route("/", methods=["GET"])
def root():
    """Health check endpoint."""
    return jsonify({
        "status": "online",
        "service": "FusionBrain",
        "version": "2.0.0",
        "ai": "Jarvis (Groq llama-3.1-8b-instant)",
        "memory": "JSON-based persistent storage",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/chat", methods=["POST"])
def chat():
    """Chat with FusionBrain AI."""
    try:
        data = request.get_json()
        content = data.get("content", "")
        user_id = data.get("user_id", "owner")
        
        if not content:
            return jsonify({"error": "Content is required"}), 400
        
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
        
        return jsonify({
            "status": "success",
            "response": ai_response,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """Get system status and monitored sources."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get recent activity
        cursor.execute("SELECT action, details, timestamp FROM activity_log ORDER BY timestamp DESC LIMIT 10")
        recent_activity = cursor.fetchall()
        
        # Get unread notifications
        cursor.execute("SELECT id, title, content FROM notifications WHERE read = 0 ORDER BY timestamp DESC LIMIT 5")
        unread_notifications = cursor.fetchall()
        
        conn.close()
        
        # Get task stats
        task_stats = memory_manager.get_task_stats()
        pending_tasks = memory_manager.get_pending_tasks()
        
        return jsonify({
            "status": "operational",
            "ai": "Jarvis Online",
            "telegram_bot": "Connected",
            "recent_activity": [
                {"action": a[0], "details": a[1], "timestamp": a[2]} for a in recent_activity
            ],
            "task_stats": task_stats,
            "pending_tasks_count": len(pending_tasks),
            "unread_notifications": len(unread_notifications),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/notify", methods=["POST"])
def notify():
    """Create notification and send via Telegram."""
    try:
        data = request.get_json()
        title = data.get("title", "")
        content = data.get("content", "")
        user_id = data.get("user_id", "owner")
        
        if not title or not content:
            return jsonify({"error": "Title and content are required"}), 400
        
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
        
        return jsonify({
            "status": "success",
            "notification_id": notification_id,
            "telegram_sent": telegram_sent,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Notify error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/memories", methods=["GET"])
def get_memories():
    """Retrieve AI memories and knowledge base."""
    try:
        facts = memory_manager.get_all_facts()
        owner_info = memory_manager.get_owner_info()
        
        return jsonify({
            "status": "success",
            "owner": owner_info["owner"],
            "facts": facts,
            "facts_count": len(facts),
            "preferences": owner_info["preferences"],
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Memories error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/memories", methods=["POST"])
def create_memory():
    """Create new memory (fact)."""
    try:
        data = request.get_json()
        key = data.get("key", "")
        value = data.get("value", "")
        
        if not key or not value:
            return jsonify({"error": "Key and value are required"}), 400
        
        result = memory_manager.remember_fact(key, value)
        log_activity("memory_created", f"Key: {key}")
        
        return jsonify({
            "status": "success",
            "message": result,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Create memory error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/tasks", methods=["POST"])
def create_task():
    """Create new task."""
    try:
        data = request.get_json()
        title = data.get("title", "")
        description = data.get("description", "")
        priority = data.get("priority", "medium")
        due_date = data.get("due_date", None)
        
        if not title:
            return jsonify({"error": "Title is required"}), 400
        
        result = memory_manager.add_task(title, description, priority, due_date)
        log_activity("task_created", f"Title: {title}")
        
        # Send notification
        send_telegram_notification("New Task Created", f"📋 {title} (Priority: {priority})")
        
        return jsonify({
            "status": "success",
            "message": result,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Create task error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/tasks", methods=["GET"])
def get_tasks():
    """Get all tasks."""
    try:
        status_filter = request.args.get("status", "all")
        tasks = memory_manager.load_tasks()
        
        if status_filter != "all":
            tasks = [t for t in tasks if t["status"] == status_filter]
        
        stats = memory_manager.get_task_stats()
        
        return jsonify({
            "status": "success",
            "tasks": tasks,
            "total": len(tasks),
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Get tasks error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    """Mark task as completed."""
    try:
        result = memory_manager.complete_task(task_id)
        log_activity("task_completed", f"Task ID: {task_id}")
        
        send_telegram_notification("Task Completed", f"✓ Task {task_id} has been marked as completed!")
        
        return jsonify({
            "status": "success",
            "message": result,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Complete task error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task."""
    try:
        result = memory_manager.delete_task(task_id)
        log_activity("task_deleted", f"Task ID: {task_id}")
        
        return jsonify({
            "status": "success",
            "message": result,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Delete task error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/briefing", methods=["GET"])
def daily_briefing():
    """Get daily briefing."""
    try:
        briefing = memory_manager.daily_briefing()
        
        return jsonify({
            "status": "success",
            "briefing": briefing,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Briefing error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    """Telegram bot webhook handler."""
    try:
        data = request.get_json()
        
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
                    stats = memory_manager.get_task_stats()
                    response = f"🟢 FusionBrain is operational.\n\n📊 Tasks: {stats['total']} total, {stats['completed']} completed, {stats['pending']} pending"
                elif text == "/briefing":
                    response = memory_manager.daily_briefing()
                elif text == "/tasks":
                    response = memory_manager.list_tasks()
                else:
                    response = "Unknown command. Try /start, /status, /briefing, or /tasks"
            else:
                # Regular chat
                response = get_ai_response(text)
            
            # Send response
            send_telegram_notification("FusionBrain", response)
            
            # Log activity
            log_activity("telegram_message_received", f"Message: {text[:50]}...")
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.route("/activity-log", methods=["GET"])
def get_activity_log():
    """Get activity log."""
    try:
        user_id = request.args.get("user_id", "owner")
        limit = request.args.get("limit", 50, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, action, details, timestamp FROM activity_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        activities = cursor.fetchall()
        conn.close()
        
        return jsonify({
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
        })
    
    except Exception as e:
        logger.error(f"Activity log error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
