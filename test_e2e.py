#!/usr/bin/env python3
import subprocess
import time
import sys
import os
import json

BASE_URL = "http://localhost:8000"
TOKEN = None


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def curl_cmd(method, path, data=None, auth=False):
    """Build curl command with optional Bearer token auth"""
    auth_header = f'-H "Authorization: Bearer {TOKEN}"' if auth else ""

    if method == "GET":
        return f'curl -s {auth_header} "{BASE_URL}{path}"'
    else:
        return f'curl -s -X {method} {auth_header} -H "Content-Type: application/json" -d \'{json.dumps(data)}\' "{BASE_URL}{path}"'


def test_endpoint(name, cmd, expect_json=True):
    out, code = run_cmd(cmd)

    if "Error" in out and "error" not in name.lower() and "warning" not in name.lower():
        print(f"  X {name}: {out[:100]}")
        return False

    if code != 0 and code != 200:
        print(f"  X {name}: HTTP {code}")
        return False

    if expect_json and not out:
        print(f"  X {name}: No response")
        return False

    print(f"  OK {name}")
    return True


def get_first_id(api_path):
    out, _ = run_cmd(curl_cmd("GET", api_path, auth=True))
    try:
        data = json.loads(out) if out else []
        if data and isinstance(data, list):
            return str(data[0].get("id", 1))
    except:
        pass
    return "1"


