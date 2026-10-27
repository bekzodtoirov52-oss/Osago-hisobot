import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(page_title="Ҳисобот ОСАГО", layout="wide")

# Делаем 2 колонки: 1 часть под логотип, 6 частей под заголовок
col_logo, col_title = st.columns([1, 6], vertical_alignment="center")

with col_logo:
    # Проверяем наличие файла
    if os.path.exists("logo.png"):
        st.image("logo.png", width=110)
    else:
        st.warning("Файл logo.png не найден")

with col_title:
    st.title("Ҳисобот ОСАГО: Расчет премий по страховым компаниям")
    st.caption("Автоматизированный мониторинг и аналитика реестров")

st.divider()

with st.container(border=True):
    uploaded_file = st.file_uploader("Загрузите файл Excel (.xlsx, .xls)", type=["xlsx", "xls"])
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip().lower() for c in df.columns]

        # 1. Определение названия компании
        if "sugurta_firma" in df.columns:
            company_col = "sugurta_firma"
        elif "insurance_company" in df.columns:
            company_col = "insurance_company"
        else:
            company_col = df.columns[0]
            st.warning(f"Колонка компании не найдена, выбрана: {company_col}")

        # 2. Объединение серии и номера полиса
        seria = df["policy_seria"].astype(str) if "policy_seria" in df.columns else ""
        num = df["policy_number"].astype(str) if "policy_number" in df.columns else ""
        df["полис_серия_номер"] = (seria + " " + num).str.strip()

        # 3. Объединение ФИО
        fname = df["firstname"].astype(str) if "firstname" in df.columns else ""
        lname = df["lastname"].astype(str) if "lastname" in df.columns else ""
        df["клиент_фио"] = (lname + " " + fname).str.strip()

        # 4. Расчет сумм премий (100%, 80%, 20%)
        prem_col = "res_ins_prem" if "res_ins_prem" in df.columns else ("premium" if "premium" in df.columns else None)
        
        if prem_col:
            df["премия_100"] = pd.to_numeric(df[prem_col].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce").fillna(0)
        else:
            df["премия_100"] = 0.0

        df["премия_80"] = df["премия_100"] * 0.80
        df["премия_20"] = df["премия_100"] * 0.20

        # Общие KPI
        total_policies = len(df)
        total_sum = df["премия_100"].sum()
        total_80 = df["премия_80"].sum()
        total_20 = df["премия_20"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Всего полисов", f"{total_policies:,}")
        col2.metric("Общая сумма (100%)", f"{total_sum:,.2f}")
        col3.metric("Сумма 80%", f"{total_80:,.2f}")
        col4.metric("Сумма 20%", f"{total_20:,.2f}")

        st.divider()

        # 5. Сводка по каждой фирме
        summary = df.groupby(company_col).agg(
            Полисов=("полис_серия_номер", "count"),
            Общая_премия=("премия_100", "sum"),
            Сумма_80=("премия_80", "sum"),
            Сумма_20=("премия_20", "sum")
        ).reset_index()

        summary.rename(columns={company_col: "Страховая компания"}, inplace=True)

        # Добавление строки ИТОГО в конец сводки
        total_row = pd.DataFrame([{
            "Страховая компания": "ИТОГО (ОБЩАЯ СУММА)",
            "Полисов": total_policies,
            "Общая_премия": total_sum,
            "Сумма_80": total_80,
            "Сумма_20": total_20
        }])
        summary_with_total = pd.concat([summary, total_row], ignore_index=True)

        tab1, tab2 = st.tabs(["📋 Сводка по фирмам (Отдельно и Общая)", "📑 Детальный реестр"])

        with tab1:
            st.subheader("Сводные данные по каждой компании")
            st.dataframe(
                summary_with_total.style.format({
                    "Общая_премия": "{:,.2f}",
                    "Сумма_80": "{:,.2f}",
                    "Сумма_20": "{:,.2f}"
                }),
                use_container_width=True
            )

        with tab2:
            st.subheader("Реестр всех договоров")
            cols_to_show = [
                c for c in [company_col, "полис_серия_номер", "клиент_фио", "polis_type", 
                            "deklaratsiya", "response_vaqti", "ins_srok", "end_date", 
                            "премия_100", "премия_80", "премия_20"] if c in df.columns
            ]
            st.dataframe(df[cols_to_show], use_container_width=True)

        # Экспорт в Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary_with_total.to_excel(writer, index=False, sheet_name="Сводка")
            df[cols_to_show].to_excel(writer, index=False, sheet_name="Реестр")
        output.seek(0)

        st.download_button(
            label="📥 Скачать готовый отчет в Excel",
            data=output,
            file_name="hisobot_osago_processed.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ошибка при обработке файла: {e}")
