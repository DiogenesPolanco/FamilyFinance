#!/bin/bash
# FamilyFinance E2E Tests
# Usage: ./e2e-tests.sh

set -e

BASE_URL="http://localhost:8000"
PASS="test123"

echo "=========================================="
echo "FamilyFinance E2E Tests"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((pass_count++))
}

fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((fail_count++))
}

# Reset database
echo -e "\n${YELLOW}Resetting database...${NC}"
rm -f family_finance.db
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
sleep 3

# Check server is running
echo -e "\n${YELLOW}Checking server status...${NC}"
if curl -s --connect-timeout 5 "$BASE_URL/api/auth/status" > /dev/null; then
    pass "Server is running"
else
    fail "Server is not running"
    exit 1
fi

# Test 1: Auth Status (no user)
echo -e "\n${YELLOW}Test 1: Auth Status (no user)${NC}"
result=$(curl -s "$BASE_URL/api/auth/status")
if echo "$result" | grep -q '"is_setup":false'; then
    pass "Auth status returns is_setup: false"
else
    fail "Auth status should return is_setup: false"
fi

# Test 2: Setup User
echo -e "\n${YELLOW}Test 2: Setup User${NC}"
result=$(curl -s -X POST "$BASE_URL/api/setup" -d "password=$PASS")
if echo "$result" | grep -q '"message":"User created successfully"'; then
    pass "User created successfully"
else
    fail "Failed to create user: $result"
fi

# Test 3: Auth Status (user exists)
echo -e "\n${YELLOW}Test 3: Auth Status (user exists)${NC}"
result=$(curl -s "$BASE_URL/api/auth/status")
if echo "$result" | grep -q '"is_setup":true'; then
    pass "Auth status returns is_setup: true"
else
    fail "Auth status should return is_setup: true"
fi

