#!/usr/bin/env node
/**
 * E2E Translation Test for FamilyFinance
 * Simulates the actual t() function and verifies all translations work
 */
const fs = require('fs');
const path = require('path');

const htmlFile = path.join(__dirname, 'static', 'index.html');
const html = fs.readFileSync(htmlFile, 'utf8');

const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  console.log('❌ No <script> found');
  process.exit(1);
}

const script = scriptMatch[1];

function extractTranslations() {
  const translations = { es: {}, en: {} };
  const bilingualTranslations = {};

  const bibStart = script.indexOf('const bilingualTranslations = {');
  const transStart = script.indexOf('const translations = {');

  if (bibStart > -1) {
    const bibEnd = script.indexOf('};', bibStart + 30);
    const bibBlock = script.substring(bibStart + 35, bibEnd);
    const bibLines = bibBlock.split('\n');
    let currentKey = null;
    let esVal = '';
    let enVal = '';

    bibLines.forEach(line => {
      const keyMatch = line.match(/^\s+([a-z_][a-z0-9_]*):\s*\{\s*es:\s*'([^']*)',\s*en:\s*'([^']*)'\s*\}/);
      if (keyMatch) {
        bilingualTranslations[keyMatch[1]] = { es: keyMatch[2], en: keyMatch[3] };
      }
    });
  }

  if (transStart > -1) {
    const esBlockMatch = script.substring(transStart).match(/es:\s*\{([\s\S]*?)\n\s*\},\s*\n\s*en:\s*\{/);
    const enBlockMatch = script.substring(transStart).match(/en:\s*\{([\s\S]*?)\n\s*\},\s*\n\s*es:\s*\{/);

    if (esBlockMatch) {
      const esLines = esBlockMatch[1].split('\n');
      esLines.forEach(line => {
        const m = line.match(/^\s+([a-z_][a-z0-9_]*):\s*'([^']*)'/);
        if (m) translations.es[m[1]] = m[2];
      });
    }

    if (enBlockMatch) {
      const enLines = enBlockMatch[1].split('\n');
      enLines.forEach(line => {
        const m = line.match(/^\s+([a-z_][a-z0-9_]*):\s*'([^']*)'/);
        if (m) translations.en[m[1]] = m[2];
      });
    }
  }

  return { translations, bilingualTranslations };
}

const { translations, bilingualTranslations } = extractTranslations();

function t(key, lang = 'es') {
  const b = bilingualTranslations[key];
  if (b && b.es) return b[lang] || b.es || key;
  return translations[lang]?.[key] || translations.es?.[key] || key;
}

let passed = 0;
let failed = 0;

function test(name, condition) {
  if (condition) {
    console.log(`  ✅ ${name}`);
    passed++;
  } else {
    console.log(`  ❌ ${name}`);
    failed++;
  }
}

console.log('='.repeat(60));
console.log('FamilyFinance Translation E2E Tests');
console.log('='.repeat(60));

console.log('\n1. Spanish translations (default language):');
const esChecks = [
  ['new_card', 'Nueva Tarjeta'],
  ['new_service', 'Nuevo Servicio'],
  ['add_income', 'Agregar Ingreso'],
  ['add_expense', 'Agregar Gasto'],
  ['expenses', 'Gastos'],
  ['income', 'Ingresos'],
  ['debt', 'Deuda'],
  ['save', 'Guardar'],
  ['loading', 'Cargando...'],
  ['password', 'Contraseña'],
  ['enter', 'Ingresar'],
  ['summary', 'Resumen'],
  ['reports', 'Reportes'],
  ['budgets', 'Presupuestos'],
  ['ai_assistant', 'Asistente IA'],
  ['kakebo', 'Kakebo'],
  ['pay_immediately', 'Pagar de Inmediato'],
  ['pay_overdue', 'Pagar Vencido'],
  ['pay_early', 'Pagar Adelantado'],
  ['no_income', 'No hay ingresos registrados'],
  ['no_expenses', 'No hay gastos registrados'],
  ['no_debts', 'No hay deudas registradas'],
  ['no_cards', 'No hay tarjetas registradas'],
  ['no_services', 'No hay servicios registrados'],
  ['upcoming_payments', 'Próximos Pagos'],
  ['kakebo_this_month', 'Kakebo - Este Mes'],
  ['needs', 'Necesidades'],
  ['wants', 'Deseos'],
  ['culture', 'Cultura'],
  ['unexpected', 'Inesperado'],
];

esChecks.forEach(([key, expected]) => {
  const actual = t(key, 'es');
  test(`${key} = "${actual}"`, actual === expected);
});

