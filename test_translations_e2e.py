#!/usr/bin/env python3
"""E2E test for Spanish translations in FamilyFinance"""

import http.server
import threading
import time
import os
import sys

# Start server
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/static")
server = http.server.HTTPServer(
    ("localhost", 8765), http.server.SimpleHTTPRequestHandler
)
t = threading.Thread(target=server.serve_forever)
t.daemon = True
t.start()
time.sleep(1)

# Read the HTML file
html_file = os.path.dirname(os.path.abspath(__file__)) + "/static/index.html"
with open(html_file, "r") as f:
    html = f.read()

print("=" * 60)
print("FamilyFinance E2E Translation Tests")
print("=" * 60)

tests_passed = 0
tests_failed = 0


def test(name, condition):
    global tests_passed, tests_failed
    if condition:
        print(f"  ✅ {name}")
        tests_passed += 1
    else:
        print(f"  ❌ {name}")
        tests_failed += 1


# Test 1: Verify translations.es block exists
print("\n1. Translation objects exist:")
test("translations.es block exists", "es: {" in html)
test("translations.en block exists", "en: {" in html)
test("bilingualTranslations exists", "const bilingualTranslations" in html)

# Test 2: Verify key Spanish translations exist in es block
print("\n2. Key Spanish translations in es:")
es_keys = {
    "new_card": "Nueva Tarjeta",
    "new_service": "Nuevo Servicio",
    "add_income": "Agregar Ingreso",
    "expenses": "Gastos",
    "income": "Ingresos",
    "debt": "Deuda",
    "save": "Guardar",
    "loading": "Cargando",
    "password": "Contraseña",
    "enter": "Entrar",
    "summary": "Resumen",
    "reports": "Reportes",
    "budgets": "Presupuestos",
    "ai_assistant": "Asistente IA",
    "kakebo": "Kakebo",
    "pay_immediately": "Pagar de Inmediato",
    "pay_overdue": "Pagar Vencido",
    "pay_early": "Pagar Adelantado",
}

for key, expected in es_keys.items():
    # Check in translations.es block (between 'es: {' and 'en: {')
    es_start = html.find("es: {")
    en_start = html.find("en: {")
    es_block = html[es_start:en_start]
    test(f"  {key} = '{expected}'", expected in es_block)

# Test 3: Verify English translations exist in en block
print("\n3. Key English translations in en:")
en_keys = {
    "new_card": "New Card",
    "new_service": "New Service",
    "add_income": "Add Income",
    "expenses": "Expenses",
    "income": "Income",
    "debt": "Debt",
    "save": "Save",
    "loading": "Loading",
    "password": "Password",
    "enter": "Enter",
    "summary": "Summary",
    "reports": "Reports",
    "budgets": "Budgets",
    "ai_assistant": "AI Assistant",
    "kakebo": "Kakebo",
    "pay_immediately": "Pay Immediately",
    "pay_overdue": "Pay Overdue",
    "pay_early": "Pay Early",
}

en_start = html.find("en: {")
en_block = html[en_start : en_start + 10000]  # Get a chunk of en block

for key, expected in en_keys.items():
    test(f"  {key} = '{expected}'", expected in en_block)

# Test 4: Verify data-i18n attributes exist in HTML
print("\n4. data-i18n attributes in HTML:")
data_i18n_checks = [
    'data-i18n="new_card"',
    'data-i18n="new_service"',
    'data-i18n="add_income"',
    'data-i18n="expenses"',
    'data-i18n="income"',
    'data-i18n="debt"',
    'data-i18n="save"',
    'data-i18n="loading"',
    'data-i18n="password"',
    'data-i18n="enter"',
    'data-i18n="summary"',
    'data-i18n="reports"',
    'data-i18n="budgets"',
    'data-i18n="ai_assistant"',
    'data-i18n="kakebo"',
]

for check in data_i18n_checks:
    test(f"  {check}", check in html)

# Test 5: Verify t() function exists and uses currentLang
print("\n5. t() function implementation:")
test("  t() function exists", "function t(key)" in html)
test("  currentLang default is 'es'", "localStorage.getItem('ff-lang') || 'es'" in html)
test("  bilingualTranslations checked first", "bilingualTranslations[key]" in html)
test("  translations.es fallback", "translations.es?.[key]" in html)

# Test 6: Verify applyTranslations is called on init
print("\n6. Translation initialization:")
test("  applyTranslations() in init()", "applyTranslations();" in html)

# Test 7: Verify no hardcoded Spanish in dynamic content
print("\n7. No hardcoded Spanish in dynamic content:")
import re

# Check for textContent = 'Spanish'
textcontent_matches = re.findall(r"textContent\s*=\s*'([^']*[áéíóúñ][^']*)'", html)
test("  No hardcoded textContent with Spanish", len(textcontent_matches) == 0)

# Check for innerHTML = 'Spanish' (excluding translation definitions)
innerhtml_matches = re.findall(r"innerHTML\s*=\s*'([^']*[áéíóúñ][^']*)'", html)
test("  No hardcoded innerHTML with Spanish", len(innerhtml_matches) == 0)

# Test 8: Verify bilingualTranslations has both ES and EN
print("\n8. Bilingual translations have both languages:")
bilingual_keys = re.findall(r"(\w+):\s*\{\s*es:\s*'([^']*)',\s*en:\s*'([^']*)'", html)
test(f"  Found {len(bilingual_keys)} bilingual translations", len(bilingual_keys) > 50)

# Check a few specific ones
for key, es_val, en_val in bilingual_keys[:5]:
    test(f"  {key}: es='{es_val}', en='{en_val}'", bool(es_val) and bool(en_val))

# Summary
print("\n" + "=" * 60)
print(f"Results: {tests_passed} passed, {tests_failed} failed")
print("=" * 60)

sys.exit(0 if tests_failed == 0 else 1)
