import os

# Пути согласно вашей реальной структуре
BASE_PATH = "data/archive/2026-02-02_2026-02-06/SO/Volkov_Ivan"
REPORT_DIR = os.path.join(BASE_PATH, "report")
FINAL_AUDIT_FILE = os.path.join(BASE_PATH, "FINAL_AUDIT_VOLKOV_FEB.md")
SUPER_REPORT_FILE = os.path.join(BASE_PATH, "FULL_WEEKLY_AUDIT_VOLKOV_COMPLETE.md")

def assemble():
    if not os.path.exists(FINAL_AUDIT_FILE):
        print("Ошибка: Сначала запустите генерацию финального отчета!")
        return

    with open(SUPER_REPORT_FILE, 'w', encoding='utf-8') as super_file:
        # 1. Записываем заглавную часть (Сводный отчет для Куркина)
        super_file.write("# СВОДНЫЙ АУДИТ РАБОТЫ ИВАНА ВОЛКОВА (02.02 - 06.02)\n")
        super_file.write("## Итоговая аналитика за неделю\n\n")
        
        with open(FINAL_AUDIT_FILE, 'r', encoding='utf-8') as f:
            super_file.write(f.read())
        
        super_file.write("\n\n---\n# ДЕТАЛЬНЫЙ РАЗБОР КАЖДОГО ЗВОНКА\n")
        super_file.write("Ниже представлены индивидуальные отчеты, на основе которых сформирован свод.\n\n")

        # 2. Добавляем все индивидуальные отчёты из папки report/
        report_files = sorted([f for f in os.listdir(REPORT_DIR) if f.endswith('.md')])
        
        for filename in report_files:
            # Пропускаем сам финальный файл, если он случайно попал в папку
            if "FINAL_AUDIT" in filename: continue
            
            file_path = os.path.join(REPORT_DIR, filename)
            super_file.write(f"\n## Звонок: {filename}\n")
            super_file.write(f"**Путь к аудио:** `audio/{filename.replace('.md', '.mp3')}`\n\n")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                super_file.write(f.read())
                super_file.write("\n\n" + "="*50 + "\n") # Разделитель между звонками

    print(f"Супер-отчет успешно собран: {SUPER_REPORT_FILE}")

if __name__ == "__main__":
    assemble()
