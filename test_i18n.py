#!/usr/bin/env python3
import re
import sys

def find_hardcoded_texts(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    issues = []
    
    spanish_pattern = re.compile(r'>([^<]*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}[^<]*)<')
    quotes_pattern = re.compile(r"textContent\s*=\s*'([^']+)'|innerHTML\s*=\s*'([^']+)'")
    
    for i, line in enumerate(lines, 1):
        if 'data-i18n' in line or 'data-i18n-placeholder' in line:
            continue
        
        if '<script' in line or '</script>' in line:
            continue
        
        if 'placeholder=' in line:
            match = re.search(r'placeholder="([^"]+)"', line)
            if match and len(match.group(1)) > 2:
                issues.append((i, 'placeholder', match.group(1)))
        
        if '.textContent = ' in line or '.innerHTML = ' in line:
            match = re.search(r"\.text(?:Content|HTML)\s*=\s*'([^']*)'", line)
            if match and len(match.group(1)) > 2 and match.group(1) not in ['<p', '<div', '<span']:
                if not match.group(1).startswith('<'):
                    issues.append((i, 'js-text', match.group(1)))
        
        for match in spanish_pattern.finditer(line):
            text = match.group(1).strip()
            if len(text) > 2 and not text.startswith('<!--'):
                skip_words = ['id=', 'class=', 'onclick=', 'href=', 'src=', 'data-', 'style=', 'for=']
                if not any(text.startswith(sw) for sw in skip_words):
                    if not re.match(r'^\d+[\.,]?\d*$', text):
                        issues.append((i, 'html-text', text))
    
    return issues

if __name__ == '__main__':
    file_path = '/home/sinope/Documents/opencodeprojects/family-finance/static/index.html'
    issues = find_hardcoded_texts(file_path)
    
    print("=" * 60)
    print("i18n Hardcoded Text Report")
    print("=" * 60)
    
    if issues:
        print(f"\nFound {len(issues)} potential hardcoded texts:\n")
        for line_num, issue_type, text in issues[:50]:
            print(f"Line {line_num} ({issue_type}): {text[:60]}")
        if len(issues) > 50:
            print(f"\n... and {len(issues) - 50} more")
    else:
        print("\nNo hardcoded texts found!")
    
    sys.exit(0)
