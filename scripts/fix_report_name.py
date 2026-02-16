path = "analyze_manager.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Добавляем маппинг имен
names_dict = """
RUS_NAMES = {
    "Volkov_Ivan": "Иван Волков",
    "Popov_Denis": "Денис Попов",
    "Ahmedshin_Dmitry": "Дмитрий Ахмедшин",
    "Garyaev_Maxim": "Максим Гаряев",
    "Ivanova_Elena": "Елена Иванова"
}

def analyze_manager(week, company, manager):
    rus_name = RUS_NAMES.get(manager, manager.replace("_", " "))
"""

# Вставляем словарь в начало скрипта (после импортов)
if "RUS_NAMES =" not in content:
    content = content.replace("GIGACHAT_KEY = os.getenv", names_dict + "\n\nGIGACHAT_KEY = os.getenv")
    
    # Заменяем manager на rus_name в промпте и заголовке MD
    content = content.replace('f"# Отчет: {manager.replace(\'_\', \' \')}', 'f"# Отчет: {rus_name}')
    # И в самом промпте
    content = content.replace('ТЫ — АУДИТОР ОТДЕЛА ПРОДАЖ.', 'ТЫ — АУДИТОР ОТДЕЛА ПРОДАЖ. МЕНЕДЖЕР: {rus_name}')
    
    # Добавляем переменную rus_name в начало функции (после def analyze_manager)
    # Это сложно сделать regex-ом, проще перезаписать функцию.
    # Но давай попробуем найти строку def analyze_manager...: и вставить после нее
    content = content.replace("def analyze_manager(week, company, manager):", 
                              "def analyze_manager(week, company, manager):\n    rus_name = RUS_NAMES.get(manager, manager.replace('_', ' '))")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Report script updated with Russian names.")
else:
    print("⚠️ Script already patched.")
