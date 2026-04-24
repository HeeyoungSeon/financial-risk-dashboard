import os
import requests
import zipfile
import io
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
API_KEY = os.getenv("DART_API_KEY")

def get_corp_codes():
    """
    OpenDART에서 고유번호(corp_code) ZIP 파일을 다운로드하여 
    전체 기업의 {종목코드: 고유번호} 매핑 딕셔너리를 반환합니다.
    """
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception("OpenDART API 호출에 실패했습니다.")
    
    corp_code_map = {}
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open('CORPCODE.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            for company in root.findall('list'):
                stock_code = company.find('stock_code').text.strip()
                if stock_code:  # 상장사만 필터링
                    corp_code_map[stock_code] = company.find('corp_code').text
    return corp_code_map

def format_amount(amount_str):
    """문자열 형태의 금액을 정수로 변환 (공백/콤마 제거)"""
    if not amount_str or amount_str == '-':
        return 0
    try:
        return int(amount_str.replace(',', '').split('.')[0])
    except:
        return 0
