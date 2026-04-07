from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from main import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    password_hash = Column(String, nullable=False)


class Income(Base):
    __tablename__ = "incomes"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String)
    category = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String)
    category = Column(String, nullable=False)
    kakebo_type = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Debt(Base):
    __tablename__ = "debts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    initial_amount = Column(Float, nullable=False)
    current_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    monthly_payment = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    next_payment_date = Column(Date, nullable=False)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    payments = relationship("DebtPayment", back_populates="debt")


class DebtPayment(Base):
    __tablename__ = "debt_payments"
    id = Column(Integer, primary_key=True, index=True)
    debt_id = Column(Integer, ForeignKey("debts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)

    debt = relationship("Debt", back_populates="payments")


class CreditCard(Base):
    __tablename__ = "credit_cards"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    limit = Column(Float, nullable=False)
    current_balance = Column(Float, default=0)
    interest_rate = Column(Float, nullable=False)
    due_date = Column(Integer, nullable=False)
    card_type = Column(String, default="visa")
    last_four = Column(String, default="0000")
    cardholder_name = Column(String, default="TITULAR")
    expiration_date = Column(String, default="12/28")
    created_at = Column(DateTime, default=datetime.now)

    charges = relationship("CreditCardCharge", back_populates="card")
    card_payments = relationship("CreditCardPayment", back_populates="card")


class CreditCardCharge(Base):
    __tablename__ = "credit_card_charges"
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    charge_date = Column(Date, nullable=False)

    card = relationship("CreditCard", back_populates="charges")


class CreditCardPayment(Base):
    __tablename__ = "credit_card_payments"
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    balance_before = Column(Float)
    balance_after = Column(Float)

    card = relationship("CreditCard", back_populates="card_payments")


class HouseholdService(Base):
    __tablename__ = "household_services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    provider = Column(String)
    amount = Column(Float, nullable=False)
    due_day = Column(Integer, nullable=False)
    reminder_days = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    last_paid_date = Column(Date)
    created_at = Column(DateTime, default=datetime.now)

    payments = relationship("ServicePayment", back_populates="service")


class ServicePayment(Base):
    __tablename__ = "service_payments"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("household_services.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)

    service = relationship("HouseholdService", back_populates="payments")
