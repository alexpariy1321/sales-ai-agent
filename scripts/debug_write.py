import os
import requests

# 1. Проверяем путь
BASE_DIR = "/root/sales-ai-agent/data/archive"
print(f"📁 Checking base dir: {BASE_DIR}")

if not os.path.exists(BASE_DIR):
    print("❌ Base dir not found! Creating...")
    try:
        os.makedirs(BASE_DIR, exist_ok=True)
        print("✅ Created base dir.")
    except Exception as e:
        print(f"❌ Failed to create base dir: {e}")
        exit(1)

# 2. Создаем тестовую папку недели
week_folder = os.path.join(BASE_DIR, "TEST_WEEK")
try:
    os.makedirs(week_folder, exist_ok=True)
    print(f"✅ Created test week folder: {week_folder}")
except Exception as e:
    print(f"❌ Failed to create week folder: {e}")
    exit(1)

# 3. Пробуем скачать реальный файл (тест интернета)
print("🌐 Testing download...")
try:
    # Маленький mp3 для теста
    url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" 
    # (или любой другой, если этот недоступен)
    
    test_file = os.path.join(week_folder, "test_download.mp3")
    
    r = requests.get(url, stream=True, timeout=10)
    if r.status_code == 200:
        with open(test_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
                break # Качаем только кусочек для теста
        print(f"✅ Successfully wrote file to: {test_file}")
        print(f"   Size: {os.path.getsize(test_file)} bytes")
    else:
        print(f"❌ Download failed: Status {r.status_code}")
except Exception as e:
    print(f"❌ Download/Write error: {e}")

# 4. Проверяем реальный скрипт download_calls.py (читаем его конфиг)
print("\n🔍 Checking download_calls.py config...")
try:
    with open("download_calls.py", "r") as f:
        content = f.read()
        if 'DATA_DIR = "/root/sales-ai-agent/data/archive"' in content:
            print("✅ DATA_DIR is correct in script.")
        else:
            print("⚠️ DATA_DIR might be wrong in script!")
            # Ищем строку с DATA_DIR
            for line in content.splitlines():
                if "DATA_DIR =" in line:
                    print(f"   Found: {line.strip()}")
except Exception as e:
    print(f"❌ Could not read download_calls.py: {e}")

