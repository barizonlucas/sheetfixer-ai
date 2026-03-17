# Ekual 🟰

Ekual is a smart spreadsheet assistant that helps you generate precise formulas and scripts for Excel, Google Sheets, VBA, and Apps Script using AI (Google Gemini 2.5). 

This project features a decoupled architecture, with a robust RESTful API backend and a modern Single Page Application (SPA) frontend.

## 🏗️ Architecture & Stack

- **Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic.
- **Frontend:** React.js (v18), Vite, Tailwind CSS.
- **AI Integration:** Google Gemini API (`gemini-2.5-flash`).

## ✨ Features

- **Smart Assistant:** Describe your problem in plain English (or other languages) and get the right formula or code.
- **Multi-language Support:** The interface and AI responses are fully available in English, Portuguese (with local Pix donation support), and Spanish.
- **Tool Support:** Context-aware prompts tailored for Excel (modern 365), Google Sheets, VBA, and Apps Script.
- **Beautiful UI:** Dark mode by default, creative loading states, and Markdown parsing for explanations.

## 🚀 How to Run Locally

### Prerequisites
- Node.js (v20+)
- Python (v3.11+)

### 1. Backend Setup (FastAPI)

Open a terminal and navigate to the backend folder:

```bash
cd backend

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file inside the `backend/` directory and add your Gemini API key:
```env
GEMINI_API_KEY='YOUR_GEMINI_API_KEY'
BMC_LINK='https://buymeacoffee.com/yourlink' # Optional
```

Start the backend server:
```bash
uvicorn app:app --reload
```
*The API will be available at `http://localhost:8000`*

### 2. Frontend Setup (React + Vite)

Open a new terminal and navigate to the frontend folder:

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
*The frontend will be available at `http://localhost:5173`*

## 🌍 Environment Variables

### Frontend (`frontend/.env.production`)
- `VITE_API_URL`: The URL of your backend API in production. 
  - Defaults to `http://localhost:8000/api` during local development.
  - Set this in your deployment platform (e.g., Vercel, Netlify) to your production backend URL (e.g., `https://api.yourdomain.com/api`).

## 📦 Deployment

### Backend
The backend can be containerized using Docker or deployed directly to services like Render, Heroku, or AWS. Ensure the start command is:
`uvicorn app:app --host 0.0.0.0 --port 8000`

### Frontend
To build the frontend for production, run `npm run build` inside the `frontend/` directory. This will generate a `dist` folder containing static files that can be easily hosted on Vercel, Netlify, AWS S3, or Cloudflare Pages.
