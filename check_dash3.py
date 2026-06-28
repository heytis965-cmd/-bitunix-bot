import requests
r = requests.get('http://localhost:5000', timeout=5)
html = r.text
print("Total visible:", "Total" in html)
print("Free visible:", ">Free<" in html)
print("In Positions:", "In Positions" in html)
print("Unrealized PnL:", "Unrealized PnL" in html)
print("Session PnL:", "Session PnL" in html)
print("$50.00:", "$50.00" in html)
