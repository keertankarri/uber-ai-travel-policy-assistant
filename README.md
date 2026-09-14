# 🧳 Uber Travel Assistant (AI Policy & Expense Bot)

An enterprise-ready AI Travel Assistant built to streamline corporate travel policies and expense tracking. This project features a dual-interface system: an intelligent **Slack Bot** for instant policy resolution and a **Web Dashboard** for financial analytics and expense logging. 

**🚀 Live Deployment:** [https://web-production-2c7d2c.up.railway.app/]

---

## ⚡ Key Features

* **Advanced Slackbot Integration:** Interacts with employees directly in Slack via Direct Messages and Channel mentions to answer complex travel policy questions.
* **Intelligent AI Processing:** Utilizes LangGraph and a FAISS vector database to retrieve, synthesize, and provide accurate answers based on internal corporate guidelines.
* **Stateful User Mapping:** Dynamically prompts unlinked Slack users for their corporate Employee ID and caches the connection for personalized, persistent chat sessions.
* **Role-Based Access Control (RBAC):** Distinct dashboards for standard employees (personal expenses) and administrators (company-wide spending analytics).
* **Interactive Analytics:** Visualizes departmental spend breakdowns and timeline-based financial metrics using Chart.js.

---

## 🤖 Slackbot Integration Details

The core of this application relies on a seamless integration with Slack, powered by the official **Slack Bolt Framework** and Python's threading capabilities. 

* **Event Handling:** Listens for `app_mention` (for channel tags) and `message.im` (for direct messages) via a secure HTTP webhook endpoint (`/slack/events`).
* **Regex Filtering:** Automatically parses and strips Slack user ID tags (e.g., `<@U12345>`) from channel mentions to ensure the AI agent receives clean text prompts.
* **Asynchronous Threading:** To comply with Slack's strict 3-second webhook acknowledgment timeout, the bot instantly replies with a placeholder message while offloading the heavy AI/LangGraph processing to a background Python thread.

---

## 🏗️ Tech Stack

* **Backend:** Python, Flask, Flask-Session
* **Database:** SQLAlchemy (SQLite for development / PostgreSQL for production)
* **AI Engine:** LangGraph, FAISS Vector DB, Google Gemini API
* **Slack SDK:** Slack Bolt for Python (`slack_bolt`)
* **Frontend:** HTML5, CSS3, Chart.js
* **Deployment:** Railway

---

## 🔑 Environment Variables

To run this project locally or in production, create a `.env` file in the root directory (or add these to your Railway variables):

| Variable | Description |
| :--- | :--- |
| `SLACK_BOT_TOKEN` | Bot User OAuth Token (`xoxb-...`) with `chat:write` permissions |
| `SLACK_SIGNING_SECRET` | Secret key to verify incoming Slack events |
| `GOOGLE_API_KEY` | API Key for LLM processing |
| `FLASK_SECRET_KEY` | Random string used to sign session cookies |
| `DATABASE_URL` | *(Optional)* PostgreSQL connection string |

---

## 🚀 Local Development Setup

**1. Clone the repository**
```bash
git clone [https://github.com/keertankarri/uber-ai-travel-policy-assistant](https://github.com/keertankarri/uber-ai-travel-policy-assistant)
cd uber-travel-assistant