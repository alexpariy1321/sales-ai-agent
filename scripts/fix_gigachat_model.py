path = "analyze_manager.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Ищем строку инициализации и добавляем модель
old_line = 'with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False) as giga:'
new_line = 'with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False, model="GigaChat-Pro") as giga:'

# Если переменная называется GIGACHAT_KEY (как в нашем скрипте), то ищем так:
if 'credentials=GIGACHAT_KEY' in content:
    old_line = 'with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:'
    new_line = 'with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False, model="GigaChat-Pro") as giga:'

if old_line in content:
    content = content.replace(old_line, new_line)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Switched to GigaChat-Pro model!")
else:
    print("⚠️ Could not find initialization line. Checking manually...")
    if 'model="GigaChat-Pro"' in content:
        print("✅ GigaChat-Pro is ALREADY set.")
    else:
        # Если не нашли, перезаписываем файл целиком (надежнее)
        pass # Мы перезапишем файл ниже
