from datetime import date, timedelta
from sqlalchemy.orm import Session
from main import Income, Expense, Debt, CreditCard, HouseholdService


class AIFinanceEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(self):
        recommendations = []
        today = date.today()
        first_of_month = today.replace(day=1)

        six_months_ago = today - timedelta(days=180)
        incomes = self.db.query(Income).filter(Income.date >= six_months_ago).all()
        expenses = self.db.query(Expense).filter(Expense.date >= six_months_ago).all()

        monthly_income = {}
        monthly_expenses = {}
        for i in incomes:
            key = (i.date.year, i.date.month)
            monthly_income[key] = monthly_income.get(key, 0) + i.amount

        for e in expenses:
            key = (e.date.year, e.date.month)
            monthly_expenses[key] = monthly_expenses.get(key, 0) + e.amount

        if monthly_income:
            avg_income = sum(monthly_income.values()) / len(monthly_income)
        else:
            avg_income = 0

        current_month_expenses = monthly_expenses.get((today.year, today.month), 0)
        current_month_income = monthly_income.get((today.year, today.month), avg_income)

        if current_month_income > 0:
            expense_ratio = current_month_expenses / current_month_income
            if expense_ratio > 0.9:
                recommendations.append(
                    {
                        "type": "critical",
                        "icon": "alert-triangle",
                        "message": "Gastas el 90%+ de tus ingresos. Corta gastos en deseos inmediatamente.",
                    }
                )
            elif expense_ratio > 0.75:
                recommendations.append(
                    {
                        "type": "warning",
                        "icon": "alert-circle",
                        "message": f"Gastas el {expense_ratio * 100:.0f}% de ingresos. Busca reducir gastos.",
                    }
                )
            elif expense_ratio < 0.6:
                recommendations.append(
                    {
                        "type": "success",
                        "icon": "check-circle",
                        "message": f"Excelente! Solo gastas el {expense_ratio * 100:.0f}%. Buen ahorro.",
                    }
                )

        category_totals = {"needs": 0, "wants": 0, "culture": 0, "unexpected": 0}
        recurring_expenses = {}
        for e in expenses:
            if e.category in category_totals:
                category_totals[e.category] += e.amount
            key = e.description.lower().strip() if e.description else "unknown"
            if key not in recurring_expenses:
                recurring_expenses[key] = []
            recurring_expenses[key].append(e.amount)

        total_expenses_6m = sum(category_totals.values())
        if total_expenses_6m > 0 and avg_income > 0:
            needs_ratio = category_totals["needs"] / total_expenses_6m
            wants_ratio = category_totals["wants"] / total_expenses_6m

            if avg_income > 0:
                monthly_savings_target = avg_income * 0.2
                current_savings = avg_income - (total_expenses_6m / 6)
                if current_savings < monthly_savings_target * 0.5:
                    recommendations.append(
                        {
                            "type": "suggestion",
                            "icon": "piggy-bank",
                            "message": f"Tu ahorro mensual es bajo. Meta: ${monthly_savings_target:,.0f}/mes (regla 50/30/20).",
                        }
                    )

            if needs_ratio > 0.7:
                recommendations.append(
                    {
                        "type": "warning",
                        "icon": "home",
                        "message": "Gastos en necesidades muy altos. Revisa alquiler, servicios, mercado.",
                    }
                )

        high_recurring = {
            k: v
            for k, v in recurring_expenses.items()
            if len(v) >= 3 and sum(v) / len(v) > 50
        }
        if high_recurring:
            sorted_recurring = sorted(
                high_recurring.items(),
                key=lambda x: sum(x[1]) / len(x[1]),
                reverse=True,
            )[:2]
            for desc, amounts in sorted_recurring:
                avg = sum(amounts) / len(amounts)
                recommendations.append(
                    {
                        "type": "opportunity",
                        "icon": "trending-down",
                        "message": f"'{desc}' promedio ${avg:,.0f}/mes. Posible suscripcion a optimizar.",
                    }
                )

        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()
        if debts:
            high_rate_debt = max(debts, key=lambda d: d.interest_rate)
            if high_rate_debt.interest_rate > 15:
                recommendations.append(
                    {
                        "type": "opportunity",
                        "icon": "landmark",
                        "message": f"'{high_rate_debt.name}' tiene {high_rate_debt.interest_rate}% TNA. Refinanciar podria ahorrarte ${high_rate_debt.current_amount * 0.03:,.0f}/ano.",
                    }
                )
            elif high_rate_debt.interest_rate > 10:
                recommendations.append(
                    {
                        "type": "suggestion",
                        "icon": "percent",
                        "message": f"Deuda '{high_rate_debt.name}' con {high_rate_debt.interest_rate}% TNA. Considera consolidar.",
                    }
                )

        cards = self.db.query(CreditCard).filter(CreditCard.current_balance > 0).all()
        if cards:
            total_card_debt = sum(c.current_balance for c in cards)
            avg_card_rate = (
                sum(c.interest_rate for c in cards) / len(cards) if cards else 0
            )
            if avg_card_rate > 35:
                recommendations.append(
                    {
                        "type": "critical",
                        "icon": "credit-card",
                        "message": f"Tarjetas: ${total_card_debt:,.0f} a ~{avg_card_rate:.0f}% TNA. Paga rapido!",
                    }
                )
            elif avg_card_rate > 25:
                recommendations.append(
                    {
                        "type": "warning",
                        "icon": "alert-triangle",
                        "message": f"Tasa tarjetas ~{avg_card_rate:.0f}% es alta. Considera transferencia a menor tasa.",
                    }
                )

        services = (
            self.db.query(HouseholdService)
            .filter(HouseholdService.is_active == True)
            .all()
        )
        if services:
            total_services = sum(s.amount for s in services)
            if total_services > avg_income * 0.15:
                expensive = max(services, key=lambda s: s.amount)
                recommendations.append(
                    {
                        "type": "opportunity",
                        "icon": "zap",
                        "message": f"Servicios: ${total_services:,.0f}/mes. '{expensive.name}' es el mas caro.",
                    }
                )

        return recommendations[:8]

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
        last_3_expenses = (
            self.db.query(Expense).filter(Expense.date >= last_3_months_start).all()
        )

        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()
        cards = self.db.query(CreditCard).filter(CreditCard.current_balance > 0).all()

        month_income_total = sum(i.amount for i in month_incomes)
        month_expense_total = sum(e.amount for e in month_expenses)
        prev_income_total = sum(i.amount for i in prev_incomes) if prev_incomes else 0
        prev_expense_total = (
            sum(e.amount for e in prev_expenses) if prev_expenses else 0
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
                        "message": f"Ingresos +{income_change:.1f}% vs mes pasado",
                    }
                )
            elif income_change < 0:
                insights["past_feedback"].append(
                    {
                        "type": "warning",
                        "icon": "trending-down",
                        "message": f"Ingresos {income_change:.1f}% vs mes pasado",
                    }
                )

            if expense_change > 20:
                insights["past_feedback"].append(
                    {
                        "type": "negative",
                        "icon": "alert-triangle",
                        "message": f"Gastos +{expense_change:.1f}% - Revisa gastos innecesarios",
                    }
                )
            elif expense_change < -10:
                insights["past_feedback"].append(
                    {
                        "type": "positive",
                        "icon": "check-circle",
                        "message": f"Excelente! Gastos reducidos {abs(expense_change):.1f}%",
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
                        "message": f"Deficit: gastas mas de lo que ganas ({abs(savings_rate):.1f}%)",
                    }
                )
            elif savings_rate < 10:
                insights["future_suggestions"].append(
                    {
                        "type": "suggestion",
                        "icon": "piggy-bank",
                        "message": f"Ahorro bajo ({savings_rate:.1f}%). Meta: 20%",
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
                    "message": f"Gastas {((month_expense_total / avg_monthly_expense) - 1) * 100:.0f}% mas que tu promedio",
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
                        "message": f"${needs_spent - needs_limit:,.0f} sobre presupuesto en necesidades",
                    }
                )
            if wants_spent > wants_limit:
                insights["future_suggestions"].append(
                    {
                        "type": "warning",
                        "icon": "shopping-bag",
                        "message": f"${wants_spent - wants_limit:,.0f} sobre presupuesto en deseos",
                    }
                )

        total_debt = sum(d.current_amount for d in debts)
        if total_debt > 0:
            insights["future_suggestions"].append(
                {
                    "type": "debt",
                    "icon": "landmark",
                    "message": f"${total_debt:,.0f} en deudas. Prioriza mayor interes.",
                }
            )

        total_card_debt = sum(c.current_balance for c in cards)
        if total_card_debt > month_income_total * 0.5:
            insights["future_suggestions"].append(
                {
                    "type": "warning",
                    "icon": "credit-card",
                    "message": f"Tarjetas: ${total_card_debt:,.0f} (>50% ingresos). Paga rapido!",
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
                        "message": f"Proyeccion: +${projected_total - month_income_total:,.0f} este mes",
                    }
                )

        if month_income_total > 0 and monthly_balance >= month_income_total * 0.2:
            insights["future_suggestions"].append(
                {
                    "type": "success",
                    "icon": "target",
                    "message": "Cumpliste meta de ahorro 20%",
                }
            )

        if not insights["past_feedback"]:
            insights["past_feedback"].append(
                {
                    "type": "info",
                    "icon": "info",
                    "message": "Continua asi! Manten tus habitos.",
                }
            )

        if not insights["future_suggestions"]:
            insights["future_suggestions"].append(
                {"type": "info", "icon": "thumbs-up", "message": "Vas bien! Sigue asi."}
            )

        return insights

    def detect_anomalies(self):
        anomalies = []
        opportunities = []

        expenses = self.db.query(Expense).order_by(Expense.date.desc()).limit(100).all()
        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()
        cards = self.db.query(CreditCard).filter(CreditCard.current_balance > 0).all()
        services = (
            self.db.query(HouseholdService)
            .filter(HouseholdService.is_active == True)
            .all()
        )
        today = date.today()

        by_category_desc = {}
        for e in expenses:
            key = f"{e.category}_{e.description.lower().strip()}"
            if key not in by_category_desc:
                by_category_desc[key] = []
            by_category_desc[key].append(e)

        for key, items in by_category_desc.items():
            if len(items) >= 2:
                amounts = [i.amount for i in items]
                if len(set(amounts)) == 1 and amounts[0] > 100:
                    anomalies.append(
                        {
                            "type": "anomaly",
                            "anomaly_type": "duplicate",
                            "severity": "high",
                            "icon": "copy",
                            "title": "Posible Gasto Duplicado",
                            "description": f"${amounts[0]:,.2f} x{len(items)} veces - '{items[0].description}'",
                            "potential_savings": amounts[0],
                        }
                    )

        by_category = {}
        for e in expenses:
            cat = e.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(e.amount)

        for cat, amounts in by_category.items():
            if len(amounts) >= 3:
                avg = sum(amounts) / len(amounts)
                for amt in amounts:
                    if amt > avg * 2:
                        anomalies.append(
                            {
                                "type": "anomaly",
                                "anomaly_type": "spike",
                                "severity": "medium",
                                "icon": "trending-up",
                                "title": "Gasto Inusual",
                                "description": f"{cat}: ${amt:,.2f} (promedio: ${avg:,.2f})",
                                "potential_savings": amt - avg,
                            }
                        )
                        break

        for s in services:
            if s.last_paid_date:
                days_since = (today - s.last_paid_date).days
                if days_since > 60:
                    anomalies.append(
                        {
                            "type": "anomaly",
                            "anomaly_type": "inactive_service",
                            "severity": "low",
                            "icon": "alert-triangle",
                            "title": "Servicio Sin Pagos",
                            "description": f"{s.name} sin pago hace {days_since} dias",
                            "potential_savings": s.amount,
                        }
                    )

        if cards:
            high_rate_card = max(cards, key=lambda c: c.interest_rate)
            if high_rate_card.interest_rate > 35:
                monthly_interest = high_rate_card.current_balance * (
                    high_rate_card.interest_rate / 100 / 12
                )
                opportunities.append(
                    {
                        "type": "opportunity",
                        "anomaly_type": "high_interest",
                        "severity": "high",
                        "icon": "credit-card",
                        "title": "Tasa Tarjeta Muy Alta",
                        "description": f"'{high_rate_card.name}' a {high_rate_card.interest_rate}% TNA. Interes mensual: ${monthly_interest:,.0f}",
                        "potential_savings": monthly_interest * 12,
                    }
                )

        if debts:
            high_rate = max(debts, key=lambda d: d.interest_rate)
            if high_rate.interest_rate > 15:
                yearly_interest = high_rate.current_amount * (
                    high_rate.interest_rate / 100
                )
                avg_rate = sum(d.interest_rate for d in debts) / len(debts)
                if avg_rate < high_rate.interest_rate - 5:
                    opportunities.append(
                        {
                            "type": "opportunity",
                            "anomaly_type": "refinance",
                            "severity": "medium",
                            "icon": "landmark",
                            "title": "Refinanciar Deuda Alta",
                            "description": f"'{high_rate.name}' a {high_rate.interest_rate}% vs promedio {avg_rate:.1f}%. Refinanciar podria ahorrar ${yearly_interest * 0.2:,.0f}/ano",
                            "potential_savings": yearly_interest * 0.2,
                        }
                    )

        recurring = {
            k: v
            for k, v in by_category_desc.items()
            if len(v) >= 3 and sum(i.amount for i in v) / len(v) > 30
        }
        for key, items in list(recurring.items())[:2]:
            avg = sum(i.amount for i in items) / len(items)
            yearly = avg * 12
            if yearly > 200:
                opportunities.append(
                    {
                        "type": "opportunity",
                        "anomaly_type": "subscription",
                        "severity": "low",
                        "icon": "repeat",
                        "title": "Suscripcion Recurrente",
                        "description": f"'{items[0].description}' ~${avg:,.0f}/mes = ${yearly:,.0f}/ano",
                        "potential_savings": yearly * 0.3,
                    }
                )

        result = anomalies[:5] + opportunities[:5]
        return result

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
                "has_debts": False,
                "total_debt": 0,
                "total_months": 0,
                "total_interest": 0,
                "total_cost": 0,
                "priority_order": [],
                "monthly_plan": [],
                "summary": "No tienes deudas activas. Excelente!",
                "recommendation": "Mantén este estilo de vida financiero.",
            }

        debts = [
            {
                "id": d.id,
                "name": d.name,
                "balance": d.current_amount,
                "monthly_payment": d.monthly_payment,
                "rate": d.interest_rate,
            }
            for d in debts_data
        ]

        if strategy == "snowball":
            debts = sorted(debts, key=lambda d: d["balance"])
        else:
            debts = sorted(debts, key=lambda d: d["rate"], reverse=True)

        total_debt = sum(d["balance"] for d in debts)
        total_monthly = sum(d["monthly_payment"] for d in debts)
        total_rate = (
            sum(d["balance"] * d["rate"] for d in debts) / total_debt
            if total_debt > 0
            else 0
        )

        min_payoff_months = (
            max((d["balance"] / d["monthly_payment"]) for d in debts) if debts else 0
        )
        avg_interest = total_rate / 100 / 12
        estimated_interest = total_debt * avg_interest * min_payoff_months

        priority_order = [
            {
                "name": d["name"],
                "balance": d["balance"],
                "rate": d["rate"],
                "monthly_payment": d["monthly_payment"],
                "payoff_months": round(d["balance"] / d["monthly_payment"], 1),
                "reason": f"Mayor tasa ({d['rate']}%)"
                if strategy == "avalanche"
                else f"Menor saldo (${d['balance']:,.0f})",
            }
            for d in debts
        ]

        summary = f"Total: ${total_debt:,.0f} | Pago mensual: ${total_monthly:,.0f} | Tasa promedio: {total_rate:.1f}%"

        recommendation = (
            (
                "Paga minimo en todas las deudas. Con ${total_monthly:,.0f}/mes disponibles, enfocate primero en "
                f"'{debts[0]['name']}' ({debts[0]['rate']}% TNA). Una vez pagada, aplica ese pago a la siguiente."
            )
            if debts
            else ""
        )

        return {
            "strategy": strategy,
            "strategy_name": "Avalancha"
            if strategy == "avalanche"
            else "Bola de Nieve",
            "has_debts": True,
            "total_debt": round(total_debt, 2),
            "total_monthly_payment": round(total_monthly, 2),
            "average_rate": round(total_rate, 2),
            "total_months_estimate": round(min_payoff_months, 1),
            "estimated_total_interest": round(estimated_interest, 2),
            "priority_order": priority_order,
            "monthly_plan": [],
            "summary": summary,
            "recommendation": recommendation,
            "tips": [
                f"1. Paga minimo ${d['monthly_payment']:,.0f} en '{d['name']}'"
                for d in debts
            ]
            + [
                f"{len(debts) + 1}. Usa el pago de '{debts[0]['name']}' para pagar la siguiente deuda mas rapido."
            ],
        }

    def simulate_scenario(self, scenario: dict):
        scenario_type = scenario.get("scenario", "")
        amount = float(scenario.get("amount", 0))
        new_rate = float(scenario.get("new_rate", 0))

        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()
        incomes = self.db.query(Income).all()
        expenses = self.db.query(Expense).all()

        current_income = (
            sum(i.amount for i in incomes)
            / max(1, len(set((i.date.year, i.date.month) for i in incomes)))
            if incomes
            else 0
        )
        current_expenses = (
            sum(e.amount for e in expenses)
            / max(1, len(set((e.date.year, e.date.month) for e in expenses)))
            if expenses
            else 0
        )

        if scenario_type == "income_change":
            monthly_extra = amount
            yearly_extra = amount * 12
            savings_increase = monthly_extra * 0.2
            return {
                "scenario": "income_change",
                "current_monthly": round(current_income, 2),
                "new_monthly": round(current_income + amount, 2),
                "extra_available": round(monthly_extra, 2),
                "recommended_savings": round(savings_increase, 2),
                "yearly_impact": round(yearly_extra * 0.2, 2),
                "impact": "positive",
                "summary": f"+${amount:,.0f}/mes = +${savings_increase:,.0f} al ahorro mensual",
            }

        elif scenario_type == "expense_reduction":
            monthly_savings = amount
            yearly_savings = amount * 12
            debt_impact = f"Puedes pagar ${yearly_savings:,.0f} extra de deuda por ano"
            return {
                "scenario": "expense_reduction",
                "current_expenses": round(current_expenses, 2),
                "new_expenses": round(current_expenses - amount, 2),
                "monthly_savings": round(monthly_savings, 2),
                "yearly_savings": round(yearly_savings, 2),
                "impact": "positive",
                "summary": f"Ahorra ${yearly_savings:,.0f}/ano. {debt_impact}",
            }

        elif scenario_type == "extra_debt_payment":
            if not debts:
                return {
                    "scenario": "extra_debt_payment",
                    "impact": "neutral",
                    "summary": "No hay deudas activas",
                }

            d = debts[0]
            monthly_rate = d.interest_rate / 100 / 12
            months_normal = (
                d.current_amount / d.monthly_payment if d.monthly_payment > 0 else 0
            )
            interest_normal = d.current_amount * monthly_rate * months_normal

            new_payment = d.monthly_payment + amount
            months_new = d.current_amount / new_payment if new_payment > 0 else 0
            interest_new = d.current_amount * monthly_rate * months_new

            months_saved = months_normal - months_new
            interest_saved = interest_normal - interest_new

            return {
                "scenario": "extra_debt_payment",
                "debt_name": d.name,
                "current_balance": round(d.current_amount, 2),
                "current_payment": round(d.monthly_payment, 2),
                "extra_payment": round(amount, 2),
                "new_payment": round(new_payment, 2),
                "months_saved": round(max(0, months_saved), 1),
                "interest_saved": round(max(0, interest_saved), 2),
                "payoff_earlier": round(max(0, months_saved / 12), 2),
                "impact": "positive",
                "summary": f"+${amount:,.0f}/mes = -{months_saved:.1f} meses, ahorra ${interest_saved:,.0f} en intereses",
            }

        elif scenario_type == "refinance":
            if not debts:
                return {
                    "scenario": "refinance",
                    "impact": "neutral",
                    "summary": "No hay deudas activas",
                }

            d = debts[0]
            old_rate = d.interest_rate
            rate_reduction = old_rate - new_rate
            monthly_rate_old = old_rate / 100 / 12
            monthly_rate_new = new_rate / 100 / 12

            months = (
                d.current_amount / d.monthly_payment if d.monthly_payment > 0 else 0
            )

            old_monthly_interest = d.current_amount * monthly_rate_old
            new_monthly_interest = d.current_amount * monthly_rate_new
            monthly_savings = old_monthly_interest - new_monthly_interest

            yearly_savings = monthly_savings * 12
            total_savings = monthly_savings * months

            return {
                "scenario": "refinance",
                "debt_name": d.name,
                "current_rate": old_rate,
                "new_rate": new_rate,
                "rate_reduction": rate_reduction,
                "monthly_interest_current": round(old_monthly_interest, 2),
                "monthly_interest_new": round(new_monthly_interest, 2),
                "monthly_savings": round(max(0, monthly_savings), 2),
                "yearly_savings": round(max(0, yearly_savings), 2),
                "total_savings": round(max(0, total_savings), 2),
                "impact": "positive" if monthly_savings > 0 else "negative",
                "summary": f"Bajar de {old_rate}% a {new_rate}% = ${monthly_savings:,.0f}/mes = ${total_savings:,.0f} total",
            }

        return {
            "scenario": scenario_type,
            "impact": "neutral",
            "summary": "Tipo de escenario no reconocido",
        }

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
            "monthly_payment": debt.monthly_payment,
            "total_interest": max(0, total_interest),
            "total_cost": debt.current_amount + max(0, total_interest),
            "months_remaining": round(months, 1),
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
                    "payment": round(payment, 2),
                    "interest": round(interest, 2),
                    "principal": round(principal, 2),
                    "balance": round(max(0, balance), 2),
                }
            )
            month += 1

        return {
            "debt_name": debt.name,
            "months_remaining": len(schedule),
            "total_interest": round(sum(s["interest"] for s in schedule), 2),
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
                    "is_high_rate": d.interest_rate > 15,
                }
            )

            total_monthly += d.monthly_payment
            total_yearly_interest += max(0, total_interest) / max(1, months) * 12

        return {
            "debts": comparisons,
            "total_monthly_payment": total_monthly,
            "total_interest_yearly": round(total_yearly_interest, 2),
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

            warning = None
            if payment <= interest:
                warning = "Pago minimo no cubre intereses - deuda crecera"

            balance += interest
            balance -= payment

            schedule.append(
                {
                    "month": month,
                    "balance": round(max(0, balance), 2),
                    "interest": round(interest, 2),
                    "payment": round(payment, 2),
                    "warning": warning,
                }
            )
            month += 1

        return {
            "card_name": card.name,
            "current_balance": card.current_balance,
            "interest_rate": card.interest_rate,
            "months_until_paidoff": len(schedule),
            "total_interest": round(sum(s["interest"] for s in schedule), 2),
            "total_cost": card.current_balance + sum(s["interest"] for s in schedule),
            "warning": schedule[0]["warning"]
            if schedule and schedule[0]["warning"]
            else None,
            "schedule": schedule[:12],
        }

    def get_cashflow_timeline(self):
        """Predict when the family will run out of money or reach savings goals."""
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        incomes = self.db.query(Income).filter(Income.date >= three_months_ago).all()
        expenses = self.db.query(Expense).filter(Expense.date >= three_months_ago).all()
        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()
        cards = self.db.query(CreditCard).filter(CreditCard.current_balance > 0).all()

        if not incomes:
            return {
                "has_data": False,
                "message": "No hay suficientes datos de ingresos",
            }

        current_balance = sum(i.amount for i in incomes) - sum(
            e.amount for e in expenses
        )

        avg_monthly_income = sum(i.amount for i in incomes) / 3
        avg_monthly_expense = sum(e.amount for e in expenses) / 3

        monthly_net = avg_monthly_income - avg_monthly_expense

        days_until_month_end = 30 - today.day
        remaining_this_month = monthly_net * (days_until_month_end / 30)

        projected_balance = current_balance + remaining_this_month

        timeline = {
            "has_data": True,
            "current_situation": {
                "balance": round(current_balance, 2),
                "monthly_income": round(avg_monthly_income, 2),
                "monthly_expense": round(avg_monthly_expense, 2),
                "monthly_net": round(monthly_net, 2),
                "is_surplus": monthly_net > 0,
            },
            "projections": [],
            "debt_impact": {
                "monthly_debt_payments": round(sum(d.monthly_payment for d in debts), 2)
                if debts
                else 0,
                "monthly_card_minimum": round(sum(c.limit * 0.05 for c in cards), 2)
                if cards
                else 0,
            },
        }

        current_month_balance = projected_balance
        for month in range(1, 7):
            if monthly_net > 0:
                current_month_balance += monthly_net
                balance_after_debt = (
                    current_month_balance - sum(d.monthly_payment for d in debts)
                    if debts
                    else current_month_balance
                )

                timeline["projections"].append(
                    {
                        "month": month,
                        "label": f"Mes {month}",
                        "balance": round(current_month_balance, 2),
                        "after_debt": round(balance_after_debt, 2),
                        "is_negative": current_month_balance < 0,
                        "is_critical": current_month_balance
                        < avg_monthly_expense * 0.5,
                    }
                )
            else:
                current_month_balance += monthly_net
                timeline["projections"].append(
                    {
                        "month": month,
                        "label": f"Mes {month}",
                        "balance": round(current_month_balance, 2),
                        "after_debt": round(
                            current_month_balance
                            - sum(d.monthly_payment for d in debts)
                            if debts
                            else current_month_balance,
                            2,
                        ),
                        "is_negative": True,
                        "is_critical": True,
                    }
                )

        if monthly_net < 0:
            months_until_zero = (
                abs(current_balance / monthly_net) if monthly_net != 0 else 0
            )
            timeline["warning"] = {
                "type": "critical",
                "message": f"Agotaras tus ahorros en aproximadamente {int(months_until_zero)} meses",
                "months_remaining": round(months_until_zero, 1),
            }
        elif current_balance < avg_monthly_expense:
            timeline["warning"] = {
                "type": "warning",
                "message": "Tu ahorro es menor a un mes de gastos. Recomendamos incrementar ingresos o reducir gastos.",
            }
        else:
            months_safe = current_balance / abs(monthly_net) if monthly_net > 0 else 999
            timeline["warning"] = {
                "type": "success",
                "message": f"Tienes {int(current_balance / avg_monthly_expense)} meses de gastos como reserva de emergencia",
            }

        return timeline

    def get_behavioral_insights(self):
        """Analyze spending patterns and detect habits."""
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        expenses = self.db.query(Expense).filter(Expense.date >= three_months_ago).all()

        if not expenses:
            return {"has_data": False, "insights": []}

        insights = []

        by_day_of_week = {i: [] for i in range(7)}
        for e in expenses:
            by_day_of_week[e.date.weekday()].append(e.amount)

        day_names = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
        ]
        avg_by_day = [
            (day, sum(amounts) / len(amounts) if amounts else 0)
            for day, amounts in by_day_of_week.items()
        ]
        avg_by_day.sort(key=lambda x: x[1], reverse=True)

        if avg_by_day[0][1] > avg_by_day[-1][1] * 1.3:
            highest_day = day_names[avg_by_day[0][0]]
            lowest_day = day_names[avg_by_day[-1][0]]
            insights.append(
                {
                    "type": "pattern",
                    "severity": "info",
                    "icon": "calendar",
                    "title": f"Patron de gasto semanal",
                    "description": f"Gastas más los {highest_day}s (${avg_by_day[0][1]:,.0f} promedio) y menos los {lowest_day}s (${avg_by_day[-1][1]:,.0f})",
                    "action": f"Considera hacer tus compras importantes los {lowest_day}s para ahorrar",
                }
            )

        impulse_threshold = sum(e.amount for e in expenses) / len(expenses) * 3
        potential_impulse = [e for e in expenses if e.amount > impulse_threshold]
        if len(potential_impulse) > 3:
            total_impulse = sum(e.amount for e in potential_impulse)
            insights.append(
                {
                    "type": "warning",
                    "severity": "high",
                    "icon": "shopping-cart",
                    "title": "Posibles compras impulsivas",
                    "description": f"{len(potential_impulse)} gastos superiores a ${impulse_threshold:,.0f} (3x promedio). Total: ${total_impulse:,.0f}",
                    "action": "Antes de comprar algo mayor a tu gasto promedio x3, espera 24 horas",
                }
            )

        category_trends = {}
        for e in expenses:
            cat = e.category
            if cat not in category_trends:
                category_trends[cat] = []
            category_trends[cat].append((e.date, e.amount))

        for cat, items in category_trends.items():
            if len(items) >= 3:
                items.sort(key=lambda x: x[0])
                recent = [i[1] for i in items[-3:]]
                older = [i[1] for i in items[:-3]] if len(items) > 3 else [recent[0]]

                if older and sum(recent) / len(recent) > sum(older) / len(older) * 1.2:
                    increase = (
                        (sum(recent) / len(recent)) / (sum(older) / len(older)) - 1
                    ) * 100
                    insights.append(
                        {
                            "type": "trend",
                            "severity": "warning",
                            "icon": "trending-up",
                            "title": f"Gasto creciente en {cat}",
                            "description": f"Esta categoría ha aumentado {increase:.0f}% en los últimos meses",
                            "action": f"Revisa si puedes reducir gastos en {cat}",
                        }
                    )

        recurring_categories = {}
        for e in expenses:
            key = f"{e.category}_{e.description.lower().strip() if e.description else 'unknown'}"
            if key not in recurring_categories:
                recurring_categories[key] = []
            recurring_categories[key].append(e.amount)

        subscription_candidates = []
        for key, amounts in recurring_categories.items():
            if len(amounts) >= 2 and max(amounts) / min(amounts) < 1.1:
                avg = sum(amounts) / len(amounts)
                yearly = avg * 12
                if yearly > 100:
                    subscription_candidates.append((key.split("_")[0], avg))

        if subscription_candidates:
            subscription_candidates.sort(key=lambda x: x[1], reverse=True)
            top_subs = subscription_candidates[:3]
            total_subs = sum(s[1] for s in top_subs) * 12
            insights.append(
                {
                    "type": "subscription",
                    "severity": "info",
                    "icon": "repeat",
                    "title": f"Suscripciones detectadas ({len(top_subs)})",
                    "description": f"~${sum(s[1] for s in top_subs):,.0f}/mes = ${total_subs:,.0f}/año",
                    "action": "Revisa cuáles realmente usas y cancela las que no",
                }
            )

        return {"has_data": True, "insights": insights}

    def get_savings_coach(self):
        """Provide personalized savings guidance with goals."""
        today = date.today()
        first_of_month = today.replace(day=1)

        incomes = self.db.query(Income).filter(Income.date >= first_of_month).all()
        expenses = self.db.query(Expense).filter(Expense.date >= first_of_month).all()

        if not incomes:
            return {"has_data": False}

        monthly_income = sum(i.amount for i in incomes)

        needs_budget = monthly_income * 0.50
        wants_budget = monthly_income * 0.30
        savings_target = monthly_income * 0.20

        needs_spent = sum(e.amount for e in expenses if e.category == "needs")
        wants_spent = sum(e.amount for e in expenses if e.category == "wants")
        savings_actual = monthly_income - sum(e.amount for e in expenses)

        coach = {
            "has_data": True,
            "monthly_income": round(monthly_income, 2),
            "budget": {
                "needs": {
                    "budget": round(needs_budget, 2),
                    "spent": round(needs_spent, 2),
                    "remaining": round(max(0, needs_budget - needs_spent), 2),
                },
                "wants": {
                    "budget": round(wants_budget, 2),
                    "spent": round(wants_spent, 2),
                    "remaining": round(max(0, wants_budget - wants_spent), 2),
                },
                "savings": {
                    "target": round(savings_target, 2),
                    "actual": round(max(0, savings_actual), 2),
                    "gap": round(max(0, savings_target - savings_actual), 2),
                },
            },
            "tips": [],
        }

        if savings_actual < savings_target:
            shortfall = savings_target - savings_actual
            if wants_spent > wants_budget:
                overspend = wants_spent - wants_budget
                coach["tips"].append(
                    {
                        "priority": "high",
                        "icon": "scissors",
                        "tip": f"Reduce gastos en 'Deseos' en ${overspend:,.0f} para alcanzar tu meta de ahorro",
                    }
                )
            else:
                coach["tips"].append(
                    {
                        "priority": "medium",
                        "icon": "target",
                        "tip": f"Reduce ${shortfall:,.0f} adicionales para cumplir la regla 50/30/20",
                    }
                )

        if needs_spent > needs_budget * 1.1:
            coach["tips"].append(
                {
                    "priority": "high",
                    "icon": "home",
                    "tip": "Gastos en necesidades están muy altos. Revisa servicios fijos y mercado",
                }
            )

        if savings_actual >= savings_target:
            coach["tips"].append(
                {
                    "priority": "success",
                    "icon": "trophy",
                    "tip": f"Excelente! Ya ahorraste ${savings_actual:,.0f} este mes ({savings_actual / monthly_income * 100:.0f}% del ingreso)",
                }
            )

        days_remaining = 30 - today.day
        days_passed = today.day
        if days_remaining > 0:
            daily_budget_wants = coach["budget"]["wants"]["remaining"] / days_remaining
            if daily_budget_wants < 5:
                coach["tips"].append(
                    {
                        "priority": "warning",
                        "icon": "alert-circle",
                        "tip": f"Te quedan ${coach['budget']['wants']['remaining']:,.0f} para {days_remaining} días. Solo ${daily_budget_wants:,.0f}/día disponible",
                    }
                )

        return coach

    def get_actionable_insights(self):
        """Generate top 5 actionable insights for the family."""
        insights = []

        cashflow = self.get_cashflow_timeline()
        behavioral = self.get_behavioral_insights()
        coach = self.get_savings_coach()

        if cashflow.get("warning"):
            w = cashflow["warning"]
            if w["type"] == "critical":
                insights.append(
                    {
                        "priority": 1,
                        "type": "urgent",
                        "icon": "alert-octagon",
                        "title": "Emergencia Financiera",
                        "description": w["message"],
                        "action": "Reduce gastos inmediatamente o busca ingresos extra",
                    }
                )
            elif w["type"] == "warning":
                insights.append(
                    {
                        "priority": 2,
                        "type": "warning",
                        "icon": "alert-triangle",
                        "title": "Reserva Baja",
                        "description": w["message"],
                        "action": "Prioriza generar reserva de emergencia",
                    }
                )

        for bi in behavioral.get("insights", []):
            if bi.get("severity") == "high" and len(insights) < 5:
                insights.append(
                    {
                        "priority": 3,
                        "type": "behavior",
                        "icon": bi.get("icon", "lightbulb"),
                        "title": bi.get("title", "Patrón Detectado"),
                        "description": bi.get("description", ""),
                        "action": bi.get("action", ""),
                    }
                )

        if coach.get("tips"):
            for tip in coach["tips"]:
                if tip.get("priority") == "high" and len(insights) < 5:
                    insights.append(
                        {
                            "priority": 4,
                            "type": "savings",
                            "icon": tip.get("icon", "piggy-bank"),
                            "title": "Oportunidad de Ahorro",
                            "description": tip.get("tip", ""),
                            "action": "Implementa este cambio esta semana",
                        }
                    )
                    break

        debts = self.db.query(Debt).filter(Debt.is_paid == False).all()
        if debts:
            high_rate = max(debts, key=lambda d: d.interest_rate)
            if high_rate.interest_rate > 15:
                yearly_interest = high_rate.current_amount * (
                    high_rate.interest_rate / 100
                )
                insights.append(
                    {
                        "priority": 5,
                        "type": "debt",
                        "icon": "landmark",
                        "title": "Deuda de Alto Costo",
                        "description": f"'{high_rate.name}' a {high_rate.interest_rate}% TNA = ${yearly_interest:,.0f}/año en intereses",
                        "action": "Considera refinanciar o hacer pagos extra",
                    }
                )

        insights.sort(key=lambda x: x["priority"])
        return insights[:5]
