# [OpenDART] 고유번호 (Corp Code) API 개발 가이드

이 문서는 OpenDART에서 제공하는 **고유번호(Corp Code)** API에 대한 상세 개발 가이드입니다. 고유번호는 OpenDART의 거의 모든 다른 API를 호출할 때 필수적으로 사용되는 식별자로, 공시대상회사의 정적 정보를 매핑하는 데 사용됩니다.

## 1. 기본 정보

| 항목 | 상세 내용 |
| :--- | :--- |
| **메서드** | GET |
| **요청 URL** | `https://opendart.fss.or.kr/api/corpCode.xml` |
| **인코딩** | UTF-8 |
| **출력 포맷** | Zip FILE (binary) |

> [!IMPORTANT]
> 이 API는 다른 API와 달리 결과가 JSON이 아닌 **정규화된 XML 파일들이 포함된 ZIP 파일** 형태로 제공됩니다. 브라우저 테스트 시 ZIP 파일로 다운로드되며, 개발 단계에서는 이를 다운로드하여 압축 해제 후 파싱하는 과정이 필요합니다.

---

## 2. 요청 인자 (Parameters)

| 요청키 | 명칭 | 타입 | 필수여부 | 값 설명 |
| :--- | :--- | :--- | :---: | :--- |
| `crtfc_key` | API 인증키 | STRING(40) | Y | 사용자가 발급받은 40자리의 인증키 |

---

## 3. 응답 결과 (Response Fields)

응답받은 ZIP 파일 내의 `CORPCODE.xml` 구성 요소입니다.

| 응답키 | 명칭 | 출력 설명 |
| :--- | :--- | :--- |
| `result` | 최상위 노드 | 전체 결과의 루트 |
| `list` | 리스트 노드 | 개별 회사 정보의 반복 단위 |
| `corp_code` | 고유번호 | **가장 중요한 필드.** 공시대상회사의 고유번호 (8자리) |
| `corp_name` | 정식명칭 | 회사의 정식 국문 명칭 |
| `corp_eng_name` | 영문 정식명칭 | 회사의 정식 영문 명칭 |
| `stock_code` | 종목코드 | 상장회사인 경우 주식의 종목코드 (6자리) |
| `modify_date` | 최종변경일자 | 고유번호 정보가 마지막으로 변경된 날짜 (YYYYMMDD) |

---

## 4. 메시지 설명 (Status Codes)

응답 상태에 따른 코드 및 메시지 설명입니다.

| 코드 | 메시지 설명 | 조치 사항 |
| :--- | :--- | :--- |
| `000` | 정상 | 정상 요청 완료 |
| `010` | 등록되지 않은 키입니다. | 인증키 발급 여부 확인 |
| `011` | 사용할 수 없는 키입니다. | 인증키의 유효성(중지 여부) 확인 |
| `012` | 접근할 수 없는 IP입니다. | OpenDART 설정에서 허용 IP 확인 |
| `013` | 조회된 데이타가 없습니다. | 요청 조건에 맞는 데이터 부재 |
| `020` | 요청 제한을 초과하였습니다. | 일일 요청 건수(보통 2만건) 확인 |
| `100` | 필드의 부적절한 값입니다. | 파라미터 오타 및 타입 확인 |
| `800` | 시스템 점검 중입니다. | 점검 종료 후 재시도 |

---

## 5. 개발 참고 사항 및 활용 팁

### 5.1 고유번호의 중요성
상장사의 경우 6자리 `종목코드(Stock Code)`를 사용하지만, OpenDART API는 비상장사를 포함하여 모든 기업을 관리하기 위해 **8자리 고유번호(`corp_code`)**를 고유 식별자로 채택하고 있습니다. 따라서 대다수의 데이터 요청 API는 `corp_code`를 필수 인자로 요구합니다.

### 5.2 데이터 업데이트 정책
고유번호 데이터는 매일 오전 0시를 기준으로 갱신됩니다. 따라서 개발 시 매번 이 API를 호출하기보다는, **주기적으로(예: 1일 1회) 다운로드하여 로컬 DB나 파일 시스템에 캐싱**해 두고 사용하는 방식을 강력히 권장합니다. 매번 30,000개가 넘는 기업 리스트를 다운로드하는 것은 API 호출 제약(쿼터) 낭비일 뿐만 아니라 서비스 성능에도 영향을 줄 수 있습니다.

### 5.3 파싱 예시 (Python 가상 코드)
```python
import requests
import zipfile
import io
import xml.etree.ElementTree as ET

def update_corp_codes(api_key):
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            with z.open('CORPCODE.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                for company in root.findall('list'):
                    code = company.find('corp_code').text
                    name = company.find('corp_name').text
                    # 로컬 DB에 저장 로직
```

### 5.4 주의사항 (Chrome/Edge 환경)
Chrome이나 Edge 브라우저에서 직접 테스트 시, 브라우저가 파일의 성격을 오판하여 `.xml` 확장자로 저장하려 할 수 있습니다. 이럴 경우 확장자를 `.zip`으로 강제 변경하면 정상적으로 압축을 해제할 수 있습니다.
