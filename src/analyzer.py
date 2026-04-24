import pandas as pd
import os

def calculate_risk_features():
    """수집된 재무 데이터를 기반으로 리스크 분석 지표를 계산합니다."""
    file_path = "data/corporate_financials.csv"
    if not os.path.exists(file_path):
        print(f"오류: {file_path} 파일이 존재하지 않습니다. 수집기를 먼저 실행하세요.")
        return

    df = pd.read_csv(file_path)

    # 1. 안정성 및 수익성 지표 계산
    # 부채비율 = 부채총계 / 자본총계
    df["부채비율"] = df["부채총계"] / df["자본총계"]
    
    # 영업이익률 = 영업이익 / 매출액
    df["영업이익률"] = df["영업이익"] / df["매출액"]
    
    # 순이익률 = 당기순이익 / 매출액
    df["순이익률"] = df["당기순이익"] / df["매출액"]

    # 2. 성장성 지표 계산 (전년 데이터 필요)
    # 기업명과 사업연도로 정렬
    df = df.sort_values(by=["기업명", "사업연도"])

    # 매출성장률 = (당기 매출액 - 전기 매출액) / 전기 매출액
    df["매출성장률"] = df.groupby("기업명")["매출액"].pct_change()

    # 영업이익성장률 = (당기 영업이익 - 전기 영업이익) / 전기 영업이익
    df["영업이익성장률"] = df.groupby("기업명")["영업이익"].pct_change()

    # 무한대(inf)나 결측치 처리
    df = df.replace([float('inf'), float('-inf')], 0).fillna(0)

    # 분석 결과 통합 저장 (원본 + 분석 지표)
    output_path = "data/corporate_analysis.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"통합 데이터 생성 완료: {output_path}")

    # 중간 원본 파일 삭제 (선택 사항이나 깔끔한 관리를 위해 삭제 권장)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"중간 파일 삭제 완료: {file_path}")

if __name__ == "__main__":
    calculate_risk_features()
