from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from sqlalchemy.orm import Session
from main import Income, Expense, Debt, CreditCard, HouseholdService


class AIFinanceEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(self):
        recommendations = []

        today = date.today()
        first_of_month = today.replace(day=1)

        incomes = self.db.query(Income).filter(Income.date >= first_of_month).all()
        expenses = self.db.query(Expense).filter(Expense.date >= first_of_month).all()

        total_income = sum(i.amount for i in incomes)
        total_expenses = sum(e.amount for e in expenses)

        if total_income > 0:
            expense_ratio = total_expenses / total_income
            if expense_ratio > 0.9:
                recommendations.append(
                    "Gastas el 90% de tus ingresos. Considera reducir gastos en deseos."
                )
            elif expense_ratio > 0.7:
                recommendations.append(
                    f"Gastas el {expense_ratio * 100:.0f}% de tus ingresos. Tienes margen para ahorrar."
                )

        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()
        if debts:
            total_debt = sum(d.current_amount for d in debts)
            recommendations.append(
                f"Tienes ${total_debt:,.2f} en deudas activas. Prioriza las con mayor tasa de interes."
            )

        if total_income > 0:
            savings = total_income * 0.2
            recommendations.append(
                f"Puedes ahorrar hasta ${savings:,.2f} aplicando la regla 50/30/20."
            )

        categories = {"needs": 0, "wants": 0, "culture": 0, "unexpected": 0}
        for e in expenses:
            if e.category in categories:
                categories[e.category] += e.amount

        if total_expenses > 0:
            needs_ratio = categories["needs"] / total_expenses
            if needs_ratio > 0.8:
                recommendations.append(
                    f"El {needs_ratio * 100:.0f}% de tus gastos son necesidades. Busca formas de optimizar costos fijos."
                )

        return recommendations[:5]

    def get_insights(self):
        from sqlalchemy import extract

        today = date.today()
        current_month = today.month
        current_year = today.year
        first_of_month = today.replace(day=1)

        month_incomes = (
            self.db.query(Income)
            .filter(
                extract("month", Income.date) == current_month,
                extract("year", Income.date) == current_year,
            )
            .all()
        )
        month_expenses = (
            self.db.query(Expense)
            .filter(
                extract("month", Expense.date) == current_month,
                extract("year", Expense.date) == current_year,
            )
            .all()
        )

        last_month_start = (first_of_month - timedelta(days=1)).replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)

        prev_incomes = (
            self.db.query(Income)
            .filter(
                extract("month", Income.date) == last_month_start.month,
                extract("year", Income.date) == last_month_start.year,
            )
            .all()
        )
        prev_expenses = (
            self.db.query(Expense)
            .filter(
                extract("month", Expense.date) == last_month_start.month,
                extract("year", Expense.date) == last_month_start.year,
            )
            .all()
        )

        last_3_months_start = today - timedelta(days=90)
        last_3_incomes = (
            self.db.query(Income).filter(Income.date >= last_3_months_start).all()
        )
        last_3_expenses = (
            self.db.query(Expense).filter(Expense.date >= last_3_months_start).all()
        )

        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()
        cards = self.db.query(CreditCard).filter(CreditCard.current_balance > 0).all()

        month_income_total = sum(i.amount for i in month_incomes)
        month_expense_total = sum(e.amount for e in month_expenses)
        prev_income_total = sum(i.amount for i in prev_incomes) if prev_incomes else 0
        prev_expense_total = (
            sum(e.amount for i in prev_expenses) if prev_expenses else 0
        )

        monthly_balance = month_income_total - month_expense_total

        insights = {
            "current_status": {
                "month": today.strftime("%B %Y"),
                "income": round(month_income_total, 2),
                "expenses": round(month_expense_total, 2),
                "balance": round(monthly_balance, 2),
                "is_positive": monthly_balance >= 0,
            },
            "past_review": {
                "month": last_month_start.strftime("%B %Y"),
                "income": round(prev_income_total, 2),
                "expenses": round(prev_expense_total, 2),
                "balance": round(prev_income_total - prev_expense_total, 2),
                "comparison": {},
            },
            "future_suggestions": [],
            "past_feedback": [],
        }

        if prev_income_total > 0:
            income_change = (
                (month_income_total - prev_income_total) / prev_income_total
            ) * 100
            expense_change = (
                ((month_expense_total - prev_expense_total) / prev_expense_total) * 100
                if prev_expense_total > 0
                else 0
            )

            insights["past_review"]["comparison"] = {
                "income_change_pct": round(income_change, 1),
                "expense_change_pct": round(expense_change, 1),
            }

            if income_change > 0:
                insights["past_feedback"].append(
                    {
                        "type": "positive",
                        "icon": "trending-up",
                        "message": f"Tus ingresos aumentaron {income_change:+.1f}% respecto al mes pasado",
                    }
                )
            elif income_change < 0:
                insights["past_feedback"].append(
                    {
                        "type": "warning",
                        "icon": "trending-down",
                        "message": f"Tus ingresos bajaron {income_change:.1f}% respecto al mes pasado",
                    }
                )

            if expense_change > 20:
                insights["past_feedback"].append(
                    {
                        "type": "negative",
                        "icon": "alert-triangle",
                        "message": f"Tus gastos aumentaron {expense_change:+.1f}% - Revisa gastos innecesarios",
                    }
                )
            elif expense_change < -10:
                insights["past_feedback"].append(
                    {
                        "type": "positive",
                        "icon": "check-circle",
                        "message": f"Excelente! Redujiste tus gastos en {abs(expense_change):.1f}%",
                    }
                )

        if month_income_total > 0:
            savings_rate = (monthly_balance / month_income_total) * 100
            insights["past_review"]["savings_rate"] = round(savings_rate, 1)

            if savings_rate < 0:
                insights["past_feedback"].append(
                    {
                        "type": "negative",
                        "icon": "alert-circle",
                        "message": f"Gastas mas de lo que ganas ({abs(savings_rate):.1f}% deficit)",
                    }
                )
            elif savings_rate < 10:
                insights["future_suggestions"].append(
                    {
                        "type": "suggestion",
                        "icon": "piggy-bank",
                        "message": f"Tu tasa de ahorro es baja ({savings_rate:.1f}%). Intenta ahorrar al menos 20%",
                    }
                )
            else:
                insights["past_feedback"].append(
                    {
                        "type": "positive",
                        "icon": "check-circle",
                        "message": f"Buen ahorro este mes: {savings_rate:.1f}% de tus ingresos",
                    }
                )

        avg_monthly_expense = (
            sum(e.amount for e in last_3_expenses) / 3 if last_3_expenses else 0
        )
        if month_expense_total > avg_monthly_expense * 1.1:
            insights["past_feedback"].append(
                {
                    "type": "warning",
                    "icon": "alert-triangle",
                    "message": f"Gastas {((month_expense_total / avg_monthly_expense) - 1) * 100:.0f}% mas que tu promedio de 3 meses",
                }
            )

        if month_income_total > 0:
            needs_limit = month_income_total * 0.50
            wants_limit = month_income_total * 0.30

            needs_spent = sum(e.amount for e in month_expenses if e.category == "needs")
            wants_spent = sum(e.amount for e in month_expenses if e.category == "wants")

            if needs_spent > needs_limit:
                insights["future_suggestions"].append(
                    {
                        "type": "warning",
                        "icon": "home",
                        "message": f"Gastas ${needs_spent - needs_limit:,.0f} de mas en necesidades. Revisa alquiler, servicios, etc.",
                    }
                )

            if wants_spent > wants_limit:
                insights["future_suggestions"].append(
                    {
                        "type": "warning",
                        "icon": "shopping-bag",
                        "message": f"Gastas ${wants_spent - wants_limit:,.0f} de mas en deseos. Considera reducir suscripciones.",
                    }
                )

        total_debt = sum(d.current_amount for d in debts)
        if total_debt > 0:
            insights["future_suggestions"].append(
                {
                    "type": "debt",
                    "icon": "landmark",
                    "message": f"Tienes ${total_debt:,.0f} en deudas. Prioriza pagar las de mayor interes.",
                }
            )

        total_card_debt = sum(c.current_balance for c in cards)
        if total_card_debt > month_income_total * 0.5:
            insights["future_suggestions"].append(
                {
                    "type": "warning",
                    "icon": "credit-card",
                    "message": f"Tu deuda de tarjetas ({total_card_debt:,.0f}) es mas del 50% de tus ingresos. Paga rapido!",
                }
            )

        days_until_month_end = 30 - today.day
        if days_until_month_end > 0 and month_expense_total > 0:
            daily_avg = month_expense_total / today.day
            projected_total = daily_avg * 30
            remaining_budget = month_income_total - month_expense_total

            if projected_total > month_income_total:
                insights["future_suggestions"].append(
                    {
                        "type": "alert",
                        "icon": "alert-octagon",
                        "message": f"Proyeccion: Gastaras ${projected_total - month_income_total:,.0f} de mas este mes. Te quedan ${remaining_budget:,.0f} para {days_until_month_end} dias.",
                    }
                )
            else:
                insights["future_suggestions"].append(
                    {
                        "type": "positive",
                        "icon": "check-circle",
                        "message": f"Tienes ${remaining_budget:,.0f} disponibles para los proximos {days_until_month_end} dias.",
                    }
                )

        if month_income_total > 0 and month_expense_total > 0:
            savings_needed = month_income_total * 0.2
            if monthly_balance >= savings_needed:
                insights["future_suggestions"].append(
                    {
                        "type": "success",
                        "icon": "target",
                        "message": f"Cumpliste tu meta de ahorro del 20% (${savings_needed:,.0f})",
                    }
                )

        if not insights["past_feedback"]:
            insights["past_feedback"].append(
                {
                    "type": "info",
                    "icon": "info",
                    "message": "Continua asi! Manten tus habitos financieros actuales.",
                }
            )

        if not insights["future_suggestions"]:
            insights["future_suggestions"].append(
                {
                    "type": "info",
                    "icon": "thumbs-up",
                    "message": "Vas bien! Sigue monitorizando tus gastos.",
                }
            )

        return insights

    def detect_anomalies(self):
        anomalies = []

        expenses = self.db.query(Expense).order_by(Expense.date.desc()).limit(50).all()

        by_category = {}
        for e in expenses:
            key = f"{e.category}_{e.description}"
            if key not in by_category:
                by_category[key] = []
            by_category[key].append(e)

        for key, items in by_category.items():
            if len(items) >= 2:
                amounts = [i.amount for i in items]
                if len(set(amounts)) == 1 and amounts[0] > 100:
                    anomalies.append(
                        {
                            "anomaly_type": "duplicate",
                            "severity": "high",
                            "title": "Posible Duplicado",
                            "description": f"Gasto duplicado: ${amounts[0]:,.2f} el {items[0].date} - '{items[0].description}'.",
                            "details": {
                                "date": str(items[0].date),
                                "amount": amounts[0],
                                "description": items[0].description,
                            },
                        }
                    )

        by_category_avg = {}
        for e in expenses:
            cat = e.category
            if cat not in by_category_avg:
                by_category_avg[cat] = []
            by_category_avg[cat].append(e.amount)

        for cat, amounts in by_category_avg.items():
            if len(amounts) >= 3:
                avg = sum(amounts) / len(amounts)
                for amt in amounts:
                    if amt > avg * 2:
                        anomalies.append(
                            {
                                "anomaly_type": "spike",
                                "severity": "medium",
                                "title": "Gasto Inusual Detectado",
                                "description": f"{cat}: ${amt:,.2f} es el doble del promedio (${avg:,.2f}).",
                                "details": {
                                    "amount": amt,
                                    "average": avg,
                                    "category": cat,
                                },
                            }
                        )
                        break

        services = (
            self.db.query(HouseholdService)
            .filter(HouseholdService.is_active == True)
            .all()
        )
        today = date.today()
        for s in services:
            if s.last_paid_date:
                days_since = (today - s.last_paid_date).days
                if days_since > 60:
                    anomalies.append(
                        {
                            "anomaly_type": "inactive_service",
                            "severity": "low",
                            "title": "Servicio Posiblemente Inactivo",
                            "description": f"{s.name} no ha sido pagado en {days_since} dias. Verifica si sigue activo.",
                            "details": {
                                "service": s.name,
                                "days_since_payment": days_since,
                                "last_paid": str(s.last_paid_date),
                            },
                        }
                    )

        return anomalies[:10]

    def get_forecast(self, days: int = 30):
        today = date.today()
        forecast = []

        incomes = (
            self.db.query(Income)
            .filter(Income.date >= today - timedelta(days=90))
            .all()
        )
        expenses = (
            self.db.query(Expense)
            .filter(Expense.date >= today - timedelta(days=90))
            .all()
        )

        if not incomes or not expenses:
            for i in range(days):
                forecast.append({"date": str(today + timedelta(days=i)), "balance": 0})
            return forecast

        avg_daily_income = sum(i.amount for i in incomes) / 90
        avg_daily_expense = sum(e.amount for e in expenses) / 90

        balance = sum(i.amount for i in incomes) - sum(e.amount for e in expenses)

        for i in range(days):
            balance += avg_daily_income - avg_daily_expense
            forecast.append(
                {"date": str(today + timedelta(days=i)), "balance": max(0, balance)}
            )

        return forecast

    def get_debt_payoff_strategy(self, strategy: str = "avalanche"):
        debts_data = self.db.query(Debt).filter(Debt.is_paid == False).all()

        if not debts_data:
            return {
                "strategy": strategy,
                "strategy_name": "Avalancha"
                if strategy == "avalanche"
                else "Bola de Nieve",
                "total_months": 0,
                "total_interest": 0,
                "total_cost": 0,
                "steps": [],
                "recommendation": "No tienes deudas activas.继续保持!",
            }

        debts = []
        for d in debts_data:
            debts.append(
                {
                    "id": d.id,
                    "name": d.name,
                    "current_amount": d.current_amount,
                    "monthly_payment": d.monthly_payment,
                    "interest_rate": d.interest_rate,
                }
            )

        if strategy == "snowball":
            debts = sorted(debts, key=lambda d: d["current_amount"])
        else:
            debts = sorted(debts, key=lambda d: d["interest_rate"], reverse=True)

        steps = []
        months = 0
        total_interest = 0
        extra_payment = 1000
        month_count = 0

        while month_count < 360:
            month_count += 1
            balance = sum(d["current_amount"] for d in debts if d["current_amount"] > 0)

            if balance <= 0:
                break

            month_interest = 0
            for d in debts:
                if d["current_amount"] > 0:
                    month_interest += d["current_amount"] * (
                        d["interest_rate"] / 100 / 12
                    )

            total_interest += month_interest

            total_monthly = sum(
                d["monthly_payment"] for d in debts if d["current_amount"] > 0
            )
            payment = total_monthly + extra_payment

            if strategy == "avalanche":
                priority_idx = 0
                for i, d in enumerate(debts):
                    if d["current_amount"] > 0:
                        priority_idx = i
                        break

                priority_payment = payment
                for i, d in enumerate(debts):
                    if d["current_amount"] > 0:
                        if i == priority_idx:
                            pay = min(
                                priority_payment,
                                d["current_amount"]
                                + month_interest
                                / len([x for x in debts if x["current_amount"] > 0]),
                            )
                            d["current_amount"] -= pay
                            priority_payment -= pay
                        else:
                            min_pay = d["monthly_payment"] * 0.5
                            d["current_amount"] -= min_pay
                            payment -= min_pay
            else:
                for d in debts:
                    if d["current_amount"] > 0:
                        d["current_amount"] -= d["monthly_payment"]

            for d in debts:
                if d["current_amount"] <= 0:
                    d["current_amount"] = 0
                    steps.append(
                        {
                            "month": month_count,
                            "action": "paid_off",
                            "name": d["name"],
                            "message": f"{d['name']} PAGADA en mes {month_count}",
                        }
                    )

            if month_count % 6 == 0:
                current_balance = sum(
                    d["current_amount"] for d in debts if d["current_amount"] > 0
                )
                steps.append(
                    {
                        "month": month_count,
                        "action": "progress",
                        "balance": current_balance,
                        "message": f"Progreso: Balance ${current_balance:,.2f} | Interes acumulado ${total_interest:,.2f}",
                    }
                )

        final_balance = sum(d["current_amount"] for d in debts)
        total_cost = sum(d["current_amount"] for d in debts) + total_interest

        recommendation = ""
        if strategy == "avalanche":
            recommendation = "Esta estrategia te ahorra mas dinero enfocandote en la deuda con mayor tasa de interes primero."
        else:
            recommendation = "Esta estrategia te da victorias rapidas Pagando primero las deudas mas pequenas."

        return {
            "strategy": strategy,
            "strategy_name": "Avalancha"
            if strategy == "avalanche"
            else "Bola de Nieve",
            "total_months": month_count,
            "total_interest": round(total_interest, 2),
            "total_cost": round(total_cost, 2),
            "remaining_balance": round(final_balance, 2),
            "steps": steps[:30],
            "payoff_order": [
                {
                    "name": d["name"],
                    "rate": d["interest_rate"],
                    "amount": d["current_amount"],
                }
                for d in debts
                if d["current_amount"] > 0
            ],
            "recommendation": recommendation,
        }

    def simulate_scenario(self, scenario: dict):
        scenario_type = scenario.get("scenario")
        amount = scenario.get("amount", 0)

        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()

        if scenario_type == "extra_debt_payment":
            if debts:
                d = debts[0]
                months_normal = d.current_amount / d.monthly_payment
                d.current_amount -= amount
                months_new = d.current_amount / d.monthly_payment

                return {
                    "scenario": scenario_type,
                    "months_saved": months_normal - months_new,
                    "interest_saved": (months_normal - months_new)
                    * d.current_amount
                    * (d.interest_rate / 100 / 12),
                    "new_months": months_new,
                }

        elif scenario_type == "income_change":
            incomes = self.db.query(Income).all()
            current_income = sum(i.amount for i in incomes)
            new_income = current_income + amount

            return {
                "scenario": scenario_type,
                "current_income": current_income,
                "new_income": new_income,
                "savings_potential": new_income * 0.2,
            }

        elif scenario_type == "expense_reduction":
            expenses = self.db.query(Expense).all()
            current_expenses = sum(e.amount for e in expenses)
            new_expenses = current_expenses - amount

            return {
                "scenario": scenario_type,
                "current_expenses": current_expenses,
                "new_expenses": new_expenses,
                "monthly_savings": amount,
            }

        elif scenario_type == "refinance":
            if debts:
                d = debts[0]
                old_rate = d.interest_rate
                new_rate = scenario.get("new_rate", old_rate)

                months_normal = d.current_amount / d.monthly_payment
                old_total_interest = (
                    months_normal * d.current_amount * (old_rate / 100 / 12)
                )

                new_monthly = (
                    d.current_amount
                    * (new_rate / 100 / 12)
                    / (1 - (1 + new_rate / 100 / 12) ** -months_normal)
                )
                new_total_interest = (
                    months_normal * d.current_amount * (new_rate / 100 / 12)
                )

                return {
                    "scenario": scenario_type,
                    "debt_name": d.name,
                    "old_rate": old_rate,
                    "new_rate": new_rate,
                    "old_interest": old_total_interest,
                    "new_interest": new_total_interest,
                    "interest_saved": old_total_interest - new_total_interest,
                }

        return {"scenario": scenario_type, "result": "No simulation available"}

    def calculate_real_interest(self, debt_id: int):
        debt = self.db.query(Debt).filter(Debt.id == debt_id).first()
        if not debt:
            return {"error": "Debt not found"}

        monthly_rate = debt.interest_rate / 100 / 12
        months = (
            debt.current_amount / debt.monthly_payment
            if debt.monthly_payment > 0
            else 0
        )

        if monthly_rate > 0:
            total_paid = debt.monthly_payment * months
            total_interest = total_paid - debt.current_amount
        else:
            total_interest = 0

        return {
            "debt_name": debt.name,
            "current_amount": debt.current_amount,
            "interest_rate": debt.interest_rate,
            "total_interest": max(0, total_interest),
            "total_cost": debt.current_amount + max(0, total_interest),
            "months_remaining": months,
        }

    def get_debt_projection(self, debt_id: int):
        debt = self.db.query(Debt).filter(Debt.id == debt_id).first()
        if not debt:
            return {"error": "Debt not found"}

        schedule = []
        balance = debt.current_amount
        month = 1
        monthly_rate = debt.interest_rate / 100 / 12

        while balance > 0 and month <= 360:
            interest = balance * monthly_rate
            payment = min(debt.monthly_payment, balance + interest)
            principal = payment - interest
            balance -= principal

            schedule.append(
                {
                    "month": month,
                    "payment": payment,
                    "interest": interest,
                    "principal": principal,
                    "balance": max(0, balance),
                }
            )

            if month <= 12:
                pass

            month += 1

        return {
            "debt_name": debt.name,
            "months_remaining": len(schedule),
            "total_interest": sum(s["interest"] for s in schedule),
            "schedule": schedule[:24],
        }

    def get_debt_comparison(self):
        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()

        if not debts:
            return {"debts": [], "total_monthly_payment": 0, "total_interest_yearly": 0}

        comparisons = []
        total_monthly = 0
        total_yearly_interest = 0

        for d in debts:
            monthly_rate = d.interest_rate / 100 / 12
            months = (
                d.current_amount / d.monthly_payment if d.monthly_payment > 0 else 0
            )

            if monthly_rate > 0:
                total_interest = (
                    months * d.current_amount * monthly_rate - d.current_amount
                )
            else:
                total_interest = 0

            comparisons.append(
                {
                    "name": d.name,
                    "current_amount": d.current_amount,
                    "interest_rate": d.interest_rate,
                    "monthly_payment": d.monthly_payment,
                    "total_interest": max(0, total_interest),
                    "total_cost": d.current_amount + max(0, total_interest),
                }
            )

            total_monthly += d.monthly_payment
            total_yearly_interest += max(0, total_interest) / max(1, months) * 12

        return {
            "debts": comparisons,
            "total_monthly_payment": total_monthly,
            "total_interest_yearly": total_yearly_interest,
        }

    def get_card_projection(self, card_id: int):
        card = self.db.query(CreditCard).filter(CreditCard.id == card_id).first()
        if not card:
            return {"error": "Card not found"}

        schedule = []
        balance = card.current_balance
        month = 1
        monthly_rate = card.interest_rate / 100 / 12
        minimum_payment = card.limit * 0.05

        while balance > 0 and month <= 60:
            interest = balance * monthly_rate
            payment = max(minimum_payment, balance * 0.1)

            if payment <= interest:
                warning = "Pago minimo no cubre intereses - deuda crecera"
            else:
                warning = None

            balance += interest
            balance -= payment

            schedule.append(
                {
                    "month": month,
                    "balance": max(0, balance),
                    "interest": interest,
                    "payment": payment,
                    "warning": warning,
                }
            )

            month += 1

        return {
            "card_name": card.name,
            "current_balance": card.current_balance,
            "interest_rate": card.interest_rate,
            "months_until_paidoff": len(schedule),
            "total_interest": sum(s["interest"] for s in schedule),
            "total_cost": card.current_balance + sum(s["interest"] for s in schedule),
            "warning": schedule[0]["warning"]
            if schedule and schedule[0]["warning"]
            else None,
            "schedule": schedule[:12],
        }
