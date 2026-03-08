# NexusAI — AI Chatbot & Automation Platform

<p align="center">
  <strong>🤖 Intelligent Conversations + ⚡ Workflow Automation + 📊 Analytics</strong>
</p>

A full-stack AI-powered platform combining real-time conversational AI (OpenAI GPT-4o), workflow automation, and analytics dashboards. Built with **Flask**, **React**, **Redux**, and **PostgreSQL**.

---

## ✨ Features

- **AI Chat** — Multi-turn conversations with context retention, streaming, and auto-titling
- **Automation Engine** — Create workflows with triggers (webhook, schedule, manual, event)
- **Analytics Dashboard** — Charts for conversation metrics, automation runs, and user engagement
- **Admin Dashboard** — User management, system overview, and health monitoring
- **JWT Authentication** — Secure login/register with role-based access control
- **WebSocket Support** — Real-time message streaming and typing indicators
- **Mock Mode** — Works without OpenAI API key for development

---

## 🏗️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Redux Toolkit, React Router, Recharts, Vite |
| **Backend** | Flask, SQLAlchemy, Flask-JWT-Extended, Flask-SocketIO |
| **Database** | SQLite (dev) / PostgreSQL (production) |
| **Cache/Queue** | Redis |
| **AI** | OpenAI GPT-4o / GPT-4o-mini |
| **DevOps** | Docker, Docker Compose, Gunicorn |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) Docker & Docker Compose

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment (edit .env to add your OpenAI key)
copy .env.example .env

# Start the backend
python wsgi.py
```

### 2. Seed Database (Optional)

```bash
cd backend
python seed.py
```

This creates:
- **Admin**: admin@chatbot.com / admin123!
- **Operator**: operator@chatbot.com / operator123!
- **Demo User**: demo@chatbot.com / demo1234!

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Open the App

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/health

### Docker Deployment (Alternative)

```bash
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

---

## 📁 Project Structure

```
chatbot/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── config.py            # Configuration
│   │   ├── extensions.py        # Flask extensions
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routes/              # API blueprints
│   │   ├── services/            # Business logic
│   │   ├── middleware/          # Auth & rate limiting
│   │   └── utils/               # Helpers & errors
│   ├── wsgi.py                  # Entry point
│   ├── seed.py                  # Database seeder
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/          # Reusable UI components
│       ├── pages/               # Route pages
│       ├── store/               # Redux slices
│       ├── services/            # API client
│       ├── App.jsx              # Router & layout
│       └── index.css            # Design system
├── docker-compose.yml
└── README.md
```

---

## 🔐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login & get JWT tokens |
| `POST` | `/api/chat/conversations` | Create conversation |
| `POST` | `/api/chat/conversations/:id/messages` | Send message & get AI response |
| `POST` | `/api/automation/workflows` | Create workflow |
| `POST` | `/api/automation/workflows/:id/trigger` | Trigger workflow |
| `GET` | `/api/analytics/overview` | Dashboard metrics |

---

## 🧩 Configuration

Set these in `backend/.env`:

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key | *(empty = mock mode)* |
| `OPENAI_MODEL` | Primary model | `gpt-4o` |
| `DATABASE_URL` | Database connection string | `sqlite:///chatbot_dev.db` |
| `JWT_SECRET_KEY` | Secret for JWT tokens | dev key |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:5173` |

---

## 📋 License

MIT
