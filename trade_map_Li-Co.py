# ================================================
# 🌍 리튬 및 코발트 국제 교역 지도
# ================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pycountry
import gdown

# ------------------------------
# ✅ Streamlit 기본 설정
# ------------------------------
st.set_page_config(page_title="국제 교역 데이터 지도", page_icon="🌐", layout="wide")
st.title("🌐 리튬 및 코발트 국제 교역 지도")


# ------------------------------
# ✅ 1. 데이터 불러오기
# ------------------------------
@st.cache_data
def load_data():
    """UN Comtrade 데이터 다운로드 및 전처리"""
    url = "https://drive.google.com/uc?id=1OmJD2lFKlaJt_oXu2LuzkvdYkD-N8PzV"
    gdown.download(url, "netwgt_import_monthly.csv", quiet=False)

    data = pd.read_csv("netwgt_import_monthly.csv", encoding="utf-8-sig")

    # 열 이름 정리
    data.columns = (
        data.columns
        .str.strip()
        .str.lower()
        .str.replace('\ufeff', '', regex=False)
    )

    # 주요 열 정리
    for col in ['period', 'cmdcode', 'reporter', 'partner']:
        if col in data.columns:
            data[col] = data[col].astype(str).str.strip()

    # 연도 컬럼 추가
    if 'period' in data.columns:
        data['year'] = data['period'].astype(str).str[:4]

    return data


data = load_data()  # ✅ 여기서 data가 처음 정의됨!


# ------------------------------
# ✅ 2. ISO 코드 변환 함수
# ------------------------------
def country_to_iso3(name):
    """국가명을 ISO3 코드로 변환"""
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None


country_fix = {
    'Korea, Rep.': 'KOR',
    'Republic of Korea': 'KOR',
    'United States': 'USA',
    'Russian Federation': 'RUS',
    'Viet Nam': 'VNM',
    'Iran (Islamic Republic of)': 'IRN',
    'Lao People\'s Democratic Republic': 'LAO',
    'Czechia': 'CZE',
    'Dominican Rep.': 'DOM'
}

# ISO 코드 컬럼 추가
data['partner_iso3'] = data['partner'].apply(
    lambda x: country_fix[x] if x in country_fix else country_to_iso3(x)
)

# 숫자 변환 및 결측치 제거
data['netwgt'] = pd.to_numeric(data['netwgt'], errors='coerce')
data = data.dropna(subset=['partner_iso3', 'netwgt'])


# ------------------------------
# ✅ 3. Streamlit UI 구성
# ------------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    view_mode = st.radio("보기 단위 선택", ["월별", "연도별"])
with col2:
    cmdcode = st.selectbox("📦 품목코드(HS Code)", sorted(data['cmdcode'].unique()))
with col3:
    reporter = st.selectbox("📊 보고국(Reporter)", sorted(data['reporter'].unique()))
with col4:
    period = st.selectbox("📅 기간(YYYYMM)", sorted(data['period'].unique()))

if view_mode == "연도별":
    year = st.selectbox("📆 연도(YYYY)", sorted(data['year'].unique()))


# ------------------------------
# ✅ 4. HS 코드 설명
# ------------------------------
hs_desc = {
    '253090': 'Arsenic sulfides, alunite, pozzuolana, earth colours and other mineral substances, n.e.s.',
    '283691': 'Lithium carbonates',
    '282520': 'Lithium oxide and hydroxide',
    '282739': 'Chlorides (excl. ammonium, calcium, magnesium, aluminium, nickel, and mercury chloride)',
    '282690': 'Fluorosilicates, fluoroaluminates and other complex fluorine salts',
    '282619': 'Fluorides (excl. of aluminium and mercury)',
    '260500': 'Cobalt ores and concentrates',
    '282200': 'Cobalt oxides and hydroxides; commercial cobalt oxides',
    '810520': 'Cobalt mattes and other intermediate products of cobalt metallurgy'
}

if cmdcode in hs_desc:
    st.info(f"🧾 **HS 코드 {cmdcode} 설명:** {hs_desc[cmdcode]}")
else:
    st.warning("❗ 해당 HS 코드의 설명 정보가 등록되어 있지 않습니다.")


# ------------------------------
# ✅ 5. 데이터 필터링 및 지도 생성
# ------------------------------
if view_mode == "월별":
    subset = data[
        (data['period'] == str(period)) &
        (data['cmdcode'] == str(cmdcode)) &
        (data['reporter'] == reporter)
    ].copy()
    title_text = f"{reporter}의 {cmdcode} 수입 (기간: {period}) [log₁₀(무역량)]"

else:
    subset = data[
        (data['year'] == str(year)) &
        (data['cmdcode'] == str(cmdcode)) &
        (data['reporter'] == reporter)
    ].copy()
    subset = subset.groupby(['partner', 'partner_iso3'], as_index=False)['netwgt'].sum()
    title_text = f"{reporter}의 {cmdcode} 수입 (연도: {year}) [log₁₀(무역량)]"


# ------------------------------
# ✅ 6. 지도 시각화
# ------------------------------
if subset.empty:
    st.warning("⚠️ 선택한 조건에 해당하는 데이터가 없습니다.")
else:
    subset['netwgt_log'] = np.log10(subset['netwgt'].replace(0, np.nan))

    fig = px.choropleth(
        subset,
        locations="partner_iso3",
        color="netwgt_log",
        hover_name="partner",
        color_continuous_scale="Viridis",
        title=title_text,
        projection="natural earth"
    )

    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        coloraxis_colorbar=dict(title="log₁₀(무역량)")
    )

    st.plotly_chart(fig, use_container_width=True)


# ------------------------------
# ✅ 7. 출처 표시
# ------------------------------
st.markdown("---")
st.caption("📊 **Source:** UN COMTRADE Database")
st.caption("국가별 교역 규모의 편차가 커, 시각화의 균형을 위해 교역량에 로그 변환(log) 값을 적용하였습니다.")



