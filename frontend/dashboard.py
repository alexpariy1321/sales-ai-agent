import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация страницы
st.set_page_config(
    page_title="📞 Анализ звонков менеджеров",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Светлая современная тема
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    h1 {
        color: #2c3e50;
        font-weight: 600;
        margin-bottom: 0;
    }
    h2, h3 {
        color: #34495e;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin: 10px 0;
    }
    .stExpander {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.title("📞 Система анализа звонков менеджеров")
st.markdown("**Bitrix24 → AI → Insights**")
st.markdown("---")

# Sidebar - фильтры
with st.sidebar:
    st.header("⚙️ Настройки")
    
    # Выбор дат
    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input(
            "Дата с:",
            value=datetime(2026, 2, 2),
            max_value=datetime.now()
        )
    with col2:
        date_to = st.date_input(
            "Дата по:",
            value=datetime(2026, 2, 6),
            max_value=datetime.now()
        )
    
    st.markdown("---")
    
    # Фильтр по менеджеру
    st.subheader("👥 Менеджеры")
    managers = {
        "Все менеджеры": None,
        "Ахмедшин Дмитрий": "+79292021732",
        "Сергеев Константин": "+79221699767",
        "Попов Денис": "+79221421423",
        "Гаряев Максим": "+79221610964",
        "Входящие (общий)": "+79222922624"
    }
    
    selected_manager = st.selectbox(
        "Выберите менеджера:",
        options=list(managers.keys()),
        index=0
    )
    
    st.markdown("---")
    
    # Кнопка загрузки
    load_button = st.button("🔄 Загрузить звонки", use_container_width=True, type="primary")
    
    st.markdown("---")
    st.caption("💡 **Подсказка:** Выберите даты и нажмите 'Загрузить звонки'")

# Основная область
if load_button:
    st.session_state.load_calls = True
    st.session_state.date_from = date_from
    st.session_state.date_to = date_to
    st.session_state.selected_manager = selected_manager

if st.session_state.get("load_calls", False):
    with st.spinner("⏳ Загружаем звонки из Bitrix24..."):
        try:
            # Получаем webhook из .env
            webhook = os.getenv("UN_BITRIX_WEBHOOK_BASE")
            
            if not webhook:
                st.error("❌ UN_BITRIX_WEBHOOK_BASE не найден в .env файле")
                st.stop()
            
            # Загружаем звонки
            all_calls = []
            start = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            while True:
                filters = {
                    "FILTER[>=CALL_START_DATE]": st.session_state.date_from.strftime("%Y-%m-%d"),
                    "FILTER[<=CALL_START_DATE]": st.session_state.date_to.strftime("%Y-%m-%d"),
                    "FILTER[!CALL_RECORD_URL]": "null",
                    "START": start,
                    "LIMIT": 50
                }
                
                if managers[st.session_state.selected_manager]:
                    filters["FILTER[PORTAL_NUMBER]"] = managers[st.session_state.selected_manager]
                
                resp = requests.post(
                    f"{webhook}voximplant.statistic.get.json",
                    data=filters,
                    timeout=60
                )
                
                batch = resp.json().get("result", [])
                if not batch:
                    break
                
                all_calls.extend(batch)
                start += 50
                
                # Обновляем прогресс
                progress = min(len(all_calls) / 600, 1.0)
                progress_bar.progress(progress)
                status_text.text(f"Загружено: {len(all_calls)} звонков...")
                
                if start > 600:
                    break
            
            progress_bar.empty()
            status_text.empty()
            
            # Статистика в карточках
            st.markdown("### 📊 Статистика за период")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Всего звонков", len(all_calls))
            
            with col2:
                incoming = sum(1 for c in all_calls if c.get("CALL_TYPE") == "1")
                st.metric("📥 Входящие", incoming, f"{incoming/len(all_calls)*100:.0f}%")
            
            with col3:
                outgoing = sum(1 for c in all_calls if c.get("CALL_TYPE") == "2")
                st.metric("📤 Исходящие", outgoing, f"{outgoing/len(all_calls)*100:.0f}%")
            
            with col4:
                durations = [int(c.get("CALL_DURATION", 0)) for c in all_calls]
                total_hours = sum(durations) / 3600
                st.metric("⏱️ Общее время", f"{total_hours:.1f} ч")
            
            st.markdown("---")
            
            # Таблица звонков
            st.markdown("### 📋 Список звонков")
            
            # Показываем первые 50
            for idx, call in enumerate(all_calls[:50]):
                manager_name = {
                    "+79292021732": "Ахмедшин Дмитрий",
                    "+79221699767": "Сергеев Константин",
                    "+79221421423": "Попов Денис",
                    "+79221610964": "Гаряев Максим",
                    "+79222922624": "Входящие (общий)"
                }.get(call.get("PORTAL_NUMBER"), "Неизвестный")
                
                call_type = "📥 Входящий" if call.get("CALL_TYPE") == "1" else "📤 Исходящий"
                duration = int(call.get("CALL_DURATION", 0))
                duration_str = f"{duration//60}:{duration%60:02d}"
                
                with st.expander(
                    f"🎧 {manager_name} | {call_type} | "
                    f"{call.get('PHONE_NUMBER', 'N/A')} | ⏱️ {duration_str}",
                    expanded=False
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**📅 Дата:** {call.get('CALL_START_DATE', 'N/A')}")
                        st.write(f"**📞 Телефон:** {call.get('PHONE_NUMBER', 'N/A')}")
                        st.write(f"**🆔 ID:** `{call.get('CALL_ID', 'N/A')[:40]}...`")
                        
                        # URL записи
                        if call.get("CALL_RECORD_URL"):
                            st.write(f"**🎵 Запись:** [Скачать]({call.get('CALL_RECORD_URL')})")
                    
                    with col2:
                        if st.button("📝 Транскрипция", key=f"trans_{idx}"):
                            st.session_state[f"show_transcript_{idx}"] = True
                        
                        if st.button("🤖 Анализ", key=f"analyze_{idx}"):
                            st.info("Функция в разработке...")
                    
                    # Показываем транскрипцию если запрошена
                    if st.session_state.get(f"show_transcript_{idx}", False):
                        st.markdown("---")
                        st.markdown("**✏️ Настройте промпт для AI:**")
                        
                        custom_prompt = st.text_area(
                            "Промпт:",
                            value="""Проанализируй звонок и оцени:
1. Качество общения менеджера (0-10)
2. Были ли договоренности о следующем контакте?
3. Какие ошибки допустил менеджер?
4. Рекомендации по улучшению""",
                            height=120,
                            key=f"prompt_{idx}"
                        )
                        
                        if st.button("🚀 Запустить анализ", key=f"run_analyze_{idx}"):
                            with st.spinner("Анализируем через Gemini API..."):
                                st.info("🔄 Интеграция Gemini API — следующий шаг!")
            
            if len(all_calls) > 50:
                st.info(f"ℹ️ Показано первых 50 из {len(all_calls)} звонков")
            
        except Exception as e:
            st.error(f"❌ Ошибка загрузки: {str(e)}")
            st.info("Проверьте, что backend запущен: `systemctl status sales-ai-backend`")

else:
    # Приветственный экран
    st.info("👈 Выберите даты в боковой панели и нажмите '🔄 Загрузить звонки'")
    
    st.markdown("### 🎯 Возможности системы:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **✅ Уже работает:**
        - 📊 Статистика по менеджерам
        - 📥 Фильтрация по датам
        - 🎧 Ссылки на аудиозаписи
        - 📞 650+ звонков в базе
        """)
    
    with col2:
        st.markdown("""
        **⏳ В разработке:**
        - 📝 Транскрибация через Gemini
        - 🤖 AI-анализ с кастомными промптами
        - 📈 Графики и визуализации
        - 💾 Экспорт отчетов
        """)
