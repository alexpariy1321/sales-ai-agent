import re

file_path = "/root/sales-ai-agent/scripts/analyze_manager.py"

# Читаем файл
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Ищем блок RUS_NAMES
pattern = r'(RUS_NAMES\s*=\s*{[^}]*)}'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_block = match.group(1)
    # Если Кузнецова еще нет -> добавляем
    if "Kuznetsov_Artem" not in old_block:
        new_entry = '    "Kuznetsov_Artem": "Артем Кузнецов",\n    "Garyaev_Maxim":' # Вставляем перед Гаряевым или в конец
        # Проще добавить в конец словаря
        new_block = old_block.rstrip() + ',\n    "Kuznetsov_Artem": "Артем Кузнецов"\n}'
        new_content = content.replace(match.group(0), new_block)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ Артем Кузнецов добавлен в analyze_manager.py!")
    else:
        print("⚠️ Артем уже есть в списке.")
else:
    print("❌ Не нашел блок RUS_NAMES в файле.")
