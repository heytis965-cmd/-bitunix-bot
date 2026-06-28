import re
with open('dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('CHART_HTML = ')
end = content.find('""" % (', start)
chart = content[start:end]

# Count %s placeholders (but not %%)
placeholders = re.findall(r'(?<!%)%s', chart)
print(f'Total placeholders: {len(placeholders)}')

# Count arguments
args_start = content.find('""" % (', start) + len('""" % (')
args_end = content.find(')', args_start)
args_str = content[args_start:args_end]
args = [a.strip().rstrip(',') for a in args_str.split(',') if a.strip()]
print(f'Total arguments: {len(args)}')
for i, a in enumerate(args):
    print(f'  {i}: {a}')
