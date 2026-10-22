import io
import re
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Ҳисобот — Sug'urta hisobotlari",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Sug'urta mukofotlari va polislar hisoboti")
st.caption(
    "Excel faylni yuklang: har bir sug'urta kompaniyasi bo'yicha hisob-kitob, OSAGO (80/20) va boshqa polislar (75/25) taqsimoti."
)


def normalize_col(name: str) -> str:
    """Ustun nomlarini tozalash va standartlashtirish."""
    s = str(name).strip().lower()
    s = re.sub(r"[\s_]+", "_", s)
    return s


def find_column(df_columns, candidates):
    """Mavjud ustunlar orasidan mos keladiganini topish."""
    col_map = {normalize_col(c): c for c in df_columns}
    for cand in candidates:
        cand_norm = normalize_col(cand)
        if cand_norm in col_map:
            return col_map[cand_norm]
    return None


def clean_currency(val):
    """Matnli pul qiymatlarini float formatga o'tkazish."""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace(" ", "").replace(",", ".").replace("\xa0", "")
    s = re.sub(r"[^\d.]", "", s)
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


uploaded_file = st.sidebar.file_uploader(
    "📁 Excel faylni yuklang (.xlsx, .xls)", type=["xlsx", "xls"]
)

if uploaded_file is None:
    st.info("Iltimos, chap paneldagi tugma orqali Excel faylni yuklang.")
    st.stop()

try:
    raw_df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Faylni o'qishda xatolik yuz berdi: {e}")
    st.stop()

# Ustunlarni aniqlash
firma_col = find_column(raw_df.columns, ["sugurta_firma", "insurance_company", "firma", "kompaniya"])
decl_col = find_column(raw_df.columns, ["declaration", "deklaratsiya", "deklaratsiya_raqami"])
type_col = find_column(raw_df.columns, ["polis_type", "sugurta_turi", "polis_turi", "type"])
vaqt_col = find_column(raw_df.columns, ["response_vaqti", "sana", "date", "vaqt", "vaqti"])
srok_col = find_column(raw_df.columns, ["ins_srok", "muddat", "srok", "period"])
seria_col = find_column(raw_df.columns, ["seria_polis", "polis_seria", "seria"])
number_col = find_column(raw_df.columns, ["number_polis", "polis_nomer", "polis_number", "number"])
first_col = find_column(raw_df.columns, ["firstname", "ism", "first_name"])
last_col = find_column(raw_df.columns, ["lastname", "familiya", "last_name"])
prem_col = find_column(raw_df.columns, ["res_ins_prem", "premium", "mukofot", "summa", "prem"])

if not firma_col or not prem_col:
    st.error("Faylda sug'urta firmasi yoki mukofot summasi ustunlari topilmadi!")
    st.write("Mavjud ustunlar:", list(raw_df.columns))
    st.stop()

# Ishchi dataframe yaratish
df = pd.DataFrame()
df["sugurta_firma"] = raw_df[firma_col].fillna("Noma'lum").astype(str).str.strip()

# Seriya va raqamni birlashtirish
ser = raw_df[seria_col].fillna("").astype(str).str.strip() if seria_col else ""
num = raw_df[number_col].fillna("").astype(str).str.strip() if number_col else ""
if seria_col or number_col:
    df["polis_full_number"] = (ser + " " + num).str.strip()
else:
    df["polis_full_number"] = "-"

# FIO birlashtirish
first = raw_df[first_col].fillna("").astype(str).str.strip() if first_col else ""
last = raw_df[last_col].fillna("").astype(str).str.strip() if last_col else ""
if first_col or last_col:
    df["client_fullname"] = (first + " " + last).str.strip()
else:
    df["client_fullname"] = "-"

df["polis_type"] = raw_df[type_col].fillna("Boshqa").astype(str).str.strip() if type_col else "Boshqa"
df["declaration"] = raw_df[decl_col].fillna("-").astype(str) if decl_col else "-"
df["ins_srok"] = raw_df[srok_col].fillna("-").astype(str) if srok_col else "-"
df["response_vaqti"] = raw_df[vaqt_col] if vaqt_col else "-"

# Mukofot summasini hisoblash
df["premium"] = raw_df[prem_col].apply(clean_currency)

# OSAGO tekshiruvi (80/20 vs 75/25)
is_osago = df["polis_type"].str.lower().str.contains("osago|осаго|avto.*fuqaro|avtograjdan", regex=True)
df["is_osago"] = is_osago
df["kategoriya"] = np.where(is_osago, "OSAGO (80/20)", "Boshqa (75/25)")

df["main_share"] = np.where(is_osago, df["premium"] * 0.80, df["premium"] * 0.75)
df["comm_share"] = np.where(is_osago, df["premium"] * 0.20, df["premium"] * 0.25)

