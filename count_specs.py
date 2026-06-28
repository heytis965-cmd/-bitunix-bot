import re
with open('dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('CHART_HTML = ')
end = content.find('return CHART_HTML')
chart_section = content[start:end]

# Find all format specifiers
specs = re.findall(r'(?<!%)%[sd]|%\.6f', chart_section)
print(f'Format specs: {len(specs)}')
for i, s in enumerate(specs):
    print(f'  {i}: {s}')
