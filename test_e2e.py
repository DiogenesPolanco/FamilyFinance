#!/usr/bin/env python3
import subprocess
import time
import sys
import os
import json

BASE_URL = "http://localhost:8000"


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


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
    out, _ = run_cmd(f'curl -s {BASE_URL}{api_path}')
    try:
        data = json.loads(out) if out else []
        if data and isinstance(data, list):
            return str(data[0].get('id', 1))
    except:
        pass
    return "1"


def main():
    print("=" * 60)
    print("FamilyFinance E2E Tests - Complete API Coverage")
    print("=" * 60 + "\n")

    os.chdir("/home/sinope/Documents/opencodeprojects/family-finance")

    print("[1] Resetting database...")
    run_cmd("rm -f family_finance.db")

    print("[2] Starting server...")
    server = subprocess.Popen(
        ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)

    try:
        passed = 0
        failed = 0

        print("\n[AUTH]")
        tests_auth = [
            ("Auth Status", f'curl -s {BASE_URL}/api/auth/status'),
            ("Setup User", f'curl -s -X POST {BASE_URL}/api/setup -H "Content-Type: application/x-www-form-urlencoded" -d "password=test123"'),
            ("Login", f'curl -s -X POST {BASE_URL}/api/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "password=test123"'),
        ]
        for name, cmd in tests_auth:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        print("\n[INCOME]")
        tests_income = [
            ("Create Income Salary", f'curl -s -X POST {BASE_URL}/api/income -H "Content-Type: application/json" -d \'{{"amount":5000,"description":"Test Salary","category":"salary","date":"2026-04-05"}}\''),
            ("Create Income Freelance", f'curl -s -X POST {BASE_URL}/api/income -H "Content-Type: application/json" -d \'{{"amount":1500,"description":"Freelance","category":"freelance","date":"2026-04-10"}}\''),
            ("Get All Incomes", f'curl -s {BASE_URL}/api/income'),
        ]
        for name, cmd in tests_income:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        print("\n[EXPENSES]")
        tests_expense = [
            ("Create Expense Needs", f'curl -s -X POST {BASE_URL}/api/expense -H "Content-Type: application/json" -d \'{{"amount":1500,"description":"Groceries","category":"needs","kakebo_type":"variable","date":"2026-04-05"}}\''),
            ("Create Expense Wants", f'curl -s -X POST {BASE_URL}/api/expense -H "Content-Type: application/json" -d \'{{"amount":500,"description":"Entertainment","category":"wants","kakebo_type":"variable","date":"2026-04-07"}}\''),
            ("Create Expense Culture", f'curl -s -X POST {BASE_URL}/api/expense -H "Content-Type: application/json" -d \'{{"amount":200,"description":"Cinema","category":"culture","kakebo_type":"discretionary","date":"2026-04-10"}}\''),
            ("Create Expense Unexpected", f'curl -s -X POST {BASE_URL}/api/expense -H "Content-Type: application/json" -d \'{{"amount":300,"description":"Repair","category":"unexpected","kakebo_type":"emergency","date":"2026-04-12"}}\''),
            ("Get All Expenses", f'curl -s {BASE_URL}/api/expense'),
            ("Kakebo Summary", f'curl -s {BASE_URL}/api/expense/kakebo'),
        ]
        for name, cmd in tests_expense:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        print("\n[DEBTS]")
        tests_debt = [
            ("Create Debt Personal Loan", f'curl -s -X POST {BASE_URL}/api/debt -H "Content-Type: application/json" -d \'{{"name":"Prestamo Personal","initial_amount":20000,"current_amount":18000,"interest_rate":18,"monthly_payment":800,"start_date":"2026-01-01","next_payment_date":"2026-04-15","is_paid":false}}\''),
            ("Create Debt Car Loan", f'curl -s -X POST {BASE_URL}/api/debt -H "Content-Type: application/json" -d \'{{"name":"Prestamo Auto","initial_amount":50000,"current_amount":45000,"interest_rate":12,"monthly_payment":1500,"start_date":"2026-01-01","next_payment_date":"2026-04-20","is_paid":false}}\''),
            ("Get All Debts", f'curl -s {BASE_URL}/api/debt'),
            ("Get Debt Comparison", f'curl -s {BASE_URL}/api/debt/comparison'),
        ]
        for name, cmd in tests_debt:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        debt_id = get_first_id("/api/debt")
        if test_endpoint("Pay Debt", f'curl -s -X POST {BASE_URL}/api/debt/{debt_id}/pay -H "Content-Type: application/json" -d \'{{"amount":500}}\''):
            passed += 1
        else:
            failed += 1

        print("\n[CREDIT CARDS]")
        tests_cards = [
            ("Create Credit Card 1", f'curl -s -X POST {BASE_URL}/api/credit-card -H "Content-Type: application/json" -d \'{{"name":"Visa Banco A","limit":10000,"current_balance":2500,"interest_rate":3.5,"due_date":15,"is_active":true}}\''),
            ("Create Credit Card 2", f'curl -s -X POST {BASE_URL}/api/credit-card -H "Content-Type: application/json" -d \'{{"name":"Mastercard Banco B","limit":15000,"current_balance":3000,"interest_rate":2.8,"due_date":20,"is_active":true}}\''),
            ("Get All Cards", f'curl -s {BASE_URL}/api/credit-card'),
            ("Get Card Comparison", f'curl -s {BASE_URL}/api/credit-card/comparison'),
        ]
        for name, cmd in tests_cards:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        card_id = get_first_id("/api/credit-card")
        if test_endpoint("Charge Card", f'curl -s -X POST {BASE_URL}/api/credit-card/{card_id}/charge -H "Content-Type: application/json" -d \'{{"amount":100,"description":"Purchase","date":"2026-04-05"}}\''):
            passed += 1
        else:
            failed += 1

        print("\n[HOUSEHOLD SERVICES]")
        tests_services = [
            ("Create Service Electricity", f'curl -s -X POST {BASE_URL}/api/service -H "Content-Type: application/json" -d \'{{"name":"Electricidad","provider":"EDESUR","amount":150,"due_day":10,"reminder_days":3,"is_active":true}}\''),
            ("Create Service Internet", f'curl -s -X POST {BASE_URL}/api/service -H "Content-Type: application/json" -d \'{{"name":"Internet","provider":"Claro","amount":50,"due_day":15,"reminder_days":3,"is_active":true}}\''),
            ("Create Service Water", f'curl -s -X POST {BASE_URL}/api/service -H "Content-Type: application/json" -d \'{{"name":"Agua","provider":"CAASD","amount":30,"due_day":20,"reminder_days":3,"is_active":true}}\''),
            ("Get All Services", f'curl -s {BASE_URL}/api/service'),
        ]
        for name, cmd in tests_services:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        service_id = get_first_id("/api/service")
        if test_endpoint("Pay Service", f'curl -s -X POST {BASE_URL}/api/service/{service_id}/pay -H "Content-Type: application/json" -d \'{{"amount":150}}\''):
            passed += 1
        else:
            failed += 1

        print("\n[DASHBOARD]")
        tests_dashboard = [
            ("Dashboard Summary", f'curl -s {BASE_URL}/api/dashboard/summary'),
            ("Upcoming Payments", f'curl -s {BASE_URL}/api/dashboard/upcoming'),
        ]
        for name, cmd in tests_dashboard:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        print("\n[REPORTS]")
        tests_reports = [
            ("Monthly Report", f'curl -s {BASE_URL}/api/reports/monthly'),
            ("Quincenal Report", f'curl -s {BASE_URL}/api/reports/quincenal'),
            ("Quarterly Report", f'curl -s {BASE_URL}/api/reports/quarterly'),
            ("Yearly Report", f'curl -s {BASE_URL}/api/reports/yearly'),
            ("Kakebo Report", f'curl -s {BASE_URL}/api/reports/kakebo'),
            ("Debts Report", f'curl -s {BASE_URL}/api/reports/debts'),
        ]
        for name, cmd in tests_reports:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        print("\n[BUDGET]")
        tests_budget = [
            ("Get Budget", f'curl -s {BASE_URL}/api/budget'),
            ("Get Budget Allocation", f'curl -s {BASE_URL}/api/budget/allocation'),
        ]
        for name, cmd in tests_budget:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        print("\n[AI ENGINE]")
        tests_ai = [
            ("AI Recommendations", f'curl -s {BASE_URL}/api/ai/recommendations'),
            ("AI Insights", f'curl -s {BASE_URL}/api/ai/insights'),
            ("AI Anomalies", f'curl -s {BASE_URL}/api/ai/anomalies'),
            ("AI Forecast", f'curl -s {BASE_URL}/api/ai/forecast'),
            ("AI Debt Strategy (Avalanche)", f'curl -s "{BASE_URL}/api/ai/debt-strategy?strategy=avalanche"'),
            ("AI Debt Strategy (Snowball)", f'curl -s "{BASE_URL}/api/ai/debt-strategy?strategy=snowball"'),
        ]
        for name, cmd in tests_ai:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        print("\n[AI SIMULATIONS]")
        tests_sim = [
            ("Simulate Income Change", f'curl -s -X POST {BASE_URL}/api/ai/simulate -H "Content-Type: application/json" -d \'{{"scenario":"income_change","amount":1000}}\''),
            ("Simulate Expense Reduction", f'curl -s -X POST {BASE_URL}/api/ai/simulate -H "Content-Type: application/json" -d \'{{"scenario":"expense_reduction","amount":500}}\''),
            ("Simulate Extra Payment", f'curl -s -X POST {BASE_URL}/api/ai/simulate -H "Content-Type: application/json" -d \'{{"scenario":"extra_debt_payment","amount":1000}}\''),
            ("Simulate Refinance", f'curl -s -X POST {BASE_URL}/api/ai/simulate -H "Content-Type: application/json" -d \'{{"scenario":"refinance","amount":5000,"new_rate":10}}\''),
        ]
        for name, cmd in tests_sim:
            if test_endpoint(name, cmd): passed += 1
            else: failed += 1

        print("\n[DEBT PROJECTIONS]")
        if test_endpoint("Debt Interest Calculation", f'curl -s {BASE_URL}/api/debt/{debt_id}/interest'):
            passed += 1
        else:
            failed += 1

        if test_endpoint("Debt Projection", f'curl -s {BASE_URL}/api/debt/{debt_id}/projection'):
            passed += 1
        else:
            failed += 1

        if test_endpoint("Card Projection", f'curl -s {BASE_URL}/api/credit-card/{card_id}/projection'):
            passed += 1
        else:
            failed += 1

        if test_endpoint("Full Debt+Card Comparison", f'curl -s {BASE_URL}/api/debt-compare/full'):
            passed += 1
        else:
            failed += 1

        print("\n[SEED DATA]")
        if test_endpoint("Seed Dummy Data", f'curl -s -X POST {BASE_URL}/api/seed/dummy'):
            passed += 1
        else:
            failed += 1

        print("\n[FRONTEND]")
        html, _ = run_cmd(f'curl -s {BASE_URL}/')
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
