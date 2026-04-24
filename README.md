# 기업 리스크 분석 프로젝트 (Financial Risk Dashboard)

이 프로젝트는 OpenDART API를 통해 얻은 국내 주요 상장기업의 재무 데이터를 수집하고, 기업의 건전성 및 리스크를 분석하기 위한 파생 지표를 산출하는 시스템입니다.

## 1. 프로젝트 구조
- `dashboard.py`: Streamlit 기반 실시간 리스크 분석 대시보드
- `src/`: 소스 코드 폴더
    - `utils.py`: API 공통 유틸리티
    - `collector.py`: OpenDART API 데이터 수집기 (CLI용)
    - `analyzer.py`: 재무 리스크 지표 분석기 (CLI용)
- `data/`: 분석된 통합 데이터 저장 폴더 (CLI 실행 시 생성)
- `docs/`: API 가이드 및 관련 문서
- `.env`: API 인증키 설정 파일

## 2. 필수 요구 사항
- Python 3.9+
- [OpenDART API Key](https://opendart.fss.or.kr/mng/userApiKeyListView.do) 필수

## 3. 시작하기

### 3.1 환경 설정
1. `.env` 파일을 열어 `DART_API_KEY` 항목에 발급받은 실제 인증키를 입력합니다.
2. 가상환경을 활성화하고 패키지를 설치합니다 (이미 설치된 경우 생략 가능).
```bash
source .venv/bin/activate
uv pip install streamlit plotly pandas requests python-dotenv
```

### 3.2 실시간 대시보드 실행
아래 명령어를 통해 웹 기반 대시보드를 실행할 수 있습니다.
```bash
streamlit run dashboard.py
```
- 실행 후 브라우저에서 `http://localhost:8501` 주소로 접속하면 대시보드를 확인할 수 있습니다.

### 3.3 대시보드 주요 기능
- **실시간 데이터 수집**: OpenDART API를 통해 기업의 최신 재무 데이터를 즉시 가져옵니다 (Streamlit Cache 지원).
- **기업 검색 및 선택**: 시가총액 상위 100개사 중 원하는 기업을 검색하여 리스크를 분석합니다.
- **Risk Score 시각화**: 부채비율, 수익성, 성장성을 바탕으로 산출된 위험도를 게이지 차트로 보여줍니다.
- **시계열 추이**: 최근 3개년의 수익성 변화를 Plotly 차트로 제공합니다.
- **리스크 랭킹**: 분석 대상 기업 중 상대적으로 위험도가 높은 기업 순위를 제공합니다.

### 3.4 데이터 수집 및 분석 (CLI 버전)
대시보드 외에 결과 파일(CSV)이 필요한 경우 순서대로 실행합니다.

1. **데이터 수집**: 주요 상장기업 100개의 최근 3개년 재무 데이터를 수집합니다.
```bash
python src/collector.py
```
- 결과 파일: `data/corporate_financials.csv` (분석기 실행 후 통합됨)

2. **지표 분석 및 통합**: 수집된 데이터를 바탕으로 리스크 지표를 계산하고 하나의 파일로 통합합니다.
```bash
python src/analyzer.py
```
- 최종 통합 파일: `data/corporate_analysis.csv`
- 포함 지표: 원본 재무 데이터 + 부채비율, 영업이익률, 순이익률, 매출성장률, 영업이익성장률

## 4. 수집 대상 기업
- 삼성전자, SK하이닉스, 현대자동차 등 국내 시가총액 상위 주요 상장기업 **총 100개사**