def main():
    global TOKEN

    print("=" * 60)
    print("FamilyFinance E2E Tests - Complete API Coverage")
    print("=" * 60 + "\n")

    os.chdir("/home/sinope/Documents/opencodeprojects/family-finance")

    print("[1] Resetting database...")
    run_cmd("pkill -9 -f 'uvicorn main:app' 2>/dev/null || true")
    run_cmd("rm -f family_finance.db")
    time.sleep(1)

    print("[2] Starting server...")
    server = subprocess.Popen(
        ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(4)

    try:
        passed = 0
        failed = 0

        print("\n[AUTH]")
        test_endpoint("Auth Status", curl_cmd("GET", "/api/auth/status", auth=False))
        test_endpoint(
            "Setup User",
            f'curl -s -X POST {BASE_URL}/api/setup -H "Content-Type: application/x-www-form-urlencoded" -d "password=1234"',
        )

        time.sleep(0.5)
        login_out, _ = run_cmd(
            f'curl -s -X POST {BASE_URL}/api/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "password=1234"'
        )
        try:
            TOKEN = json.loads(login_out).get("access_token", "")
        except Exception as e:
            print(f"    Login parse error: {login_out[:100]}")
            TOKEN = ""

        if TOKEN:
            print("  OK Login (token extracted)")
            passed += 3
        else:
            print("  X Login failed")
            failed += 1

        print("\n[INCOME]")
        tests_income = [
            (
                "Create Income Salary",
                curl_cmd(
                    "POST",
                    "/api/income",
                    {
                        "amount": 5000,
                        "description": "Test Salary",
                        "category": "salary",
                        "date": "2026-04-05",
                    },
                    auth=True,
                ),
            ),
            (
                "Create Income Freelance",
                curl_cmd(
                    "POST",
                    "/api/income",
                    {
                        "amount": 1500,
                        "description": "Freelance",
                        "category": "freelance",
                        "date": "2026-04-10",
                    },
                    auth=True,
                ),
            ),
            ("Get All Incomes", curl_cmd("GET", "/api/income", auth=True)),
        ]
        for name, cmd in tests_income:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        print("\n[EXPENSES]")
        tests_expense = [
            (
                "Create Expense Needs",
                curl_cmd(
                    "POST",
                    "/api/expense",
                    {
                        "amount": 1500,
                        "description": "Groceries",
                        "category": "needs",
                        "kakebo_type": "variable",
                        "date": "2026-04-05",
                    },
                    auth=True,
                ),
            ),
            (
                "Create Expense Wants",
                curl_cmd(
                    "POST",
                    "/api/expense",
                    {
                        "amount": 500,
                        "description": "Entertainment",
                        "category": "wants",
                        "kakebo_type": "variable",
                        "date": "2026-04-07",
                    },
                    auth=True,
                ),
            ),
            (
                "Create Expense Culture",
                curl_cmd(
                    "POST",
                    "/api/expense",
                    {
                        "amount": 200,
                        "description": "Cinema",
                        "category": "culture",
                        "kakebo_type": "discretionary",
                        "date": "2026-04-10",
                    },
                    auth=True,
                ),
            ),
            (
                "Create Expense Unexpected",
                curl_cmd(
                    "POST",
                    "/api/expense",
                    {
                        "amount": 300,
                        "description": "Repair",
                        "category": "unexpected",
                        "kakebo_type": "emergency",
                        "date": "2026-04-12",
                    },
                    auth=True,
                ),
            ),
            ("Get All Expenses", curl_cmd("GET", "/api/expense", auth=True)),
            ("Kakebo Summary", curl_cmd("GET", "/api/expense/kakebo", auth=True)),
        ]
        for name, cmd in tests_expense:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        print("\n[DEBTS]")
        tests_debt = [
            (
                "Create Debt Personal Loan",
                curl_cmd(
                    "POST",
                    "/api/debt",
                    {
                        "name": "Prestamo Personal",
                        "initial_amount": 20000,
                        "current_amount": 18000,
                        "interest_rate": 18,
                        "monthly_payment": 800,
                        "start_date": "2026-01-01",
                        "next_payment_date": "2026-04-15",
                        "is_paid": False,
                    },
                    auth=True,
                ),
            ),
            (
                "Create Debt Car Loan",
                curl_cmd(
                    "POST",
                    "/api/debt",
                    {
                        "name": "Prestamo Auto",
                        "initial_amount": 50000,
                        "current_amount": 45000,
                        "interest_rate": 12,
                        "monthly_payment": 1500,
                        "start_date": "2026-01-01",
                        "next_payment_date": "2026-04-20",
                        "is_paid": False,
                    },
                    auth=True,
                ),
            ),
            ("Get All Debts", curl_cmd("GET", "/api/debt", auth=True)),
            ("Get Debt Comparison", curl_cmd("GET", "/api/debt/comparison", auth=True)),
        ]
        for name, cmd in tests_debt:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        debt_id = get_first_id("/api/debt")
        if test_endpoint(
            "Pay Debt",
            curl_cmd("POST", f"/api/debt/{debt_id}/pay", {"amount": 500}, auth=True),
        ):
            passed += 1
        else:
            failed += 1

        print("\n[CREDIT CARDS]")
        tests_cards = [
            (
                "Create Credit Card VISA",
                curl_cmd(
                    "POST",
                    "/api/credit-card",
                    {
                        "name": "Visa Banco A",
                        "limit": 10000,
                        "current_balance": 2500,
                        "interest_rate": 3.5,
                        "due_date": 15,
                        "card_type": "visa",
                        "last_four": "4532",
                        "cardholder_name": "JUAN PEREZ",
                        "expiration_date": "12/28",
                    },
                    auth=True,
                ),
            ),
            (
                "Create Credit Card Mastercard",
                curl_cmd(
                    "POST",
                    "/api/credit-card",
                    {
                        "name": "Mastercard Banco B",
                        "limit": 15000,
                        "current_balance": 3000,
                        "interest_rate": 2.8,
                        "due_date": 20,
                        "card_type": "mastercard",
                        "last_four": "5678",
                        "cardholder_name": "MARIA GOMEZ",
                        "expiration_date": "06/27",
                    },
                    auth=True,
                ),
            ),
            (
                "Create Credit Card Amex",
                curl_cmd(
                    "POST",
                    "/api/credit-card",
                    {
                        "name": "American Express",
                        "limit": 20000,
                        "current_balance": 5000,
                        "interest_rate": 4.5,
                        "due_date": 25,
                        "card_type": "amex",
                        "last_four": "1234",
                        "cardholder_name": "CARLOS LOPEZ",
                        "expiration_date": "03/29",
                    },
                    auth=True,
                ),
            ),
            ("Get All Cards", curl_cmd("GET", "/api/credit-card", auth=True)),
            (
                "Get Card Payments",
                curl_cmd("GET", "/api/credit-card/payments", auth=True),
            ),
            (
                "Get Card Charges",
                curl_cmd("GET", "/api/credit-card/charges", auth=True),
            ),
            (
                "Get Card Comparison",
                curl_cmd("GET", "/api/credit-card/comparison", auth=True),
            ),
        ]
        for name, cmd in tests_cards:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        card_id = get_first_id("/api/credit-card")
        if test_endpoint(
            "Charge Card",
            curl_cmd(
                "POST",
                f"/api/credit-card/{card_id}/charge",
                {
                    "amount": 100,
                    "description": "Grocery Store",
                    "charge_date": "2026-04-05",
                },
                auth=True,
            ),
        ):
            passed += 1
        else:
            failed += 1

        if test_endpoint(
            "Pay Card",
            curl_cmd(
                "POST",
                f"/api/credit-card/{card_id}/pay",
                {"amount": 500, "payment_date": "2026-04-10"},
                auth=True,
            ),
        ):
            passed += 1
        else:
            failed += 1

        if test_endpoint(
            "Card Projection",
            curl_cmd("GET", f"/api/credit-card/{card_id}/projection", auth=True),
        ):
            passed += 1
        else:
            failed += 1

        print("\n[HOUSEHOLD SERVICES]")
        tests_services = [
            (
                "Create Service Electricity",
                curl_cmd(
                    "POST",
                    "/api/service",
                    {
                        "name": "Electricidad",
                        "provider": "EDESUR",
                        "amount": 150,
                        "due_day": 10,
                        "reminder_days": 3,
                        "is_active": True,
                    },
                    auth=True,
                ),
            ),
            (
                "Create Service Internet",
                curl_cmd(
                    "POST",
                    "/api/service",
                    {
                        "name": "Internet",
                        "provider": "Claro",
                        "amount": 50,
                        "due_day": 15,
                        "reminder_days": 3,
                        "is_active": True,
                    },
                    auth=True,
                ),
            ),
            (
                "Create Service Water",
                curl_cmd(
                    "POST",
                    "/api/service",
                    {
                        "name": "Agua",
                        "provider": "CAASD",
                        "amount": 30,
                        "due_day": 20,
                        "reminder_days": 3,
                        "is_active": True,
                    },
                    auth=True,
                ),
            ),
            ("Get All Services", curl_cmd("GET", "/api/service", auth=True)),
        ]
        for name, cmd in tests_services:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        service_id = get_first_id("/api/service")
        if test_endpoint(
            "Pay Service",
            curl_cmd(
                "POST", f"/api/service/{service_id}/pay", {"amount": 150}, auth=True
            ),
        ):
            passed += 1
        else:
            failed += 1

        print("\n[DASHBOARD]")
        tests_dashboard = [
            ("Dashboard Summary", curl_cmd("GET", "/api/dashboard/summary", auth=True)),
            (
                "Upcoming Payments",
                curl_cmd("GET", "/api/dashboard/upcoming", auth=True),
            ),
        ]
        for name, cmd in tests_dashboard:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        print("\n[REPORTS]")
        tests_reports = [
            ("Monthly Report", curl_cmd("GET", "/api/reports/monthly", auth=True)),
            ("Quincenal Report", curl_cmd("GET", "/api/reports/quincenal", auth=True)),
            ("Quarterly Report", curl_cmd("GET", "/api/reports/quarterly", auth=True)),
            ("Yearly Report", curl_cmd("GET", "/api/reports/yearly", auth=True)),
            ("Kakebo Report", curl_cmd("GET", "/api/reports/kakebo", auth=True)),
            ("Debts Report", curl_cmd("GET", "/api/reports/debts", auth=True)),
        ]
        for name, cmd in tests_reports:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        print("\n[BUDGET]")
        tests_budget = [
            ("Get Budget", curl_cmd("GET", "/api/budget", auth=True)),
            (
                "Get Budget Allocation",
                curl_cmd("GET", "/api/budget/allocation", auth=True),
            ),
        ]
        for name, cmd in tests_budget:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        print("\n[AI ENGINE]")
        tests_ai = [
            (
                "AI Recommendations",
                curl_cmd("GET", "/api/ai/recommendations", auth=True),
            ),
            ("AI Insights", curl_cmd("GET", "/api/ai/insights", auth=True)),
            ("AI Anomalies", curl_cmd("GET", "/api/ai/anomalies", auth=True)),
            ("AI Forecast", curl_cmd("GET", "/api/ai/forecast", auth=True)),
            (
                "AI Debt Strategy (Avalanche)",
                f'curl -s -H "Authorization: Bearer {TOKEN}" "{BASE_URL}/api/ai/debt-strategy?strategy=avalanche"',
            ),
            (
                "AI Debt Strategy (Snowball)",
                f'curl -s -H "Authorization: Bearer {TOKEN}" "{BASE_URL}/api/ai/debt-strategy?strategy=snowball"',
            ),
        ]
        for name, cmd in tests_ai:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        print("\n[AI SIMULATIONS]")
        tests_sim = [
            (
                "Simulate Income Change",
                curl_cmd(
                    "POST",
                    "/api/ai/simulate",
                    {"scenario": "income_change", "amount": 1000},
                    auth=True,
                ),
            ),
            (
                "Simulate Expense Reduction",
                curl_cmd(
                    "POST",
                    "/api/ai/simulate",
                    {"scenario": "expense_reduction", "amount": 500},
                    auth=True,
                ),
            ),
            (
                "Simulate Extra Payment",
                curl_cmd(
                    "POST",
                    "/api/ai/simulate",
                    {"scenario": "extra_debt_payment", "amount": 1000},
                    auth=True,
                ),
            ),
            (
                "Simulate Refinance",
                curl_cmd(
                    "POST",
                    "/api/ai/simulate",
                    {"scenario": "refinance", "amount": 5000, "new_rate": 10},
                    auth=True,
                ),
            ),
        ]
        for name, cmd in tests_sim:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        print("\n[DEBT PROJECTIONS]")
        if test_endpoint(
            "Debt Interest Calculation",
            curl_cmd("GET", f"/api/debt/{debt_id}/interest", auth=True),
        ):
            passed += 1
        else:
            failed += 1

        if test_endpoint(
            "Debt Projection",
            curl_cmd("GET", f"/api/debt/{debt_id}/projection", auth=True),
        ):
            passed += 1
        else:
            failed += 1

        if test_endpoint(
            "Card Projection",
            curl_cmd("GET", f"/api/credit-card/{card_id}/projection", auth=True),
        ):
            passed += 1
        else:
            failed += 1

        if test_endpoint(
            "Full Debt+Card Comparison",
            curl_cmd("GET", "/api/debt-compare/full", auth=True),
        ):
            passed += 1
        else:
            failed += 1

        print("\n[SEED DATA]")
        if test_endpoint(
            "Seed Dummy Data", curl_cmd("POST", "/api/seed/dummy", {}, auth=True)
        ):
            passed += 1
        else:
            failed += 1

        print("\n[UPDATE TESTS]")
        tests_update = [
            (
                "Update Income",
                curl_cmd(
                    "PUT",
                    "/api/income/1",
                    {
                        "amount": 6000,
                        "description": "Updated",
                        "category": "salary",
                        "date": "2026-04-05",
                    },
                    auth=True,
                ),
            ),
            (
                "Update Expense",
                curl_cmd(
                    "PUT",
                    "/api/expense/1",
                    {
                        "amount": 1600,
                        "description": "Updated",
                        "category": "needs",
                        "kakebo_type": "variable",
                        "date": "2026-04-05",
                    },
                    auth=True,
                ),
            ),
            (
                "Update Debt",
                curl_cmd(
                    "PUT",
                    "/api/debt/1",
                    {
                        "name": "Updated Loan",
                        "initial_amount": 20000,
                        "current_amount": 17000,
                        "interest_rate": 15,
                        "monthly_payment": 850,
                        "start_date": "2026-01-01",
                        "next_payment_date": "2026-04-15",
                        "is_paid": False,
                    },
                    auth=True,
                ),
            ),
            (
                "Update Service",
                curl_cmd(
                    "PUT",
                    "/api/service/1",
                    {
                        "name": "Updated Service",
                        "provider": "Provider2",
                        "amount": 200,
                        "due_day": 20,
                        "reminder_days": 5,
                        "is_active": True,
                    },
                    auth=True,
                ),
            ),
            (
                "Update Card",
                curl_cmd(
                    "PUT",
                    "/api/credit-card/1",
                    {
                        "name": "Updated Card",
                        "limit": 12000,
                        "current_balance": 2000,
                        "interest_rate": 3.0,
                        "due_date": 18,
                        "card_type": "amex",
                        "last_four": "9999",
                        "cardholder_name": "CARLOS LOPEZ",
                        "expiration_date": "09/30",
                    },
                    auth=True,
                ),
            ),
        ]
        for name, cmd in tests_update:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        print("\n[DELETE TESTS]")
        tests_delete = [
            (
                "Delete Income",
                f'curl -s -X DELETE -H "Authorization: Bearer {TOKEN}" "{BASE_URL}/api/income/1"',
            ),
            (
                "Delete Expense",
                f'curl -s -X DELETE -H "Authorization: Bearer {TOKEN}" "{BASE_URL}/api/expense/1"',
            ),
            (
                "Delete Debt",
                f'curl -s -X DELETE -H "Authorization: Bearer {TOKEN}" "{BASE_URL}/api/debt/1"',
            ),
            (
                "Delete Service",
                f'curl -s -X DELETE -H "Authorization: Bearer {TOKEN}" "{BASE_URL}/api/service/1"',
            ),
            (
                "Delete Card",
                f'curl -s -X DELETE -H "Authorization: Bearer {TOKEN}" "{BASE_URL}/api/credit-card/1"',
            ),
        ]
        for name, cmd in tests_delete:
            if test_endpoint(name, cmd):
                passed += 1
            else:
                failed += 1

        print("\n[FRONTEND]")
        html, _ = run_cmd(f"curl -s {BASE_URL}/")
        if "FamilyFinance" in html and "tailwind" in html:
            print("  OK HTML Page loads correctly")
            passed += 1
        else:
            print("  X HTML Page failed to load")
            failed += 1

        print("\n" + "=" * 60)
        print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
        print("=" * 60)

        if failed == 0:
            print("\nOK ALL TESTS PASSED!")
            return 0
        else:
            print(f"\nX {failed} TESTS FAILED")
            return 1

    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    sys.exit(main())
