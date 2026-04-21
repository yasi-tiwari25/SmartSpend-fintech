from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import User, Transaction
from app.schemas.schemas import TransactionCreate, TransactionOut
from app.services.auth_service import get_current_user
from app.engines import transaction_categorizer  # ← add this import

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionOut, status_code=201)
@router.post("/", response_model=TransactionOut, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = payload.model_dump()

    # Auto-categorize from description
    if data.get("description"):
        result = transaction_categorizer.classify(data["description"])
        data["category"] = result["category"]

    t = Transaction(user_id=user.id, **data)
    db.add(t)

    # ← NEW: update monthly income if salary transaction
    if data.get("category") == "salary" and data.get("type") == "income":
        user.monthly_income = data["amount"]
        db.add(user)

    db.commit()
    db.refresh(t)
    return t


@router.get("/", response_model=List[TransactionOut])
def list_transactions(
    limit: int = 100,
    offset: int = 0,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Transaction).filter(Transaction.user_id == user.id)
    if type:
        q = q.filter(Transaction.type == type)
    return q.order_by(Transaction.date.desc()).offset(offset).limit(limit).all()


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = db.query(Transaction).filter(
        Transaction.id == transaction_id, Transaction.user_id == user.id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    db.delete(t)
    db.commit()