console.log('\n2. English translations:');
const enChecks = [
  ['new_card', 'New Card'],
  ['new_service', 'New Service'],
  ['add_income', 'Add Income'],
  ['add_expense', 'Add Expense'],
  ['expenses', 'Expenses'],
  ['income', 'Income'],
  ['debt', 'Debt'],
  ['save', 'Save'],
  ['loading', 'Loading...'],
  ['password', 'Password'],
  ['enter', 'Enter'],
  ['summary', 'Summary'],
  ['reports', 'Reports'],
  ['budgets', 'Budgets'],
  ['ai_assistant', 'AI Assistant'],
  ['kakebo', 'Kakebo'],
  ['pay_immediately', 'Pay Immediately'],
  ['pay_overdue', 'Pay Overdue'],
  ['pay_early', 'Pay Early'],
  ['no_income', 'No income recorded'],
  ['no_expenses', 'No expenses recorded'],
  ['no_debts', 'No debts recorded'],
  ['no_cards', 'No cards recorded'],
  ['no_services', 'No services recorded'],
  ['upcoming_payments', 'Upcoming Payments'],
  ['kakebo_this_month', 'Kakebo - This Month'],
  ['needs', 'Needs'],
  ['wants', 'Wants'],
  ['culture', 'Culture'],
  ['unexpected', 'Unexpected'],
];

enChecks.forEach(([key, expected]) => {
  const actual = t(key, 'en');
  test(`${key} = "${actual}"`, actual === expected);
});

console.log('\n3. Bilingual translations (both languages):');
const bibChecks = [
  'card_limit_usage',
  'current_balance_label',
  'view_projection_short',
  'amount_label',
  'description_label',
  'category_label',
  'date_label',
  'name_label',
  'initial_amount_label',
  'interest_rate_pct',
  'monthly_payment_label',
  'start_date_label',
  'next_payment_label',
  'limit_label',
  'actual_balance_label',
  'cutoff_day_label',
  'provider_label',
  'monthly_amount_label',
  'payment_day_label',
  'reminder_days_label',
  'save_label',
  'salary_label',
  'freelance_label',
  'investment_label',
  'gift_label',
  'other_income_label',
  'kakebo_category_label',
  'needs_label',
  'wants_label',
  'culture_label',
  'unexpected_label',
  'this_month',
  'view_all_count',
  'no_income_month',
  'no_description',
  'all_income_label',
  'view_current_month',
  'no_expenses_month',
  'all_expenses_label',
  'pay_immediately',
  'pay_overdue',
  'pay_early',
];

bibChecks.forEach(key => {
  const b = bilingualTranslations[key];
  if (b) {
    test(`${key}: es="${b.es}", en="${b.en}"`, !!b.es && !!b.en);
  } else {
    test(`${key}: exists in bilingualTranslations`, false);
  }
});

console.log('\n4. Default language is Spanish:');
const defaultLangMatch = script.match(/localStorage\.getItem\('ff-lang'\)\s*\|\|\s*'es'/);
test("currentLang default is 'es'", !!defaultLangMatch);

console.log('\n5. applyTranslations() is called on init:');
const initMatch = script.includes('async function init()') && script.includes('applyTranslations()');
test('applyTranslations() called in init()', initMatch);

console.log('\n6. data-i18n attributes in HTML:');
const dataI18nCount = (html.match(/data-i18n="/g) || []).length;
test(`${dataI18nCount} data-i18n attributes found`, dataI18nCount > 30);

console.log('\n7. No hardcoded Spanish in dynamic JS code:');
const codeLines = script.split('\n');
let hardcodedIssues = 0;
codeLines.forEach((line, i) => {
  if (line.includes('const translations') || line.includes('const bilingualTranslations')) return;
  if (line.match(/textContent\s*=\s*'[^']*[áéíóúñ][^']*'/)) hardcodedIssues++;
  if (line.match(/innerHTML\s*=\s*'[^']*[áéíóúñ][^']*'/)) hardcodedIssues++;
});
test('No hardcoded Spanish in dynamic code', hardcodedIssues === 0);

console.log('\n8. Key ES/EN translation counts:');
const esCount = Object.keys(translations.es).length;
const enCount = Object.keys(translations.en).length;
const bibCount = Object.keys(bilingualTranslations).length;
test(`translations.es has ${esCount} keys`, esCount > 100);
test(`translations.en has ${enCount} keys`, enCount > 100);
test(`bilingualTranslations has ${bibCount} keys`, bibCount > 50);

console.log('\n' + '='.repeat(60));
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log('='.repeat(60));

process.exit(failed === 0 ? 0 : 1);
