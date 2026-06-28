import re
with open('dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.find('CHART_HTML = f"""')
end = content.find('"""', start + 20)
chart = content[start:end]
for i, line in enumerate(chart.split('\n')):
    for m in re.finditer(r'(?<!\{)\{(?!\{)', line):
        pos = m.start()
        ctx = line[max(0, pos-30):pos+30].strip()
        print(f'L{i}: [{ctx}]')
