# SMART SPEND FIN 💰
### AI-Powered Smart Financial Wellness Platform

Built for the hackathon — a full-stack platform that uses 6 proprietary AI/ML engines to give users personalized, data-driven financial insights.

---

## 🚀 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Recharts, DM Mono + Syne fonts |
| Backend | FastAPI, Python 3.13, SQLAlchemy |
| Database | PostgreSQL |
| ML/AI | scikit-learn (Isolation Forest), scipy, numpy |
| Auth | JWT (python-jose), bcrypt 4.0.1 |

---

## 🤖 6 AI Engines

| Engine | Method | What it does |
|--------|--------|-------------|
| Salary Allocation | Rule-based priority budgeting | Optimally splits income across EMIs, savings, investments |
| What-If Simulation | Monte Carlo (500 runs) + compound interest | Projects balance impact of any financial decision |
| Financial Stress Index | Isolation Forest + 5 statistical signals (hybrid) | 0–100 stress score from spending patterns |
| Goal Probability | Monte Carlo (2000 trials, Normal distribution) | Probability of hitting a savings goal by deadline |
| Lifestyle Inflation | Isolation Forest + % change vs income | Detects spending creep in discretionary categories |
| Debt Optimizer | Iterative amortization simulation | Avalanche vs Snowball strategy comparison |

---

## ⚙️ Running Locally

### Prerequisites
- Python 3.13+
- Node.js 18+
- PostgreSQL 14+

### 1. Database
```sql
CREATE DATABASE zenith_fintech;
```

Create `backend/.env`:
### 2. Backend
```bash
cd backend
pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary
pip install python-jose[cryptography] passlib bcrypt==4.0.1
pip install scikit-learn scipy numpy email-validator
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
npm start
```
App: http://localhost:3000

> Both terminals must stay open simultaneously.

---

## 📁 Project Structure
POST /auth/register          → create account
POST /auth/login             → get JWT token
POST /ai/salary-allocation   → run salary engine
GET  /ai/stress-index        → run stress engine
POST /ai/what-if-simulation  → run simulation
POST /ai/goal-probability    → run Monte Carlo
GET  /ai/lifestyle-inflation → run inflation detector
POST /ai/debt-optimization   → run debt planner

---

## 🚀 Deployment

- **Backend** → Railway (set root directory to `backend`)
- **Frontend** → Vercel (set root directory to `frontend`)
- **Database** → Railway PostgreSQL

---

## ⚠️ Known Setup Notes

- `bcrypt` must be pinned to `4.0.1` for Python 3.13 compatibility
- JWT tokens expire after 40 minutes — log out and back in if you see 401 errors
- Stress Index and Lifestyle Inflation need at least 2 months of transaction data