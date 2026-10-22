import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Хисобот кузатув", layout="wide")

st.title("📊 Хисобот кузатув — Страховые полисы и премии")

# 1. Боковая панель: выбор режима
mode = st.sidebar.radio(
    "Выберите тип страхования / процентное соотношение:",
    ("Стандартный (75% / 25%)", "ОСАГО (80% / 20%)")
)

is_osago = "ОСАГО" in mode
pct1 = 0.80 if is_osago else 0.75
pct2 = 0.20 if is_osago else 0.25
col1_name = "Доля 80%" if is_osago else "Доля 75%"
col2_name = "Доля 20%" if is_osago else "Доля 25%"

uploaded_file = st.sidebar.file_uploader("Загрузите Excel файл", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        # Очистка названий колонок
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Проверка обязательных полей
        required = ['sugurta_firma', 'res_ins_prem']
        missing = [c for c in required if c not in df.columns]
        if missing:
            st.error(f"В файле отсутствуют обязательные колонки: {missing}")
            st.stop()

        # Преобразование суммы в число
        df['res_ins_prem'] = pd.to_numeric(
            df['res_ins_prem'].astype(str).str.replace(' ', '').str.replace(',', '.'), 
            errors='coerce'
        ).fillna(0)

        # Объединение серий и номеров
        seria = df['seria_polis'].fillna('').astype(str) if 'seria_polis' in df.columns else ''
        number = df['number_polis'].fillna('').astype(str) if 'number_polis' in df.columns else ''
        df['polis_full'] = (seria + ' ' + number).str.strip()

        # Объединение ФИО
        first = df['firstname'].fillna('').astype(str) if 'firstname' in df.columns else ''
        last = df['lastname'].fillna('').astype(str) if 'lastname' in df.columns else ''
        df['client_fullname'] = (first + ' ' + last).str.strip()

        # Расчет процентов
        df[col1_name] = df['res_ins_prem'] * pct1
        df[col2_name] = df['res_ins_prem'] * pct2

        # Общие показатели (KPI)
        total_policies = len(df)
        total_prem = df['res_ins_prem'].sum()
        total_part1 = df[col1_name].sum()
        total_part2 = df[col2_name].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Всего полисов", f"{total_policies:,}")
        m2.metric("Общая премия", f"{total_prem:,.2f}")
        m3.metric(f"Итого {col1_name}", f"{total_part1:,.2f}")
        m4.metric(f"Итого {col2_name}", f"{total_part2:,.2f}")

        # Сводка по каждой фирме отдельно
        st.subheader("🏢 Сводный отчет по страховым компаниям")
        summary = df.groupby('sugurta_firma').agg(
            Полисов=('sugurta_firma', 'count'),
            Общая_премия=('res_ins_prem', 'sum'),
            **{col1_name: (col1_name, 'sum')},
            **{col2_name: (col2_name, 'sum')}
        ).reset_index()

        st.dataframe(summary.style.format({
            'Общая_премия': '{:,.2f}',
            col1_name: '{:,.2f}',
            col2_name: '{:,.2f}'
        }), use_container_width=True)

        # Детальная таблица
        st.subheader("📄 Детальные данные")
        firms = st.multiselect("Фильтр по страховой компании:", options=df['sugurta_firma'].unique(), default=df['sugurta_firma'].unique())
        
        display_cols = [c for c in ['sugurta_firma', 'declaration', 'response_vaqti', 'polis_full', 'ins_srok', 'client_fullname', 'res_ins_prem', col1_name, col2_name] if c in df.columns]
        filtered_df = df[df['sugurta_firma'].isin(firms)][display_cols]

        st.dataframe(filtered_df.style.format({
            'res_ins_prem': '{:,.2f}',
            col1_name: '{:,.2f}',
            col2_name: '{:,.2f}'
        }), use_container_width=True)

        # Выгрузка в Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary.to_excel(writer, sheet_name='Сводка по фирмам', index=False)
            filtered_df.to_excel(writer, sheet_name='Детально', index=False)
        
        st.download_button(
            label="📥 Скачать результат в Excel",
            data=output.getvalue(),
            file_name="xisobot_kuzatuv_raschet.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ошибка при обработке файла: {e}")
else:
    st.info("Пожалуйста, загрузите Excel файл через боковое меню для расчета.")