# Test 4: Login with correct password
echo -e "\n${YELLOW}Test 4: Login with correct password${NC}"
result=$(curl -s -X POST "$BASE_URL/api/auth/login" -d "password=$PASS")
if echo "$result" | grep -q '"access_token"'; then
    pass "Login successful, token received"
    TOKEN=$(echo "$result" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
else
    fail "Login failed: $result"
    TOKEN=""
fi

# Test 5: Login with wrong password
echo -e "\n${YELLOW}Test 5: Login with wrong password${NC}"
result=$(curl -s -X POST "$BASE_URL/api/auth/login" -d "password=wrongpass")
if echo "$result" | grep -q '"detail"'; then
    pass "Login with wrong password returns error"
else
    fail "Login with wrong password should return error"
fi

# Test 6: Create Income
echo -e "\n${YELLOW}Test 6: Create Income${NC}"
result=$(curl -s -X POST "$BASE_URL/api/income" \
    -H "Content-Type: application/json" \
    -d '{"amount":5000,"description":"Test salary","category":"salary","date":"2026-04-05"}')
if echo "$result" | grep -q '"amount":5000'; then
    pass "Income created successfully"
else
    fail "Failed to create income: $result"
fi

# Test 7: Get Incomes
echo -e "\n${YELLOW}Test 7: Get Incomes${NC}"
result=$(curl -s "$BASE_URL/api/income")
if echo "$result" | grep -q '"category":"salary"'; then
    pass "Income list retrieved"
else
    fail "Failed to get income list: $result"
fi

# Test 8: Create Expense
echo -e "\n${YELLOW}Test 8: Create Expense${NC}"
result=$(curl -s -X POST "$BASE_URL/api/expense" \
    -H "Content-Type: application/json" \
    -d '{"amount":1500,"description":"Test expense","category":"needs","kakebo_type":"variable","date":"2026-04-05"}')
if echo "$result" | grep -q '"amount":1500'; then
    pass "Expense created successfully"
else
    fail "Failed to create expense: $result"
fi

# Test 9: Get Expenses
echo -e "\n${YELLOW}Test 9: Get Expenses${NC}"
result=$(curl -s "$BASE_URL/api/expense")
if echo "$result" | grep -q '"category":"needs"'; then
    pass "Expense list retrieved"
else
    fail "Failed to get expense list: $result"
fi

# Test 10: Kakebo Summary
echo -e "\n${YELLOW}Test 10: Kakebo Summary${NC}"
result=$(curl -s "$BASE_URL/api/expense/kakebo")
if echo "$result" | grep -q '"by_category"'; then
    pass "Kakebo summary retrieved"
else
    fail "Failed to get kakebo summary: $result"
fi

# Test 11: Create Debt
echo -e "\n${YELLOW}Test 11: Create Debt${NC}"
result=$(curl -s -X POST "$BASE_URL/api/debt" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Loan","initial_amount":10000,"current_amount":10000,"interest_rate":12,"monthly_payment":500,"start_date":"2026-01-01","next_payment_date":"2026-04-15"}')
if echo "$result" | grep -q '"name":"Test Loan"'; then
    pass "Debt created successfully"
else
    fail "Failed to create debt: $result"
fi

# Test 12: Get Debts
echo -e "\n${YELLOW}Test 12: Get Debts${NC}"
result=$(curl -s "$BASE_URL/api/debt")
if echo "$result" | grep -q '"Test Loan"'; then
    pass "Debt list retrieved"
else
    fail "Failed to get debt list: $result"
fi

# Test 13: Create Credit Card
echo -e "\n${YELLOW}Test 13: Create Credit Card${NC}"
result=$(curl -s -X POST "$BASE_URL/api/credit-card" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Card","limit":10000,"current_balance":0,"interest_rate":3.5,"due_date":15}')
if echo "$result" | grep -q '"name":"Test Card"'; then
    pass "Credit card created successfully"
else
    fail "Failed to create credit card: $result"
fi

# Test 14: Get Credit Cards
echo -e "\n${YELLOW}Test 14: Get Credit Cards${NC}"
result=$(curl -s "$BASE_URL/api/credit-card")
if echo "$result" | grep -q '"Test Card"'; then
    pass "Credit card list retrieved"
else
    fail "Failed to get credit card list: $result"
fi

# Test 15: Create Service
echo -e "\n${YELLOW}Test 15: Create Service${NC}"
result=$(curl -s -X POST "$BASE_URL/api/service" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Service","provider":"Test Provider","amount":100,"due_day":15,"reminder_days":3}')
if echo "$result" | grep -q '"name":"Test Service"'; then
    pass "Service created successfully"
else
    fail "Failed to create service: $result"
fi

# Test 16: Get Services
echo -e "\n${YELLOW}Test 16: Get Services${NC}"
result=$(curl -s "$BASE_URL/api/service")
if echo "$result" | grep -q '"Test Service"'; then
    pass "Service list retrieved"
else
    fail "Failed to get service list: $result"
fi

# Test 17: Dashboard Summary
echo -e "\n${YELLOW}Test 17: Dashboard Summary${NC}"
result=$(curl -s "$BASE_URL/api/dashboard/summary")
if echo "$result" | grep -q '"balance"'; then
    pass "Dashboard summary retrieved"
else
    fail "Failed to get dashboard summary: $result"
fi

# Test 18: Upcoming Payments
echo -e "\n${YELLOW}Test 18: Upcoming Payments${NC}"
result=$(curl -s "$BASE_URL/api/dashboard/upcoming")
if echo "$result" | grep -q '\[{"type"'; then
    pass "Upcoming payments retrieved"
else
    fail "Failed to get upcoming payments: $result"
fi

# Test 19: Monthly Report
echo -e "\n${YELLOW}Test 19: Monthly Report${NC}"
result=$(curl -s "$BASE_URL/api/reports/monthly")
if echo "$result" | grep -q '"total_income"'; then
    pass "Monthly report retrieved"
else
    fail "Failed to get monthly report: $result"
fi

# Test 20: Budget
echo -e "\n${YELLOW}Test 20: Budget${NC}"
result=$(curl -s "$BASE_URL/api/budget")
if echo "$result" | grep -q '"budgets"'; then
    pass "Budget retrieved"
else
    fail "Failed to get budget: $result"
fi

# Test 21: AI Recommendations
echo -e "\n${YELLOW}Test 21: AI Recommendations${NC}"
result=$(curl -s "$BASE_URL/api/ai/recommendations")
if echo "$result" | grep -q '\['; then
    pass "AI recommendations retrieved"
else
    fail "Failed to get AI recommendations: $result"
fi

# Test 22: AI Insights
echo -e "\n${YELLOW}Test 22: AI Insights${NC}"
result=$(curl -s "$BASE_URL/api/ai/insights")
if echo "$result" | grep -q '{'; then
    pass "AI insights retrieved"
else
    fail "Failed to get AI insights: $result"
fi

# Test 23: Seed Dummy Data
echo -e "\n${YELLOW}Test 23: Seed Dummy Data${NC}"
result=$(curl -s -X POST "$BASE_URL/api/seed/dummy")
if echo "$result" | grep -q '"Datos dummy cargados"'; then
    pass "Dummy data seeded successfully"
else
    fail "Failed to seed dummy data: $result"
fi

# Test 24: HTML Page Loads
echo -e "\n${YELLOW}Test 24: HTML Page Loads${NC}"
result=$(curl -s "$BASE_URL/")
if echo "$result" | grep -q '<!DOCTYPE html>'; then
    pass "HTML page loads correctly"
else
    fail "HTML page failed to load"
fi

# Test 25: Pay Service
echo -e "\n${YELLOW}Test 25: Pay Service${NC}"
result=$(curl -s -X POST "$BASE_URL/api/service/1/pay")
if echo "$result" | grep -q '"id"'; then
    pass "Service payment successful"
else
    fail "Failed to pay service: $result"
fi

# Test 26: Debt Comparison
echo -e "\n${YELLOW}Test 26: Debt Comparison${NC}"
result=$(curl -s "$BASE_URL/api/debt/comparison")
if echo "$result" | grep -q '\[{'; then
    pass "Debt comparison retrieved"
else
    fail "Failed to get debt comparison: $result"
fi

# Test 27: Debt Strategy
echo -e "\n${YELLOW}Test 27: Debt Strategy${NC}"
result=$(curl -s "$BASE_URL/api/ai/debt-strategy?strategy=avalanche")
if echo "$result" | grep -q '"steps"'; then
    pass "Debt strategy retrieved"
else
    fail "Failed to get debt strategy: $result"
fi

# Test 28: Delete Income
echo -e "\n${YELLOW}Test 28: Delete Income${NC}"
result=$(curl -s -X DELETE "$BASE_URL/api/income/1")
if echo "$result" | grep -q '"message"'; then
    pass "Income deleted successfully"
else
    fail "Failed to delete income: $result"
fi

# Test 29: Delete Expense
echo -e "\n${YELLOW}Test 29: Delete Expense${NC}"
result=$(curl -s -X DELETE "$BASE_URL/api/expense/1")
if echo "$result" | grep -q '"message"'; then
    pass "Expense deleted successfully"
else
    fail "Failed to delete expense: $result"
fi

# Test 30: Update Debt
echo -e "\n${YELLOW}Test 30: Update Debt${NC}"
result=$(curl -s -X PUT "$BASE_URL/api/debt/1" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Loan Updated","initial_amount":10000,"current_amount":9500,"interest_rate":12,"monthly_payment":500,"start_date":"2026-01-01","next_payment_date":"2026-04-15"}')
if echo "$result" | grep -q '"current_amount":9500'; then
    pass "Debt updated successfully"
else
    fail "Failed to update debt: $result"
fi

# Summary
echo -e "\n=========================================="
echo -e "Test Summary"
echo -e "=========================================="
echo -e "${GREEN}Passed: $pass_count${NC}"
echo -e "${RED}Failed: $fail_count${NC}"
echo -e "Total: $((pass_count + fail_count))"

if [ $fail_count -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
fi
