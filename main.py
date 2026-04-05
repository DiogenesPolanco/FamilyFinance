from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

SECRET_KEY = os.getenv("SECRET_KEY", "family-finance-secret-key-change-in-production")
ALGORITHM = "HS256"

DATABASE_URL = "sqlite:///./family_finance.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def lifespan(app):
    from sqlalchemy import inspect
    from sqlalchemy.exc import OperationalError

    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except OperationalError:
        # Tables already exist, continue
        pass
    yield


app = FastAPI(title="FamilyFinance API", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


security = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    if not credentials:
        return {"id": 1, "username": "user"}

    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        return {"id": 1, "username": payload.get("sub", "user")}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


from models import (
    User,
    Income,
    Expense,
    Debt,
    DebtPayment,
    CreditCard,
    CreditCardCharge,
    HouseholdService,
    ServicePayment,
)


@app.get("/")
def read_root():
    return FileResponse("static/index.html")


@app.post("/api/setup")
def setup_user(password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(password_hash=get_password_hash(password))
    db.add(user)
    db.commit()
    return {"message": "User created successfully"}


@app.post("/api/auth/login")
def login(password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found. Setup first.")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_access_token({"sub": "user"})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/auth/status")
def auth_status(db: Session = Depends(get_db)):
    user = db.query(User).first()
    return {"is_setup": user is not None}


@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    today = date.today()
    first_of_month = today.replace(day=1)

    total_income = db.query(Income).filter(Income.date >= first_of_month).all()
    total_expenses = db.query(Expense).filter(Expense.date >= first_of_month).all()

    income_sum = sum(i.amount for i in total_income)
    expense_sum = sum(e.amount for e in total_expenses)

    debts = db.query(Debt).filter(Debt.is_paid == False).all()
    total_debt = sum(d.current_amount for d in debts)

    credit_cards = db.query(CreditCard).all()
    credit_usage = sum(c.current_balance for c in credit_cards)
    credit_limit = sum(c.limit for c in credit_cards)

    return {
        "balance": income_sum - expense_sum,
        "monthly_income": income_sum,
        "monthly_expenses": expense_sum,
        "total_debt": total_debt,
        "credit_usage": credit_usage,
        "credit_limit": credit_limit,
        "credit_usage_percent": (credit_usage / credit_limit * 100)
        if credit_limit > 0
        else 0,
    }


@app.get("/api/dashboard/upcoming")
def get_upcoming_payments(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    today = date.today()
    end_date = today + timedelta(days=days)
    upcoming = []

    debts = (
        db.query(Debt)
        .filter(Debt.is_paid == False, Debt.next_payment_date <= end_date)
        .all()
    )
    for d in debts:
        upcoming.append(
            {
                "type": "debt",
                "id": d.id,
                "name": d.name,
                "amount": d.monthly_payment,
                "due_date": d.next_payment_date,
                "days_until": (d.next_payment_date - today).days,
            }
        )

    services = (
        db.query(HouseholdService).filter(HouseholdService.is_active == True).all()
    )
    for s in services:
        if s.due_day:
            next_date = date(today.year, today.month, min(s.due_day, 28))
            if next_date < today:
                next_date = date(today.year, today.month + 1, min(s.due_day, 28))
            if next_date <= end_date:
                upcoming.append(
                    {
                        "type": "service",
                        "id": s.id,
                        "name": s.name,
                        "amount": s.amount,
                        "due_date": next_date,
                        "days_until": (next_date - today).days,
                    }
                )

    cards = db.query(CreditCard).all()
    for c in cards:
        due_date = date(today.year, today.month, min(c.due_date, 28))
        if due_date < today:
            due_date = date(today.year, today.month + 1, min(c.due_date, 28))
        if due_date <= end_date and c.current_balance > 0:
            upcoming.append(
                {
                    "type": "card",
                    "id": c.id,
                    "name": f"Pago tarjeta {c.name}",
                    "amount": min(c.current_balance, c.limit * 0.15),
                    "due_date": due_date,
                    "days_until": (due_date - today).days,
                }
            )

    return sorted(upcoming, key=lambda x: x["due_date"])


# Income CRUD
class IncomeCreate(BaseModel):
    amount: float
    description: Optional[str] = None
    category: str
    date: date


class IncomeResponse(IncomeCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


@app.get("/api/income", response_model=list[IncomeResponse])
def get_incomes(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return db.query(Income).order_by(Income.date.desc()).all()


@app.post("/api/income", response_model=IncomeResponse)
def create_income(
    income: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_income = Income(
        amount=income.amount,
        description=income.description,
        category=income.category,
        date=income.date.date() if isinstance(income.date, datetime) else income.date,
        created_at=datetime.now(),
    )
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    return db_income


@app.put("/api/income/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: int,
    income: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_income = db.query(Income).filter(Income.id == income_id).first()
    if not db_income:
        raise HTTPException(status_code=404, detail="Income not found")

    for key, value in income.model_dump().items():
        setattr(db_income, key, value)

    db.commit()
    db.refresh(db_income)
    return db_income


@app.delete("/api/income/{income_id}")
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_income = db.query(Income).filter(Income.id == income_id).first()
    if not db_income:
        raise HTTPException(status_code=404, detail="Income not found")

    db.delete(db_income)
    db.commit()
    return {"message": "Income deleted"}


# Expense CRUD
class ExpenseCreate(BaseModel):
    amount: float
    description: Optional[str] = None
    category: str
    kakebo_type: str
    date: date


class ExpenseResponse(ExpenseCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


@app.get("/api/expense", response_model=list[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return db.query(Expense).order_by(Expense.date.desc()).all()


@app.post("/api/expense", response_model=ExpenseResponse)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_expense = Expense(
        amount=expense.amount,
        description=expense.description,
        category=expense.category,
        kakebo_type=expense.kakebo_type,
        date=expense.date.date()
        if isinstance(expense.date, datetime)
        else expense.date,
        created_at=datetime.now(),
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@app.put("/api/expense/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    for key, value in expense.model_dump().items():
        setattr(db_expense, key, value)

    db.commit()
    db.refresh(db_expense)
    return db_expense


@app.delete("/api/expense/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(db_expense)
    db.commit()
    return {"message": "Expense deleted"}


@app.get("/api/expense/kakebo")
def get_kakebo_summary(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    today = date.today()
    first_of_month = today.replace(day=1)

    expenses = db.query(Expense).filter(Expense.date >= first_of_month).all()

    categories = {"needs": 0, "wants": 0, "culture": 0, "unexpected": 0}
    types = {"fixed": 0, "variable": 0, "occasional": 0}
    total = 0

    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount
        types[e.kakebo_type] = types.get(e.kakebo_type, 0) + e.amount
        total += e.amount

    return {
        "total": total,
        "by_category": categories,
        "by_type": types,
        "expense_count": len(expenses),
    }


# Debt CRUD
class DebtCreate(BaseModel):
    name: str
    initial_amount: float
    current_amount: float
    interest_rate: float
    monthly_payment: float
    start_date: date
    next_payment_date: date
    is_paid: bool = False


class DebtPaymentCreate(BaseModel):
    amount: float
    payment_date: date


class DebtResponse(DebtCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


@app.get("/api/debt", response_model=list[DebtResponse])
def get_debts(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return db.query(Debt).order_by(Debt.created_at.desc()).all()


@app.post("/api/debt", response_model=DebtResponse)
def create_debt(
    debt: DebtCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_debt = Debt(
        name=debt.name,
        initial_amount=debt.initial_amount,
        current_amount=debt.current_amount,
        interest_rate=debt.interest_rate,
        monthly_payment=debt.monthly_payment,
        start_date=debt.start_date,
        next_payment_date=debt.next_payment_date,
        is_paid=debt.is_paid,
        created_at=datetime.now(),
    )
    db.add(db_debt)
    db.commit()
    db.refresh(db_debt)
    return db_debt


@app.put("/api/debt/{debt_id}", response_model=DebtResponse)
def update_debt(
    debt_id: int,
    debt: DebtCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_debt = db.query(Debt).filter(Debt.id == debt_id).first()
    if not db_debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    for key, value in debt.model_dump().items():
        setattr(db_debt, key, value)

    db.commit()
    db.refresh(db_debt)
    return db_debt


@app.post("/api/debt/{debt_id}/pay")
def pay_debt(
    debt_id: int,
    payment: DebtPaymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_debt = db.query(Debt).filter(Debt.id == debt_id).first()
    if not db_debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    db_payment = DebtPayment(
        debt_id=debt_id,
        amount=payment.amount,
        payment_date=payment.payment_date,
    )
    db.add(db_payment)

    db_debt.current_amount -= payment.amount
    if db_debt.current_amount <= 0:
        db_debt.current_amount = 0
        db_debt.is_paid = True

    db_debt.next_payment_date = payment.payment_date + timedelta(days=30)

    db.commit()
    db.refresh(db_debt)
    return db_debt


@app.delete("/api/debt/{debt_id}")
def delete_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_debt = db.query(Debt).filter(Debt.id == debt_id).first()
    if not db_debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    db.query(DebtPayment).filter(DebtPayment.debt_id == debt_id).delete()
    db.delete(db_debt)
    db.commit()
    return {"message": "Debt deleted"}


# Credit Card CRUD
class CreditCardCreate(BaseModel):
    name: str
    limit: float
    current_balance: float = 0
    interest_rate: float
    due_date: int


class CreditCardChargeCreate(BaseModel):
    amount: float
    description: Optional[str] = None
    charge_date: Optional[date] = None


class CreditCardResponse(CreditCardCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


@app.get("/api/credit-card", response_model=list[CreditCardResponse])
def get_credit_cards(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return db.query(CreditCard).all()


@app.post("/api/credit-card", response_model=CreditCardResponse)
def create_credit_card(
    card: CreditCardCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_card = CreditCard(
        name=card.name,
        limit=card.limit,
        current_balance=card.current_balance,
        interest_rate=card.interest_rate,
        due_date=card.due_date,
        created_at=datetime.now(),
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card


@app.put("/api/credit-card/{card_id}", response_model=CreditCardResponse)
def update_credit_card(
    card_id: int,
    card: CreditCardCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_card = db.query(CreditCard).filter(CreditCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")

    for key, value in card.model_dump().items():
        setattr(db_card, key, value)

    db.commit()
    db.refresh(db_card)
    return db_card


@app.post("/api/credit-card/{card_id}/charge")
def add_card_charge(
    card_id: int,
    charge: CreditCardChargeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_card = db.query(CreditCard).filter(CreditCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")

    db_charge = CreditCardCharge(
        card_id=card_id,
        amount=charge.amount,
        description=charge.description,
        charge_date=charge.charge_date or date.today(),
    )
    db.add(db_charge)

    db_card.current_balance += charge.amount
    db.commit()
    db.refresh(db_card)
    return db_card


@app.delete("/api/credit-card/{card_id}")
def delete_credit_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_card = db.query(CreditCard).filter(CreditCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.query(CreditCardCharge).filter(CreditCardCharge.card_id == card_id).delete()
    db.delete(db_card)
    db.commit()
    return {"message": "Card deleted"}


# Household Service CRUD
class ServiceCreate(BaseModel):
    name: str
    provider: Optional[str] = None
    amount: float
    due_day: int
    reminder_days: int = 3
    is_active: bool = True


class ServiceResponse(ServiceCreate):
    id: int
    last_paid_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


@app.get("/api/service", response_model=list[ServiceResponse])
def get_services(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return db.query(HouseholdService).all()


@app.post("/api/service", response_model=ServiceResponse)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_service = HouseholdService(
        name=service.name,
        provider=service.provider,
        amount=service.amount,
        due_day=service.due_day,
        reminder_days=service.reminder_days,
        is_active=service.is_active,
        created_at=datetime.now(),
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


@app.put("/api/service/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_service = (
        db.query(HouseholdService).filter(HouseholdService.id == service_id).first()
    )
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")

    for key, value in service.model_dump().items():
        setattr(db_service, key, value)

    db.commit()
    db.refresh(db_service)
    return db_service


@app.post("/api/service/{service_id}/pay")
def pay_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_service = (
        db.query(HouseholdService).filter(HouseholdService.id == service_id).first()
    )
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")

    db_payment = ServicePayment(
        service_id=service_id,
        amount=db_service.amount,
        payment_date=date.today(),
    )
    db.add(db_payment)

    db_service.last_paid_date = date.today()
    db.commit()
    db.refresh(db_service)
    return db_service


@app.delete("/api/service/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_service = (
        db.query(HouseholdService).filter(HouseholdService.id == service_id).first()
    )
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")

    db.query(ServicePayment).filter(ServicePayment.service_id == service_id).delete()
    db.delete(db_service)
    db.commit()
    return {"message": "Service deleted"}


# Reports
@app.get("/api/reports/{report_type}")
def get_report(
    report_type: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    today = date.today()

    if report_type == "fortnightly":
        current_period_start = today.replace(day=1)
        current_period_end = date(today.year, today.month, 15)
        prev_period_start = (current_period_start - timedelta(days=15)).replace(day=16)
        prev_period_end = current_period_start - timedelta(days=1)

        current_incomes = (
            db.query(Income)
            .filter(
                Income.date >= current_period_start, Income.date <= current_period_end
            )
            .all()
        )
        current_expenses = (
            db.query(Expense)
            .filter(
                Expense.date >= current_period_start, Expense.date <= current_period_end
            )
            .all()
        )
        prev_incomes = (
            db.query(Income)
            .filter(Income.date >= prev_period_start, Income.date <= prev_period_end)
            .all()
        )
        prev_expenses = (
            db.query(Expense)
            .filter(Expense.date >= prev_period_start, Expense.date <= prev_period_end)
            .all()
        )

        return {
            "type": "fortnightly",
            "periods": [
                {
                    "period": "previous",
                    "label": f"16-{prev_period_start.day} al {prev_period_end.day} {prev_period_end.strftime('%b')}",
                    "start_date": str(prev_period_start),
                    "end_date": str(prev_period_end),
                    "total_income": sum(i.amount for i in prev_incomes),
                    "total_expenses": sum(e.amount for e in prev_expenses),
                    "balance": sum(i.amount for i in prev_incomes)
                    - sum(e.amount for e in prev_expenses),
                },
                {
                    "period": "current",
                    "label": f"1-15 {today.strftime('%b')}",
                    "start_date": str(current_period_start),
                    "end_date": str(current_period_end),
                    "total_income": sum(i.amount for i in current_incomes),
                    "total_expenses": sum(e.amount for e in current_expenses),
                    "balance": sum(i.amount for i in current_incomes)
                    - sum(e.amount for e in current_expenses),
                },
            ],
            "comparison": {
                "income_change": sum(i.amount for i in current_incomes)
                - sum(i.amount for i in prev_incomes),
                "expense_change": sum(e.amount for e in current_expenses)
                - sum(e.amount for e in prev_expenses),
            },
        }

    elif report_type == "monthly":
        first_of_month = today.replace(day=1)
        last_month_start = (first_of_month - timedelta(days=1)).replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)

        this_incomes = db.query(Income).filter(Income.date >= first_of_month).all()
        this_expenses = db.query(Expense).filter(Expense.date >= first_of_month).all()
        prev_incomes = (
            db.query(Income)
            .filter(Income.date >= last_month_start, Income.date <= last_month_end)
            .all()
        )
        prev_expenses = (
            db.query(Expense)
            .filter(Expense.date >= last_month_start, Expense.date <= last_month_end)
            .all()
        )

        by_category = {"needs": 0, "wants": 0, "culture": 0, "unexpected": 0}
        by_type = {"fixed": 0, "variable": 0, "occasional": 0}

        for e in this_expenses:
            by_category[e.category] = by_category.get(e.category, 0) + e.amount
            by_type[e.kakebo_type] = by_type.get(e.kakebo_type, 0) + e.amount

        this_income_total = sum(i.amount for i in this_incomes)
        this_expense_total = sum(e.amount for e in this_expenses)
        prev_income_total = sum(i.amount for i in prev_incomes)
        prev_expense_total = sum(e.amount for e in prev_expenses)

        return {
            "type": "monthly",
            "periods": [
                {
                    "period": "previous",
                    "label": last_month_start.strftime("%B %Y"),
                    "start_date": str(last_month_start),
                    "end_date": str(last_month_end),
                    "total_income": prev_income_total,
                    "total_expenses": prev_expense_total,
                    "balance": prev_income_total - prev_expense_total,
                },
                {
                    "period": "current",
                    "label": today.strftime("%B %Y"),
                    "start_date": str(first_of_month),
                    "end_date": str(today),
                    "total_income": this_income_total,
                    "total_expenses": this_expense_total,
                    "balance": this_income_total - this_expense_total,
                },
            ],
            "by_category": by_category,
            "by_type": by_type,
            "comparison": {
                "income_change": this_income_total - prev_income_total,
                "expense_change": this_expense_total - prev_expense_total,
            },
        }

    elif report_type == "quarterly":
        months = []
        for i in range(3):
            month_date = (
                date(today.year, today.month - 2 + i, 1)
                if today.month - 2 + i > 0
                else date(today.year - 1, 12 + today.month - 2 + i, 1)
            )
            month_end = (
                date(month_date.year, month_date.month + 1, 1) - timedelta(days=1)
                if month_date.month < 12
                else date(month_date.year + 1, 1, 1) - timedelta(days=1)
            )

            month_incomes = (
                db.query(Income)
                .filter(Income.date >= month_date, Income.date <= month_end)
                .all()
            )
            month_expenses = (
                db.query(Expense)
                .filter(Expense.date >= month_date, Expense.date <= month_end)
                .all()
            )

            inc_total = sum(i.amount for i in month_incomes)
            exp_total = sum(e.amount for e in month_expenses)

            months.append(
                {
                    "period": f"month_{i + 1}",
                    "label": month_date.strftime("%B %Y"),
                    "start_date": str(month_date),
                    "end_date": str(month_end),
                    "total_income": inc_total,
                    "total_expenses": exp_total,
                    "balance": inc_total - exp_total,
                }
            )

        avg_income = sum(m["total_income"] for m in months) / 3
        avg_expenses = sum(m["total_expenses"] for m in months) / 3
        current_month = months[-1]["total_expenses"] if months else 0

        return {
            "type": "quarterly",
            "periods": months,
            "averages": {
                "income": avg_income,
                "expenses": avg_expenses,
            },
            "comparison": {
                "vs_average_expense": current_month - avg_expenses,
                "trend": "increasing" if current_month > avg_expenses else "decreasing",
            },
        }

    elif report_type == "yearly":
        first_of_year = today.replace(month=1, day=1)

        monthly_data = []
        for m in range(1, 13):
            if m > today.month:
                break
            month_start = date(today.year, m, 1)
            if m == 12:
                month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(today.year, m + 1, 1) - timedelta(days=1)

            month_incomes = (
                db.query(Income)
                .filter(Income.date >= month_start, Income.date <= month_end)
                .all()
            )
            month_expenses = (
                db.query(Expense)
                .filter(Expense.date >= month_start, Expense.date <= month_end)
                .all()
            )

            inc_total = sum(i.amount for i in month_incomes)
            exp_total = sum(e.amount for e in month_expenses)

            monthly_data.append(
                {
                    "period": f"month_{m}",
                    "label": month_start.strftime("%B"),
                    "total_income": inc_total,
                    "total_expenses": exp_total,
                    "balance": inc_total - exp_total,
                }
            )

        total_income = sum(m["total_income"] for m in monthly_data)
        total_expenses = sum(m["total_expenses"] for m in monthly_data)

        return {
            "type": "yearly",
            "periods": monthly_data,
            "totals": {
                "income": total_income,
                "expenses": total_expenses,
                "balance": total_income - total_expenses,
            },
        }

    elif report_type == "kakebo":
        first_of_month = today.replace(day=1)

        expenses = db.query(Expense).filter(Expense.date >= first_of_month).all()

        by_kakebo = {"needs": 0, "wants": 0, "culture": 0, "unexpected": 0}
        by_type = {"fixed": 0, "variable": 0, "occasional": 0}
        total = 0

        for e in expenses:
            by_kakebo[e.category] = by_kakebo.get(e.category, 0) + e.amount
            by_type[e.kakebo_type] = by_type.get(e.kakebo_type, 0) + e.amount
            total += e.amount

        total_income = sum(
            i.amount
            for i in db.query(Income).filter(Income.date >= first_of_month).all()
        )

        return {
            "type": "kakebo",
            "periods": [
                {
                    "period": "current",
                    "label": today.strftime("%B %Y"),
                    "total_expenses": total,
                    "total_income": total_income,
                }
            ],
            "by_category": by_kakebo,
            "by_type": by_type,
            "percentages": {
                k: round((v / total * 100) if total > 0 else 0, 1)
                for k, v in by_kakebo.items()
            },
            "budget_recommendations": {
                "needs": total_income * 0.50,
                "wants": total_income * 0.30,
                "culture": total_income * 0.10,
                "unexpected": total_income * 0.10,
            },
        }

    elif report_type == "debts":
        debts = db.query(Debt).all()

        debt_history = []
        for d in debts:
            debt_history.append(
                {
                    "id": d.id,
                    "name": d.name,
                    "initial_amount": d.initial_amount,
                    "current_amount": d.current_amount,
                    "progress": round(
                        (1 - d.current_amount / d.initial_amount) * 100, 1
                    )
                    if d.initial_amount > 0
                    else 0,
                    "is_paid": d.is_paid,
                    "interest_rate": d.interest_rate,
                }
            )

        return {
            "type": "debts",
            "periods": [],
            "debts": debt_history,
            "totals": {
                "initial": sum(d["initial_amount"] for d in debt_history),
                "current": sum(d["current_amount"] for d in debt_history),
                "paid": sum(
                    d["initial_amount"] - d["current_amount"] for d in debt_history
                ),
            },
        }

    raise HTTPException(status_code=400, detail="Invalid report type")


# Budget
@app.get("/api/budget")
def get_budget(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    today = date.today()
    first_of_month = today.replace(day=1)

    total_income = sum(
        i.amount for i in db.query(Income).filter(Income.date >= first_of_month).all()
    )

    expenses = db.query(Expense).filter(Expense.date >= first_of_month).all()
    by_category = {"needs": 0, "wants": 0, "culture": 0, "unexpected": 0}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount

    limits = {
        "needs": total_income * 0.50,
        "wants": total_income * 0.30,
        "culture": total_income * 0.10,
        "unexpected": total_income * 0.10,
    }

    budgets = {}
    alerts = []

    for cat in ["needs", "wants", "culture", "unexpected"]:
        spent = by_category.get(cat, 0)
        limit = limits[cat]
        percentage = (spent / limit * 100) if limit > 0 else 0
        budgets[cat] = {"limit": limit, "spent": spent, "percentage": percentage}

        if percentage > 100:
            alerts.append(
                {
                    "category": cat,
                    "message": f"Has exceeded your {cat} budget by {percentage - 100:.1f}%",
                    "severity": "critical",
                }
            )
        elif percentage > 80:
            alerts.append(
                {
                    "category": cat,
                    "message": f"Approaching {cat} budget limit ({percentage:.1f}%)",
                    "severity": "warning",
                }
            )

    return {
        "total_income": total_income,
        "budgets": budgets,
        "alerts": alerts,
    }


# AI Engine
from ai_engine import AIFinanceEngine


@app.get("/api/ai/recommendations")
def get_recommendations(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    ai = AIFinanceEngine(db)
    return ai.get_recommendations()


@app.get("/api/ai/insights")
def get_insights(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    ai = AIFinanceEngine(db)
    return ai.get_insights()


@app.get("/api/ai/anomalies")
def get_anomalies(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    ai = AIFinanceEngine(db)
    return ai.detect_anomalies()


@app.get("/api/ai/forecast")
def get_forecast(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ai = AIFinanceEngine(db)
    return ai.get_forecast(days)


@app.get("/api/ai/debt-strategy")
def get_debt_strategy(
    strategy: str = "avalanche",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ai = AIFinanceEngine(db)
    return ai.get_debt_payoff_strategy(strategy)


@app.post("/api/ai/simulate")
def simulate_scenario(
    scenario: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ai = AIFinanceEngine(db)
    return ai.simulate_scenario(scenario)


@app.get("/api/debt/{debt_id}/interest")
def get_debt_interest(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ai = AIFinanceEngine(db)
    return ai.calculate_real_interest(debt_id)


@app.get("/api/debt/{debt_id}/projection")
def get_debt_projection(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ai = AIFinanceEngine(db)
    return ai.get_debt_projection(debt_id)


@app.get("/api/debt/comparison")
def get_debt_comparison(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ai = AIFinanceEngine(db)
    return ai.get_debt_comparison()


@app.get("/api/debt-compare/full")
def get_full_debt_comparison(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    debts = db.query(Debt).filter(Debt.is_paid == False).all()
    cards = db.query(CreditCard).all()

    debt_items = []
    card_items = []
    all_items = []

    for d in debts:
        monthly_rate = d.interest_rate / 100 / 12
        months = d.current_amount / d.monthly_payment if d.monthly_payment > 0 else 0
        if monthly_rate > 0 and months > 0:
            total_paid = d.monthly_payment * months
            total_interest = total_paid - d.current_amount
        else:
            total_interest = 0

        item = {
            "id": d.id,
            "name": d.name,
            "type": "debt",
            "current_amount": d.current_amount,
            "interest_rate": d.interest_rate,
            "monthly_payment": d.monthly_payment,
            "total_interest": max(0, total_interest),
            "total_cost": d.current_amount + max(0, total_interest),
            "months_to_payoff": round(months) if months > 0 else 0,
        }
        debt_items.append(item)
        all_items.append(item)

    for c in cards:
        if c.current_balance <= 0:
            continue
        monthly_rate = c.interest_rate / 100 / 12
        min_payment = c.limit * 0.05
        months = 12
        if monthly_rate > 0:
            if min_payment > c.current_balance * monthly_rate:
                months = c.current_balance / (
                    min_payment - c.current_balance * monthly_rate
                )
            else:
                months = 60
        total_interest = c.current_balance * monthly_rate * max(1, int(months))

        item = {
            "id": c.id,
            "name": c.name,
            "type": "card",
            "current_amount": c.current_balance,
            "interest_rate": c.interest_rate,
            "monthly_payment": round(min_payment, 2),
            "total_interest": max(0, total_interest),
            "total_cost": c.current_balance + max(0, total_interest),
            "months_to_payoff": max(1, min(60, int(months))),
            "limit": c.limit,
            "usage_percent": round(c.current_balance / c.limit * 100)
            if c.limit > 0
            else 0,
        }
        card_items.append(item)
        all_items.append(item)

    debt_items.sort(key=lambda x: x["interest_rate"], reverse=True)
    card_items.sort(key=lambda x: x["interest_rate"], reverse=True)
    all_items.sort(key=lambda x: x["interest_rate"], reverse=True)

    total_debt_principal = sum(d["current_amount"] for d in debt_items)
    total_debt_interest = sum(d["total_interest"] for d in debt_items)
    total_card_principal = sum(c["current_amount"] for c in card_items)
    total_card_interest = sum(c["total_interest"] for c in card_items)

    highest_rate = all_items[0] if all_items else None
    lowest_rate = all_items[-1] if all_items else None

    return {
        "debts": debt_items,
        "cards": card_items,
        "all_items": all_items,
        "summary": {
            "total_debts": len(debt_items),
            "total_cards": len(card_items),
            "total_principal_debts": total_debt_principal,
            "total_interest_debts": total_debt_interest,
            "total_principal_cards": total_card_principal,
            "total_interest_cards": total_card_interest,
            "total_principal": total_debt_principal + total_card_principal,
            "total_interest": total_debt_interest + total_card_interest,
            "highest_rate_item": highest_rate,
            "lowest_rate_item": lowest_rate,
        },
    }


@app.get("/api/credit-card/{card_id}/projection")
def get_card_projection(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ai = AIFinanceEngine(db)
    return ai.get_card_projection(card_id)


# Export
@app.get("/api/export/csv")
def export_csv(
    resource: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from fastapi.responses import StreamingResponse
    import csv
    import io

    valid_resources = [
        "transactions",
        "income",
        "expense",
        "debt",
        "credit_card",
        "service",
    ]

    if resource not in valid_resources:
        raise HTTPException(status_code=400, detail="Invalid resource")

    output = io.StringIO()
    writer = csv.writer(output)

    if resource == "transactions":
        writer.writerow(["Fecha", "Tipo", "Monto", "Descripcion", "Categoria"])
        incomes = db.query(Income).all()
        for i in incomes:
            writer.writerow(
                [i.date, "Ingreso", i.amount, i.description or "", i.category]
            )
        expenses = db.query(Expense).all()
        for e in expenses:
            writer.writerow(
                [e.date, "Gasto", e.amount, e.description or "", e.category]
            )

    elif resource == "income":
        writer.writerow(["Fecha", "Monto", "Descripcion", "Categoria"])
        for i in db.query(Income).all():
            writer.writerow([i.date, i.amount, i.description or "", i.category])

    elif resource == "expense":
        writer.writerow(["Fecha", "Monto", "Descripcion", "Categoria", "Tipo Kakebo"])
        for e in db.query(Expense).all():
            writer.writerow(
                [e.date, e.amount, e.description or "", e.category, e.kakebo_type]
            )

    elif resource == "debt":
        writer.writerow(
            [
                "Nombre",
                "Monto Inicial",
                "Monto Actual",
                "Tasa",
                "Pago Mensual",
                "Pagado",
            ]
        )
        for d in db.query(Debt).all():
            writer.writerow(
                [
                    d.name,
                    d.initial_amount,
                    d.current_amount,
                    d.interest_rate,
                    d.monthly_payment,
                    "Si" if d.is_paid else "No",
                ]
            )

    elif resource == "credit_card":
        writer.writerow(["Nombre", "Limite", "Saldo", "Tasa", "Dia Corte"])
        for c in db.query(CreditCard).all():
            writer.writerow(
                [c.name, c.limit, c.current_balance, c.interest_rate, c.due_date]
            )

    elif resource == "service":
        writer.writerow(["Nombre", "Proveedor", "Monto", "Dia Pago", "Activo"])
        for s in db.query(HouseholdService).all():
            writer.writerow(
                [
                    s.name,
                    s.provider or "",
                    s.amount,
                    s.due_day,
                    "Si" if s.is_active else "No",
                ]
            )

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={resource}.csv"},
    )


# Seed Dummy Data
@app.post("/api/seed/dummy")
def seed_dummy_data(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    incomes = [
        {
            "amount": 15000,
            "description": "Salario mensual",
            "category": "salary",
            "date": date(2026, 3, 1),
        },
        {
            "amount": 15000,
            "description": "Salario mensual",
            "category": "salary",
            "date": date(2026, 4, 1),
        },
        {
            "amount": 3000,
            "description": "Freelance diseno web",
            "category": "freelance",
            "date": date(2026, 3, 15),
        },
        {
            "amount": 2000,
            "description": "Venta articulos usados",
            "category": "other",
            "date": date(2026, 4, 3),
        },
    ]
    for inc in incomes:
        db.add(Income(**inc, created_at=datetime.now()))

    expenses = [
        {
            "amount": 5500,
            "description": "Renta departamento",
            "category": "needs",
            "kakebo_type": "fixed",
            "date": date(2026, 3, 1),
        },
        {
            "amount": 5500,
            "description": "Renta departamento",
            "category": "needs",
            "kakebo_type": "fixed",
            "date": date(2026, 4, 1),
        },
        {
            "amount": 2800,
            "description": "Supermercado quincena 1",
            "category": "needs",
            "kakebo_type": "variable",
            "date": date(2026, 3, 5),
        },
        {
            "amount": 2200,
            "description": "Supermercado quincena 2",
            "category": "needs",
            "kakebo_type": "variable",
            "date": date(2026, 3, 20),
        },
        {
            "amount": 1500,
            "description": "Gasolina",
            "category": "needs",
            "kakebo_type": "variable",
            "date": date(2026, 3, 10),
        },
        {
            "amount": 800,
            "description": "Netflix + Spotify",
            "category": "wants",
            "kakebo_type": "fixed",
            "date": date(2026, 3, 15),
        },
        {
            "amount": 1200,
            "description": "Cena restaurante",
            "category": "wants",
            "kakebo_type": "variable",
            "date": date(2026, 3, 22),
        },
        {
            "amount": 600,
            "description": "Curso online Python",
            "category": "culture",
            "kakebo_type": "occasional",
            "date": date(2026, 3, 8),
        },
        {
            "amount": 350,
            "description": "Libros",
            "category": "culture",
            "kakebo_type": "occasional",
            "date": date(2026, 4, 2),
        },
        {
            "amount": 450,
            "description": "Medicinas",
            "category": "unexpected",
            "kakebo_type": "occasional",
            "date": date(2026, 4, 1),
        },
        {
            "amount": 1800,
            "description": "Reparacion auto",
            "category": "unexpected",
            "kakebo_type": "occasional",
            "date": date(2026, 3, 25),
        },
        {
            "amount": 15000,
            "description": "Supermercado quincena 1",
            "category": "needs",
            "kakebo_type": "variable",
            "date": date(2026, 3, 12),
        },
        {
            "amount": 2600,
            "description": "Supermercado quincena 1",
            "category": "needs",
            "kakebo_type": "variable",
            "date": date(2026, 2, 5),
        },
    ]
    for exp in expenses:
        db.add(Expense(**exp, created_at=datetime.now()))

    debts = [
        {
            "name": "Prestamo Auto",
            "initial_amount": 150000,
            "current_amount": 120000,
            "interest_rate": 12,
            "monthly_payment": 5000,
            "start_date": date(2025, 1, 1),
            "next_payment_date": date(2026, 4, 15),
            "created_at": datetime.now(),
        },
        {
            "name": "Tarjeta Tienda",
            "initial_amount": 25000,
            "current_amount": 25000,
            "interest_rate": 48,
            "monthly_payment": 1500,
            "start_date": date(2025, 6, 1),
            "next_payment_date": date(2026, 4, 10),
            "created_at": datetime.now(),
        },
        {
            "name": "Prestamo Personal",
            "initial_amount": 50000,
            "current_amount": 50000,
            "interest_rate": 24,
            "monthly_payment": 3000,
            "start_date": date(2026, 1, 1),
            "next_payment_date": date(2026, 4, 20),
            "created_at": datetime.now(),
        },
    ]
    for debt in debts:
        db.add(Debt(**debt))

    cards = [
        {
            "name": "Visa Oro",
            "limit": 50000,
            "current_balance": 32000,
            "interest_rate": 3.5,
            "due_date": 15,
            "created_at": datetime.now(),
        },
        {
            "name": "Mastercard Black",
            "limit": 35000,
            "current_balance": 20700,
            "interest_rate": 3.2,
            "due_date": 22,
            "created_at": datetime.now(),
        },
    ]
    for card in cards:
        db.add(CreditCard(**card))

    services = [
        {
            "name": "Internet Fibra",
            "provider": "Telecom",
            "amount": 800,
            "due_day": 5,
            "reminder_days": 3,
            "is_active": True,
            "last_paid_date": date(2026, 3, 5),
            "created_at": datetime.now(),
        },
        {
            "name": "Netflix",
            "provider": "Netflix Inc",
            "amount": 350,
            "due_day": 12,
            "reminder_days": 3,
            "is_active": True,
            "last_paid_date": date(2026, 3, 12),
            "created_at": datetime.now(),
        },
        {
            "name": "Spotify",
            "provider": "Spotify AB",
            "amount": 180,
            "due_day": 15,
            "reminder_days": 3,
            "is_active": True,
            "last_paid_date": date(2026, 3, 15),
            "created_at": datetime.now(),
        },
        {
            "name": "Gym Premium",
            "provider": "FitClub",
            "amount": 1200,
            "due_day": 1,
            "reminder_days": 5,
            "is_active": True,
            "last_paid_date": date(2025, 12, 8),
            "created_at": datetime.now(),
        },
        {
            "name": "Luz",
            "provider": "Utility Co",
            "amount": 1500,
            "due_day": 20,
            "reminder_days": 3,
            "is_active": True,
            "last_paid_date": date(2026, 3, 20),
            "created_at": datetime.now(),
        },
        {
            "name": "Agua",
            "provider": "Water Dept",
            "amount": 400,
            "due_day": 25,
            "reminder_days": 3,
            "is_active": True,
            "last_paid_date": date(2026, 3, 25),
            "created_at": datetime.now(),
        },
    ]
    for svc in services:
        db.add(HouseholdService(**svc))

    db.commit()

    return {
        "message": "Datos dummy cargados",
        "counts": {
            "incomes": len(incomes),
            "expenses": len(expenses),
            "debts": len(debts),
            "cards": len(cards),
            "services": len(services),
        },
    }
