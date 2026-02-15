# -*- coding: utf-8 -*-

MANAGER_NAMES = {
    "Ahmedshin_Dmitry": "Дмитрий Ахмедшин",
    "Garyaev_Maxim": "Максим Гарьяев", 
    "Popov_Denis": "Денис Попов",
    "Volkov_Ivan": "Иван Волков",
    "Sergeev_Alexey": "Алексей Сергеев",
    "Unknown": "Неизвестный",
    "Ivanova_Elena": "Елена Иванова",
    "Shevchuk_Dmitry": "Дмитрий Шевчук"
}

def get_rus_name(eng_name):
    # Пытаемся найти точное совпадение
    if eng_name in MANAGER_NAMES:
        return MANAGER_NAMES[eng_name]
    
    # Если нет, пытаемся красиво отформатировать (Ahmedshin_Dmitry -> Ahmedshin Dmitry)
    return eng_name.replace("_", " ")
