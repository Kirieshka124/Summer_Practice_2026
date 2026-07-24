import requests

API_KEY = "31fadd410b7bfeb1e11280ffedc81652"  # Вставь сюда свой рабочий ключ

url = "https://ws.audioscrobbler.com/2.0/"
params = {
    "method": "artist.getinfo",
    "artist": "Radiohead",
    "api_key": API_KEY,
    "format": "json"
}

# Твой текущий User-Agent (как в коде)
headers_bad = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# Попробуем без User-Agent
print("1. Без User-Agent:")
r1 = requests.get(url, params=params)
print(f"Статус: {r1.status_code}")
if r1.status_code == 200:
    print("✅ Работает!")
else:
    print(f"❌ Ошибка: {r1.text[:200]}")

# Попробуем с твоим User-Agent
print("\n2. С твоим User-Agent:")
r2 = requests.get(url, params=params, headers=headers_bad)
print(f"Статус: {r2.status_code}")
if r2.status_code == 200:
    print("✅ Работает!")
else:
    print(f"❌ Ошибка: {r2.text[:200]}")

# Попробуем без параметров (только ключ)
print("\n3. Просто ключ (без artist):")
params2 = {"method": "artist.getinfo", "api_key": API_KEY, "format": "json"}
r3 = requests.get(url, params=params2)
print(f"Статус: {r3.status_code}")