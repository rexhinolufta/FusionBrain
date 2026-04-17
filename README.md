# FusionBrain Backend

**FusionBrain** is an autonomous personal AI superassistant that acts as your 24/7 command center. This is the backend service built with FastAPI, Groq AI, and Telegram integration.

## 🚀 Features

- **AI Chat Interface** — Conversational AI with Groq (llama-3.1-8b-instant model)
- **Telegram Bot Integration** — Direct messaging with Jarvis personality
- **Task Management** — Create, track, and manage tasks autonomously
- **Memory & Knowledge Base** — Persistent AI memory for personalized interactions
- **Activity Logging** — Chronological audit trail of all AI actions
- **Notifications** — Real-time alerts via Telegram
- **Status Monitoring** — System health and activity overview

## 📋 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check & service info |
| GET | `/health` | Health status |
| POST | `/chat` | Chat with AI (Jarvis) |
| GET | `/status` | System status & monitored sources |
| POST | `/notify` | Create notification |
| GET | `/memories` | Retrieve AI memories |
| POST | `/memories` | Create new memory |
| POST | `/tasks` | Create new task |
| GET | `/tasks` | Get all tasks |
| GET | `/activity-log` | Activity audit trail |
| POST | `/telegram/webhook` | Telegram bot webhook |

## 🔧 Setup & Deployment

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rexhinolufta/FusionBrain.git
   cd FusionBrain
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```
   GROQ_API_KEY=your_groq_api_key
   TELEGRAM_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   GMAIL_CLIENT_ID=your_gmail_client_id
   GMAIL_CLIENT_SECRET=your_gmail_client_secret
   PORT=8000
   ```

5. **Run the server:**
   ```bash
   python main.py
   ```

   The server will start at `http://localhost:8000`

### Deploy to Render.com

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Initial FusionBrain backend"
   git push origin main
   ```

2. **Connect to Render:**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select branch: `main`
   - Runtime: `Python`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables:**
   - GROQ_API_KEY
   - TELEGRAM_TOKEN
   - TELEGRAM_CHAT_ID
   - GMAIL_CLIENT_ID
   - GMAIL_CLIENT_SECRET
   - PORT=8000

4. **Deploy** — Render will automatically deploy on push

## 📡 Telegram Bot Setup

1. **Create bot via @BotFather:**
   - Open Telegram and search for @BotFather
   - Send `/newbot`
   - Follow instructions
   - Copy the bot token

2. **Set webhook:**
   ```bash
   curl -X POST "https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook" \
     -d "url=https://your-render-url/telegram/webhook"
   ```

## 🧠 AI Configuration

- **Model:** Groq llama-3.1-8b-instant
- **Personality:** Jarvis (intelligent, proactive, professional)
- **Memory:** Conversation history (last 10 messages)
- **Response Time:** < 1 second

## 📧 Gmail Integration (Coming Soon)

- OAuth2 authentication
- Email monitoring every 10 minutes
- Important email filtering
- Telegram notifications

## 🗄️ Database

- **Type:** SQLite (local file: `fusionbrain.db`)
- **Tables:**
  - `chat_history` — Conversation logs
  - `memories` — AI knowledge base
  - `notifications` — Alert history
  - `tasks` — Task management
  - `activity_log` — Action audit trail
  - `gmail_tokens` — Gmail OAuth tokens

## 🔐 Security

- Environment variables for all secrets
- No hardcoded credentials
- CORS enabled for frontend integration
- Activity logging for audit trail

## 📊 Example Requests

### Chat with AI
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "What are my tasks for today?"}'
```

### Create Task
```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "Review emails", "priority": "high", "due_date": "2026-04-18"}'
```

### Send Notification
```bash
curl -X POST "http://localhost:8000/notify" \
  -H "Content-Type: application/json" \
  -d '{"title": "Important", "content": "You have a new email from John"}'
```

### Get System Status
```bash
curl "http://localhost:8000/status"
```

## 🛠️ Development

### Project Structure
```
FusionBrain-Backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Procfile            # Render deployment config
├── render.yaml         # Render configuration
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

### Adding New Features

1. Add new database tables to `init_db()`
2. Create Pydantic models for request/response
3. Add new endpoints in `main.py`
4. Test locally with curl or Postman
5. Push to GitHub and Render will auto-deploy

## 📝 Logging

All activities are logged to the database:
- Chat interactions
- Task creation/updates
- Notifications sent
- Telegram messages
- System events

Access logs via `/activity-log` endpoint.

## 🚨 Troubleshooting

### Bot not responding
- Check `TELEGRAM_TOKEN` is correct
- Verify webhook URL is set
- Check Render logs for errors

### AI not responding
- Verify `GROQ_API_KEY` is valid
- Check Groq API quota
- Review Render logs

### Database errors
- Ensure `fusionbrain.db` has write permissions
- Check disk space on Render
- Verify database tables are created

## 📞 Support

For issues or questions, check the logs:
```bash
# View Render logs
# Go to Render dashboard → Your service → Logs
```

## 📄 License

MIT License - Feel free to use and modify

## 🎯 Next Steps

- [ ] Gmail email monitoring integration
- [ ] Hotmail/Outlook integration
- [ ] Voice activation (Whisper API)
- [ ] Scheduled background jobs
- [ ] Advanced analytics dashboard
- [ ] Multi-source data aggregation

---

**Built with ❤️ by Manus AI for Rexhino Lufta**

**FusionBrain v1.0.0** — Your autonomous AI superassistant
