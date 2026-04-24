import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
import zipfile
import io
import time
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# 페이지 설정
st.set_page_config(page_title="Financial Risk Dashboard", layout="wide")

# .env 파일 로드 및 API 키 확인
load_dotenv()
API_KEY = os.getenv("DART_API_KEY")

if not API_KEY or API_KEY == "your_api_key_here":
    st.error(".env 파일에 유효한 DART_API_KEY를 설정해주세요.")
    st.stop()

# --- 데이터 수집 관련 함수 (Caching 활용) ---

@st.cache_data
def get_corp_codes():
    """모든 상장사 고유번호 매핑 데이터 패치"""
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return {}
    
    corp_map = {}
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open('CORPCODE.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            for company in root.findall('list'):
                stock_code = company.find('stock_code').text.strip()
                if stock_code:
                    corp_map[stock_code] = {
                        "corp_code": company.find('corp_code').text,
                        "corp_name": company.find('corp_name').text
                    }
    return corp_map

@st.cache_data
def fetch_single_company_data(corp_code, corp_name, stock_code, years):
    """특정 기업의 다년도 데이터 수집"""
    data_list = []
    target_accounts = {
        "매출액": "revenue", "영업이익": "operating_profit", "당기순이익": "net_income",
        "자산총계": "total_assets", "부채총계": "total_liabilities", "자본총계": "total_equity"
    }

    for year in years:
        url = f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json?crtfc_key={API_KEY}&corp_code={corp_code}&bsns_year={year}&reprt_code=11011"
        try:
            res = requests.get(url).json()
            if res.get("status") == "000":
                row = {"기업명": corp_name, "종목코드": stock_code, "사업연도": int(year)}
                items = res.get("list", [])
                for acc_nm_key, field_name in target_accounts.items():
                    val = 0
                    for item in items:
                        if acc_nm_key in item.get("account_nm", "").replace(" ", ""):
                            val = int(item.get("thstrm_amount", "0").replace(",", "").split('.')[0])
                            break
                    row[field_name] = val
                data_list.append(row)
            time.sleep(0.1) # 0.1초 소량의 지연 (Rate limit 방지)
        except:
            continue
    return data_list

def calculate_metrics(df):
    """파생 지표 및 Risk Score 계산"""
    if df.empty: return df
    
    # 기본 지표
    df["부채비율"] = df["total_liabilities"] / df["total_equity"].replace(0, 1)
    df["영업이익률"] = df["operating_profit"] / df["revenue"].replace(0, 1)
    df["순이익률"] = df["net_income"] / df["revenue"].replace(0, 1)
    
    # 성장률 (정렬 후 계산)
    df = df.sort_values(["기업명", "사업연도"])
    df["매출성장률"] = df.groupby("기업명")["revenue"].pct_change()
    df["영업이익성장률"] = df.groupby("기업명")["operating_profit"].pct_change()
    
    # 무한대/결측치 처리
    df = df.replace([float('inf'), float('-inf')], 0).fillna(0)
    
    # --- Risk Score 계산 (정규화) ---
    # 각 지표에 대해 0~1 사이로 정규화 (부채비율은 높을수록 위험하므로 그대로 사용, 이익률/성장률은 낮을수록 위험하므로 1에서 뺌)
    def normalize(series):
        if series.max() == series.min(): return series * 0
        return (series - series.min()) / (series.max() - series.min())

    df["risk_debt"] = normalize(df["부채비율"]) # 높을수록 위험
    df["risk_profit"] = 1 - normalize(df["영업이익률"]) # 낮을수록 위험
    df["risk_growth"] = 1 - normalize(df["매출성장률"]) # 낮을수록 위험
    
    # 가중합 (부채 40%, 수익성 30%, 성장성 30%)
    df["Risk_Score"] = (df["risk_debt"] * 0.4 + df["risk_profit"] * 0.3 + df["risk_growth"] * 0.3) * 100
    return df

# --- 메인 대시보드 로직 ---

st.title("🛡️ 기업 재무 리스크 분석 종합 대시보드")
st.markdown("OpenDART API 실시간 데이터를 기반으로 기업의 건전성을 평가합니다.")

# 대상 기업 정의 (100개사 리스트 - 이전 단계에서 사용한 것과 동일)
TARGET_CODES = [
    "005930", "000660", "373220", "207940", "005380", "000270", "068270", "105560", "055550", "005490",
    "035420", "012330", "028260", "006400", "051910", "086790", "035720", "066570", "138040", "000810",
    "017670", "003550", "034020", "011780", "010130", "032830", "009150", "015760", "000100", "011200",
    "003670", "000720", "018260", "316140", "323410", "010140", "024110", "036570", "086280", "001040",
    "047050", "011070", "051900", "005830", "000880", "004020", "090430", "001570", "096770", "029780",
    "259960", "302440", "010950", "071050", "033780", "001450", "034220", "002790", "042700", "010620",
    "028050", "161390", "000210", "005940", "006800", "030200", "001060", "000670", "011170", "002380",
    "006360", "008930", "128940", "004170", "035250", "023530", "078930", "000120", "004800", "097950",
    "003410", "000990", "012750", "014680", "005440", "011210", "001740", "000240", "267250", "003240",
    "047810", "052690", "000080", "001800", "010120"
]

# 1. 고유번호 매핑 데이터 로드
with st.spinner("기업 정보를 불러오는 중..."):
    corp_codes = get_corp_codes()

# 2. 사이드바 - 기업 검색 및 선택
st.sidebar.header("🔍 기업 필터링")
search_query = st.sidebar.text_input("기업명 검색", "")

# 검색어에 따른 리스트 필터링
option_list = []
for code in TARGET_CODES:
    if code in corp_codes:
        name = corp_codes[code]["corp_name"]
        if search_query.lower() in name.lower():
            option_list.append(f"{name} ({code})")

if not option_list:
    st.warning("검색 결과가 없습니다.")
    st.stop()

selected_option = st.sidebar.selectbox("대상 기업 선택", option_list)
selected_stock_code = selected_option.split("(")[1].replace(")", "").strip()
selected_corp_info = corp_codes[selected_stock_code]

# 3. 데이터 로드 (최근 3개년 수집)
years_to_fetch = ["2022", "2023", "2024"]
with st.spinner(f"{selected_option} 데이터 수집 중..."):
    # 선택된 기업 데이터 + 전체 랭킹용 샘플 데이터 (성능상 랭킹은 주요 20개로 제한하여 실시간 확인)
    # 실제 100개를 실시간 수집하기엔 스트림릿 대기시간이 길어지므로, 캐시를 십분 활용합니다.
    
    raw_list = []
    # 선택된 기업은 반드시 수집
    raw_list.extend(fetch_single_company_data(selected_corp_info["corp_code"], selected_corp_info["corp_name"], selected_stock_code, years_to_fetch))
    
    # 랭킹용 및 비교용 데이터 (주요 기업 20개 선정하여 병렬 수집 느낌으로 처리)
    comparison_codes = TARGET_CODES[:20] 
    for c_code in comparison_codes:
        if c_code != selected_stock_code and c_code in corp_codes:
            raw_list.extend(fetch_single_company_data(corp_codes[c_code]["corp_code"], corp_codes[c_code]["corp_name"], c_code, years_to_fetch))

df_all = calculate_metrics(pd.DataFrame(raw_list))

# --- 대시보드 표시 ---

# 현재 선택된 기업의 최신 데이터
df_selected = df_all[df_all["종목코드"] == selected_stock_code].sort_values("사업연도", ascending=False)
if df_selected.empty:
    st.error("데이터를 불러오지 못했습니다.")
    st.stop()
    
latest = df_selected.iloc[0]

# 상단 KPI 카드
cols = st.columns(4)
cols[0].metric("Risk Score", f"{latest['Risk_Score']:.1f} / 100", help="낮을수록 안전, 높을수록 위험")
cols[1].metric("부채비율", f"{latest['부채비율']*100:.1f}%")
cols[2].metric("영업이익률", f"{latest['영업이익률']*100:.1f}%")
cols[3].metric("매출성장률", f"{latest['매출성장률']*100:.1f}%")

st.divider()

# 메인 차트 영역
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 리스크 스코어 분석")
    # 게이지 차트
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = latest['Risk_Score'],
        title = {'text': "위험도 측정"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps' : [
                {'range': [0, 30], 'color': "green"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "red"}],
            'threshold' : {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': latest['Risk_Score']}
        }
    ))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col2:
    st.subheader("📈 실적 추이")
    # 시계열 라인 차트
    fig_line = px.line(df_selected.sort_values("사업연도"), x="사업연도", y=["revenue", "operating_profit", "net_income"],
                       title=f"{latest['기업명']} 수익성 추이", labels={"value": "금액 (원)", "variable": "항목"},
                       markers=True)
    fig_line.update_layout(xaxis=dict(tickmode='linear'))
    st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# 하단 랭킹 영역
st.subheader("🏆 주요 기업 Risk Score 랭킹 (TOP 10)")
# 랭킹 산출 (최신 연도 기준)
df_latest_all = df_all[df_all["사업연도"] == 2024].sort_values("Risk_Score", ascending=False)
fig_rank = px.bar(df_latest_all.head(10), x="Risk_Score", y="기업명", orientation='h',
                  color="Risk_Score", color_continuous_scale="Reds",
                  title="2024년 기준 위험도가 높은 기업 순위")
fig_rank.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_rank, use_container_width=True)

# 데이터 테이블 상세 보기
if st.checkbox("상세 재무 데이터 보기"):
    st.dataframe(df_selected[["사업연도", "revenue", "operating_profit", "net_income", "total_assets", "부채비율", "Risk_Score"]], use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("데이터 출처: OpenDART (실시간 API)")
st.sidebar.caption("※ Risk Score는 부채비율, 수익성, 성장성을 기반으로 산출된 가상의 지표입니다.")
