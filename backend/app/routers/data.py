from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import User, Loan, Goal
from app.schemas.schemas import LoanCreate, LoanOut, GoalCreate, GoalOut
from app.services.auth_service import get_current_user

loans_router = APIRouter(prefix="/loans", tags=["Loans"])
goals_router = APIRouter(prefix="/goals", tags=["Goals"])


# ── Loans ─────────────────────────────────────────────────────────────────────

@loans_router.post("/", response_model=LoanOut, status_code=201)
def create_loan(payload: LoanCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    loan = Loan(user_id=user.id, **payload.model_dump())
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


@loans_router.get("/", response_model=List[LoanOut])
def list_loans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Loan).filter(Loan.user_id == user.id).all()


@loans_router.delete("/{loan_id}", status_code=204)
def delete_loan(loan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == user.id).first()
    if not loan:
        raise HTTPException(404, "Loan not found.")
    db.delete(loan)
    db.commit()


# ── Goals ─────────────────────────────────────────────────────────────────────

@goals_router.post("/", response_model=GoalOut, status_code=201)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    goal = Goal(user_id=user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@goals_router.get("/", response_model=List[GoalOut])
def list_goals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Goal).filter(Goal.user_id == user.id).all()


@goals_router.put("/{goal_id}/contribute", response_model=GoalOut)
def contribute_to_goal(
    goal_id: int,
    amount: float,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(404, "Goal not found.")
    goal.current_amount += amount
    db.commit()
    db.refresh(goal)
    return goal


@goals_router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(404, "Goal not found.")
    db.delete(goal)
    db.commit()
