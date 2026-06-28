import requests

tokens = [
    "ghp_BBhSOYPgkTUIh2jQcK9hVMDUZiF7C84Bc29S",
    "ghI_BBhSOYPgkTUIh2jQcK9hVMDUZiF7C84Bc29S",
]

for t in tokens:
    r = requests.get("https://api.github.com/user", headers={"Authorization": f"token {t}"}, timeout=10)
    data = r.json()
    login = data.get("login", "")
    msg = data.get("message", "")
    print(f"{t[:10]}... -> {r.status_code} {login or msg}")
