from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth, transactions, ai_engines
from app.routers.data import loans_router, goals_router
from app.models import models  # noqa: ensure models are registered

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zenith Fintech API",
    description="AI-powered Smart Financial Wellness Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(loans_router)
app.include_router(goals_router)
app.include_router(ai_engines.router)


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": "Zenith Fintech",
        "version": "1.0.0",
        "engines": [
            "salary-allocation",
            "what-if-simulation",
            "stress-index",
            "goal-probability",
            "lifestyle-inflation",
            "debt-optimization",
        ],
    }
