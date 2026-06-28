import subprocess, sys
proc = subprocess.Popen(
    [sys.executable, "-u", "simulator.py"],
    stdout=open("output.log", "w", encoding="utf-8"),
    stderr=subprocess.STDOUT,
    cwd=r"C:\Users\Леонид\Mimo_Projects\bitunix_bot",
)
print(f"Simulator PID: {proc.pid}")
print("Check output.log for results")
