import requests
r = requests.get('http://localhost:5000', timeout=5)
html = r.text
print("Current column:", "Current" in html)
print("1000PEPE:", "1000PEPE" in html)
print("BOME:", "BOMEUSDT" in html)
print("No BONK:", html.count("BONKUSDT") <= 1)
print("Unrealized shown:", "$+0." in html or "$-0." in html or "+0.0" in html)
