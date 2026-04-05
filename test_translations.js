const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, 'static/index.html'), 'utf8');

const translations = {};
const translationMatch = html.match(/const translations = \{([\s\S]*?)\};/);
if (translationMatch) {
    const content = translationMatch[1];
    const esMatch = content.match(/es:\s*\{([\s\S]*?)\},/);
    const enMatch = content.match(/en:\s*\{([\s\S]*?)\}/);
    
    if (esMatch) {
        const keys = esMatch[1].match(/(\w+):/g) || [];
        translations.es = keys.map(k => k.replace(':', ''));
    }
    if (enMatch) {
        const keys = enMatch[1].match(/(\w+):/g) || [];
        translations.en = keys.map(k => k.replace(':', ''));
    }
}

const dataI18nElements = html.match(/data-i18n="([^"]+)"/g) || [];
const usedKeys = dataI18nElements.map(e => e.match(/data-i18n="([^"]+)"/)[1]);

const missingInES = usedKeys.filter(k => !translations.es.includes(k));
const missingInEN = usedKeys.filter(k => !translations.en.includes(k));

console.log('='.repeat(60));
console.log('Translation Coverage Report');
console.log('='.repeat(60));
console.log(`Total translation keys (ES): ${translations.es.length}`);
console.log(`Total translation keys (EN): ${translations.en.length}`);
console.log(`Elements with data-i18n: ${usedKeys.length}`);

if (missingInES.length > 0) {
    console.log(`\n⚠ Missing in ES (${missingInES.length}):`);
    missingInES.slice(0, 10).forEach(k => console.log(`  - ${k}`));
    if (missingInES.length > 10) console.log(`  ... and ${missingInES.length - 10} more`);
}

if (missingInEN.length > 0) {
    console.log(`\n⚠ Missing in EN (${missingInEN.length}):`);
    missingInEN.slice(0, 10).forEach(k => console.log(`  - ${k}`));
    if (missingInEN.length > 10) console.log(`  ... and ${missingInEN.length - 10} more`);
}

if (missingInES.length === 0 && missingInEN.length === 0) {
    console.log('\n✅ All translation keys are defined in both languages!');
}

const unusedKeys = translations.es.filter(k => !usedKeys.includes(k));
if (unusedKeys.length > 0) {
    console.log(`\nℹ Unused translation keys (${unusedKeys.length}):`);
    unusedKeys.slice(0, 5).forEach(k => console.log(`  - ${k}`));
}

console.log('\n' + '='.repeat(60));
