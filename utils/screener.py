# utils/screener.py

import sys
import os
import pandas as pd

# 프로젝트 최상위 폴더를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import db_handler

def screen_stocks():
    """
    데이터베이스의 모든 주식을 평가하여 투자에 가장 유망한 상위 5개 종목을 추천합니다.
    평가 기준: 가치, 성장, 퀄리티, 모멘텀 점수의 총합
    """
    print("\n🔬 전체 시장을 스캔하여 유망 종목을 탐색합니다 (Screener)...")
    
    conn = db_handler.get_db_connection()
    if not conn:
        print("❌ 스크리너 실행을 위해 데이터베이스 연결이 필요합니다.")
        return None

    try:
        # style 컬럼에 저장된 팩터 점수를 가져옵니다.
        sql = "SELECT ticker, company_name, style FROM stock_master WHERE is_active = TRUE;"
        df = pd.read_sql(sql, conn)

        if df.empty:
            print("⚠️ 평가할 주식 정보가 없습니다. collector.py를 먼저 실행하세요.")
            return None

        def calculate_score(style_str):
            # 'Value,Growth' 같은 문자열을 분리하여 개수를 셉니다.
            if style_str and style_str != 'N/A':
                return len(style_str.split(','))
            return 0

        df['score'] = df['style'].apply(calculate_score)
        
        # 점수가 높은 순으로 정렬하고, 상위 5개 종목만 선택합니다.
        top_stocks = df.sort_values(by='score', ascending=False).head(5)

        print("\n--- 🔬 AI 스크리너 추천 Top 5 ---")
        if top_stocks.empty or top_stocks['score'].max() == 0:
            print("오늘은 특별히 추천할 만한 종목을 찾지 못했습니다.")
            return []
        
        for _, row in top_stocks.iterrows():
            print(f"  - [{row['ticker']}] {row['company_name']} (Score: {row['score']}, Style: {row['style']})")
        
        return top_stocks['ticker'].tolist()

    except Exception as e:
        print(f"❌ 스크리닝 중 오류 발생: {e}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # stock_classifier를 먼저 실행하여 style 정보를 최신 상태로 유지해야 합니다.
    # from utils import stock_classifier
    # stock_classifier.classify_stocks_pro()
    
    recommended_tickers = screen_stocks()
    if recommended_tickers:
        print("\n추천 종목에 대한 상세 분석을 시작할 수 있습니다.")