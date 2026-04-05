#!/usr/bin/env python3
import subprocess
import time
import sys
import os

BASE_URL = "http://localhost:8000"


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def main():
    print("=== FamilyFinance E2E Tests ===\n")

    os.chdir("/home/sinope/Documents/opencodeprojects/family-finance")

    print("1. Starting server...")
    run_cmd("rm -f family_finance.db")

    server = subprocess.Popen(
        ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(3)

    try:
        print("2. Testing API endpoints...\n")

        tests = [
            ("Auth Status", "curl -s http://localhost:8000/api/auth/status"),
            (
                "Setup User",
                'curl -s -X POST http://localhost:8000/api/setup -H "Content-Type: application/x-www-form-urlencoded" -d "password=test123"',
            ),
            (
                "Auth Status (user exists)",
                "curl -s http://localhost:8000/api/auth/status",
            ),
            (
                "Login",
                'curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "password=test123"',
            ),
            (
                "Create Income",
                'curl -s -X POST http://localhost:8000/api/income -H "Content-Type: application/json" -d \'{"amount":5000,"description":"Test","category":"salary","date":"2026-04-05"}\'',
            ),
            ("Get Incomes", "curl -s http://localhost:8000/api/income"),
            (
                "Create Expense",
                'curl -s -X POST http://localhost:8000/api/expense -H "Content-Type: application/json" -d \'{"amount":1500,"description":"Test","category":"needs","kakebo_type":"variable","date":"2026-04-05"}\'',
            ),
            ("Get Expenses", "curl -s http://localhost:8000/api/expense"),
            ("Kakebo Summary", "curl -s http://localhost:8000/api/expense/kakebo"),
            (
                "Create Debt",
                'curl -s -X POST http://localhost:8000/api/debt -H "Content-Type: application/json" -d \'{"name":"Test Loan","initial_amount":10000,"current_amount":10000,"interest_rate":12,"monthly_payment":500,"start_date":"2026-01-01","next_payment_date":"2026-04-15"}\'',
            ),
            ("Get Debts", "curl -s http://localhost:8000/api/debt"),
            (
                "Create Card",
                'curl -s -X POST http://localhost:8000/api/credit-card -H "Content-Type: application/json" -d \'{"name":"Test Card","limit":10000,"current_balance":0,"interest_rate":3.5,"due_date":15}\'',
            ),
            ("Get Cards", "curl -s http://localhost:8000/api/credit-card"),
            (
                "Create Service",
                'curl -s -X POST http://localhost:8000/api/service -H "Content-Type: application/json" -d \'{"name":"Test Service","provider":"Provider","amount":100,"due_day":15,"reminder_days":3}\'',
            ),
            ("Get Services", "curl -s http://localhost:8000/api/service"),
            (
                "Dashboard Summary",
                "curl -s http://localhost:8000/api/dashboard/summary",
            ),
            (
                "Upcoming Payments",
                "curl -s http://localhost:8000/api/dashboard/upcoming",
            ),
            ("Monthly Report", "curl -s http://localhost:8000/api/reports/monthly"),
            ("Budget", "curl -s http://localhost:8000/api/budget"),
            (
                "AI Recommendations",
                "curl -s http://localhost:8000/api/ai/recommendations",
            ),
            ("AI Insights", "curl -s http://localhost:8000/api/ai/insights"),
            ("Seed Dummy", "curl -s -X POST http://localhost:8000/api/seed/dummy"),
            ("HTML Page", "curl -s http://localhost:8000/ | head -c 200"),
        ]

        passed = 0
        failed = 0

        for i, (name, cmd) in enumerate(tests, 1):
            out, code = run_cmd(cmd)

            if "Error" in out and "error" not in name.lower():
                print(f"✗ Test {i}: {name} - FAILED")
                failed += 1
            elif code == 0 and out:
                print(f"✓ Test {i}: {name} - PASSED")
                passed += 1
            else:
                print(f"✗ Test {i}: {name} - FAILED (no output)")
                failed += 1

        print(f"\n=== Results ===")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Total: {passed + failed}")

        if failed == 0:
            print("\n✓ ALL TESTS PASSED!")
            return 0
        else:
            print(f"\n✗ {failed} TESTS FAILED")
            return 1

    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    sys.exit(main())
