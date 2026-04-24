import pandas as pd
import requests
import os
import time
from utils import API_KEY, get_corp_codes, format_amount

# 대상 기업 (시가총액 상위 100개 주요 기업 리스트)
TARGET_COMPANIES = {
    "005930": "삼성전자", "000660": "SK하이닉스", "373220": "LG엔솔", "207940": "삼성바이오",
    "005380": "현대차", "000270": "기아", "068270": "셀트리온", "105560": "KB금융",
    "055550": "신한지주", "005490": "POSCO홀딩스", "035420": "NAVER", "012330": "현대모비스",
    "028260": "삼성물산", "006400": "삼성SDI", "051910": "LG화학", "086790": "하나금융",
    "035720": "카카오", "066570": "LG전자", "138040": "메리츠금융", "000810": "삼성화재",
    "017670": "SK텔레콤", "003550": "LG", "034020": "두산에너빌리티", "000100": "유한양행",
    "010130": "고려아연", "032830": "삼성생명", "009150": "삼성전기", "015760": "한국전력",
    "011200": "HMM", "003670": "포스코퓨처엠", "000720": "현대건설", "018260": "삼성SDS",
    "316140": "우리금융", "323410": "카카오뱅크", "010140": "삼성중공업", "024110": "IBK기업은행",
    "036570": "엔씨소프트", "086280": "현대글로비스", "001040": "CJ", "047050": "포스코인터",
    "011070": "LG이노텍", "051900": "LG생활건강", "005830": "DB손해보험", "000880": "한화",
    "004020": "현대제철", "090430": "아모레퍼시픽", "001570": "금양", "096770": "SK이노베이션",
    "029780": "삼성카드", "259960": "크래프톤", "302440": "SK바이오사이언스", "010950": "S-Oil",
    "071050": "한국금융지주", "033780": "KT&G", "001450": "현대해상", "034220": "LG디스플레이",
    "002790": "아모레G", "042700": "한미반도체", "010620": "현대미포조선", "028050": "삼성엔지니어링",
    "161390": "한국타이어", "000210": "DL", "005940": "NH투자증권", "006800": "미래에셋증권",
    "030200": "KT", "001060": "JW중외제약", "000670": "영풍", "011170": "롯데케미칼",
    "002380": "KCC", "006360": "GS건설", "008930": "한미사이언스", "128940": "한미약품",
    "004170": "신세계", "035250": "강원랜드", "023530": "롯데쇼핑", "078930": "GS",
    "001120": "LX인터내셔널", "000120": "CJ대한통운", "004800": "효성", "097950": "CJ제일제당",
    "003410": "쌍용C&E", "000990": "DB하이텍", "012750": "에스원", "014680": "한솔케미칼",
    "005440": "현대그린푸드", "011210": "현대위아", "001740": "SK네트웍스", "000240": "한국앤컴퍼니",
    "267250": "HD현대", "003240": "태광산업", "047810": "한국항공우주", "052690": "한전기술",
    "000080": "하이트진로", "001800": "오리온홀딩스", "001120": "LX인터내셔널", "011780": "금호석유",
    "005935": "삼성전자우", "010120": "LS", "000990": "DB하이텍", "004020": "현대제철"
}

# 최근 3개년
YEARS = ["2022", "2023", "2024"]


def fetch_financial_data():
    """상장기업의 재무 데이터를 수집하여 CSV로 저장합니다."""
    print("고유번호 맵을 생성 중입니다...")
    corp_code_map = get_corp_codes()
    
    all_data = []
    
    # 필요한 계정명 정의
    target_accounts = {
        "매출액": "revenue",
        "영업이익": "operating_profit",
        "당기순이익": "net_income",
        "자산총계": "total_assets",
        "부채총계": "total_liabilities",
        "자본총계": "total_equity"
    }

    for stock_code, corp_name in TARGET_COMPANIES.items():
        corp_code = corp_code_map.get(stock_code)
        if not corp_code:
            print(f"{corp_name}({stock_code})의 고유번호를 찾을 수 없습니다.")
            continue
        
        for year in YEARS:
            print(f"{corp_name} {year}년 데이터 수집 중...")
            # 단일회사 주요계정 API (11011: 사업보고서)
            url = f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json?crtfc_key={API_KEY}&corp_code={corp_code}&bsns_year={year}&reprt_code=11011"
            
            response = requests.get(url)
            result = response.json()
            
            if result.get("status") == "000":
                items = result.get("list", [])
                
                # 한 기업/연도에 대한 데이터 정리
                row = {
                    "기업명": corp_name,
                    "종목코드": stock_code,
                    "사업연도": year,
                    "보고서구분": "사업보고서"
                }
                
                # 초기값 설정
                for key in target_accounts.values():
                    row[key] = 0
                
                # API 결과에서 해당 계정 추출
                for item in items:
                    acc_nm = item.get("account_nm", "").replace(" ", "")
                    for target_nm, target_key in target_accounts.items():
                        if target_nm in acc_nm:
                            # 이미 데이터가 들어있다면 무시 (중복 방지, CFS 우선)
                            if row[target_key] == 0:
                                row[target_key] = format_amount(item.get("thstrm_amount", "0"))
                
                all_data.append(row)
            else:
                print(f"오류 발생 ({corp_name} {year}): {result.get('message')}")
            
            # API 과부하 방지
            time.sleep(0.5)

    df = pd.DataFrame(all_data)
    
    # 컬럼명 한글로 변경
    df.columns = ["기업명", "종목코드", "사업연도", "보고서구분", 
                  "매출액", "영업이익", "당기순이익", "자산총계", "부채총계", "자본총계"]
    
    # data 폴더 생성 및 저장
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/corporate_financials.csv", index=False, encoding="utf-8-sig")
    print("수집 완료: data/corporate_financials.csv")

if __name__ == "__main__":
    fetch_financial_data()
