with open('all_symbols.txt') as f:
    syms = [line.strip() for line in f if line.strip()]

lines = []
for i in range(0, len(syms), 8):
    chunk = syms[i:i+8]
    lines.append("    " + ", ".join(f'"{s}"' for s in chunk) + ",")

print(f"# Total: {len(syms)} symbols")
print("PD_SYMBOLS = [")
for l in lines:
    print(l)
print("]")
