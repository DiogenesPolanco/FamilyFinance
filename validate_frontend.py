#!/usr/bin/env python3
import re
import sys

def validate_html_js(file_path):
    errors = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    script_starts = []
    for i, line in enumerate(lines, 1):
        if '<script' in line and 'src=' in line:
            script_starts.append(i)
    
    script_injection = [
        (r'html\s*\+=.*`<script>', 'Script tag injection in template literal'),
        (r'`[^`]*\$\{[^}]*<script', 'Script tag in template literal variable'),
    ]
    
    for i, line in enumerate(lines, 1):
        for pattern, desc in script_injection:
            if re.search(pattern, line):
                errors.append(f"Line {i}: {desc}")
    
    func_defs = {}
    func_pattern = r'(?:^|[,\(])\s*(?:async\s+)?function\s+(\w+)'
    for i, line in enumerate(lines, 1):
        for match in re.finditer(func_pattern, line):
            func_name = match.group(1)
            if func_name in func_defs:
                errors.append(f"Line {i}: Duplicate function '{func_name}' (first at line {func_defs[func_name]})")
            else:
                func_defs[func_name] = i
    
    return errors

if __name__ == '__main__':
    file_path = '/home/sinope/Documents/opencodeprojects/family-finance/static/index.html'
    errors = validate_html_js(file_path)
    
    print("=" * 60)
    print("Frontend Validation Report")
    print("=" * 60)
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  X {e}")
        sys.exit(1)
    else:
        print("\nNo errors found!")
        sys.exit(0)