# Sidebar filtrlari
st.sidebar.markdown("---")
st.sidebar.subheader("Filtrlar")

kompaniyalar = ["Barchasi"] + sorted(df["sugurta_firma"].unique().tolist())
sel_firma = st.sidebar.selectbox("Sug'urta kompaniyasi", kompaniyalar)

sel_tur = st.sidebar.radio("Polis turi bo'yicha", ["Barchasi", "Faqat OSAGO", "OSAGO emas"])

filtered_df = df.copy()

if sel_firma != "Barchasi":
    filtered_df = filtered_df[filtered_df["sugurta_firma"] == sel_firma]

if sel_tur == "Faqat OSAGO":
    filtered_df = filtered_df[filtered_df["is_osago"]]
elif sel_tur == "OSAGO emas":
    filtered_df = filtered_df[~filtered_df["is_osago"]]

# KPI Metrikalar
c1, c2, c3, c4 = st.columns(4)
total_count = len(filtered_df)
total_prem = filtered_df["premium"].sum()
total_main = filtered_df["main_share"].sum()
total_comm = filtered_df["comm_share"].sum()

c1.metric("Jami polislar soni", f"{total_count:,} dona")
c2.metric("Umumiy summa (100%)", f"{total_prem:,.2f} UZS")
c3.metric("Asosiy ulush (75% / 80%)", f"{total_main:,.2f} UZS")
c4.metric("Komissiya (25% / 20%)", f"{total_comm:,.2f} UZS")

st.markdown("---")

# 1. Kompaniyalar bo'yicha jamlanma jadval
st.subheader("🏢 Kompaniyalar kesimida hisobot")

summary = (
    filtered_df.groupby("sugurta_firma")
    .agg(
        polis_soni=("premium", "count"),
        jami_premium=("premium", "sum"),
        asosiy_ulush=("main_share", "sum"),
        komissiya_ulush=("comm_share", "sum"),
    )
    .reset_index()
)

summary.rename(
    columns={
        "sugurta_firma": "Sug'urta kompaniyasi",
        "polis_soni": "Polislar soni",
        "jami_premium": "Jami summa",
        "asosiy_ulush": "Asosiy ulush (75%/80%)",
        "komissiya_ulush": "Komissiya (25%/20%)",
    },
    inplace=True,
)

# Umumiy JAMI qatorini qo'shish
total_row = pd.DataFrame(
    [
        {
            "Sug'urta kompaniyasi": "JAMI / ИТОГО",
            "Polislar soni": summary["Polislar soni"].sum(),
            "Jami summa": summary["Jami summa"].sum(),
            "Asosiy ulush (75%/80%)": summary["Asosiy ulush (75%/80%)"].sum(),
            "Komissiya (25%/20%)": summary["Komissiya (25%/20%)"].sum(),
        }
    ]
)
summary_with_total = pd.concat([summary, total_row], ignore_index=True)

st.dataframe(
    summary_with_total.style.format(
        {
            "Polislar soni": "{:,}",
            "Jami summa": "{:,.2f}",
            "Asosiy ulush (75%/80%)": "{:,.2f}",
            "Komissiya (25%/20%)": "{:,.2f}",
        }
    ),
    use_container_width=True,
)

st.markdown("---")

# 2. To'liq tafsilotli jadval
st.subheader("📋 To'liq tafsilotli ro'yxat")

detail_display = filtered_df[
    [
        "sugurta_firma",
        "polis_full_number",
        "client_fullname",
        "polis_type",
        "kategoriya",
        "declaration",
        "ins_srok",
        "response_vaqti",
        "premium",
        "main_share",
        "comm_share",
    ]
].rename(
    columns={
        "sugurta_firma": "Kompaniya",
        "polis_full_number": "Polis seriya va raqami",
        "client_fullname": "Mijoz (F.I.O)",
        "polis_type": "Polis turi",
        "kategoriya": "Taqsimot qoidasi",
        "declaration": "Deklaratsiya",
        "ins_srok": "Muddati",
        "response_vaqti": "Sana/Vaqt",
        "premium": "Mukofot (100%)",
        "main_share": "Asosiy (75%/80%)",
        "comm_share": "Komissiya (25%/20%)",
    }
)

st.dataframe(
    detail_display.style.format(
        {
            "Mukofot (100%)": "{:,.2f}",
            "Asosiy (75%/80%)": "{:,.2f}",
            "Komissiya (25%/20%)": "{:,.2f}",
        }
    ),
    use_container_width=True,
)

# Excel formatida yuklab olish
output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    summary_with_total.to_excel(writer, sheet_name="Jamlanma_Hisobot", index=False)
    detail_display.to_excel(writer, sheet_name="Batafsil_Polislar", index=False)

st.download_button(
    label="📥 Tayyor hisobotni Excel formatida yuklab olish",
    data=output.getvalue(),
    file_name="Sugurta_Hisoboti.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
