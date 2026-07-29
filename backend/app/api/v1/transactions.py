from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


class BalanceError(Exception):
    pass


def _update_account_balance(
    account: Account,
    old_amount: float,
    old_type: str,
    new_amount: float,
    new_type: str,
) -> None:
    if old_type == "income":
        account.balance -= old_amount
    else:
        account.balance += old_amount

    if new_type == "expense" and account.balance < new_amount:
        if old_type == "income":
            account.balance += old_amount
        else:
            account.balance -= old_amount
        raise BalanceError("Insufficient funds")

    if new_type == "income":
        account.balance += new_amount
    else:
        account.balance -= new_amount


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    account_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    )

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if type is not None:
        query = query.filter(Transaction.type == type)
    if date_from is not None:
        query = query.filter(Transaction.date >= date_from)
    if date_to is not None:
        query = query.filter(Transaction.date <= date_to)

    query = query.order_by(
        Transaction.date.desc(),
        Transaction.created_at.desc()
    )
    query = query.offset(offset).limit(limit)
    return query.all()


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(
        Account.id == payload.account_id,
        Account.user_id == current_user.id,
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account not found or does not belong to user",
        )

    if payload.category_id is not None:
        category = db.query(Category).filter(
            Category.id == payload.category_id,
            Category.user_id == current_user.id,
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or does not belong to user",
            )

    transaction = Transaction(
        user_id=current_user.id,
        account_id=payload.account_id,
        category_id=payload.category_id,
        type=payload.type,
        amount=payload.amount,
        currency=account.currency,
        description=payload.description,
        notes=payload.notes,
        date=payload.date,
        is_recurring=payload.is_recurring,
        recurrence_rule=payload.recurrence_rule,
    )

    try:
        _update_account_balance(
            account, 0,
            "expense",
            payload.amount,
            payload.type
        )
    except BalanceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    cat_id = payload.category_id
    if cat_id is not None and cat_id != transaction.category_id:
        category = db.query(Category).filter(
            Category.id == payload.category_id,
            Category.user_id == current_user.id,
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or does not belong to user",
            )

    old_amount = transaction.amount
    old_type = transaction.type

    update_data = payload.model_dump(exclude_unset=True)
    new_amount = update_data.get("amount", old_amount)
    new_type = update_data.get("type", old_type)

    if "account_id" in update_data:
        account = db.query(Account).filter(
            Account.id == update_data["account_id"],
            Account.user_id == current_user.id,
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New account not found or does not belong to user",
            )

    if new_amount != old_amount or new_type != old_type:
        account = db.query(Account).filter(
            Account.id == transaction.account_id,
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated account not found",
            )
        try:
            _update_account_balance(
                account, old_amount,
                old_type, new_amount,
                new_type
            )
        except BalanceError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    for field, value in update_data.items():
        if field not in ("account_id",):
            setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    account = db.query(Account).filter(
        Account.id == transaction.account_id
    ).first()
    if account:
        transaction.apply_to_balance(account, sign=-1)

    db.delete(transaction)
    db.commit()
