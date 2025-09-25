# utils/stock_classifier.py

import yfinance as yf
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import db_handler

# --- [수정된 부분] ---
# 순환 참조의 원인이었던 아래 라인을 삭제합니다.
# from sentiment_analyzer import analyze_and_update_sentiment
# --- [수정된 부분 끝] ---


def get_stock_factors(ticker_symbol, conn):
    """지정된 티커의 5대 팩터(가치, 성장, 퀄리티, 모멘텀, 감성) 점수를 계산합니다."""
    stock = yf.Ticker(ticker_symbol)
    info = stock.info

    scores = {
        'Value': 0, 'Growth': 0, 'Quality': 0, 'Momentum': 0, 'Sentiment': 0
    }

    # 1. 가치(Value)
    pe_ratio = info.get('trailingPE')
    pb_ratio = info.get('priceToBook')
    if pe_ratio is not None and 0 < pe_ratio < 15: scores['Value'] += 1
    if pb_ratio is not None and 0 < pb_ratio < 2: scores['Value'] += 1

    # 2. 성장(Growth)
    revenue_growth = info.get('revenueGrowth')
    earnings_growth = info.get('earningsQuarterlyGrowth')
    if revenue_growth is not None and revenue_growth > 0.1: scores['Growth'] += 1
    if earnings_growth is not None and earnings_growth > 0.1: scores['Growth'] += 1

    # 3. 퀄리티(Quality)
    roe = info.get('returnOnEquity')
    debt_to_equity = info.get('debtToEquity')
    if roe is not None and roe > 0.15: scores['Quality'] += 1
    if debt_to_equity is not None and debt_to_equity < 100: scores['Quality'] += 1

    # 4. 모멘텀(Momentum)
    fifty_two_week_high = info.get('fiftyTwoWeekHigh')
    fifty_two_week_low = info.get('fiftyTwoWeekLow')
    current_price = info.get('regularMarketPreviousClose')
    if all([fifty_two_week_high, fifty_two_week_low, current_price]):
        if current_price > (fifty_two_week_high - fifty_two_week_low) * 0.7 + fifty_two_week_low:
            scores['Momentum'] += 1
    if info.get('fiftyDayAverage') is not None and current_price > info.get('fiftyDayAverage'):
        scores['Momentum'] += 1

    # 5. 감성(Sentiment)
    try:
        sql = f"SELECT AVG(sentiment_score) FROM stock_news WHERE ticker = '{ticker_symbol}' AND published_at >= NOW() - INTERVAL '30 days';"
        sentiment_df = pd.read_sql(sql, conn)
        if not sentiment_df.empty and sentiment_df.iloc[0,0] is not None:
            avg_sentiment = sentiment_df.iloc[0,0]
            if avg_sentiment > 0.2:
                scores['Sentiment'] += 1
    except Exception as e:
        print(f"  - {ticker_symbol} 감성 점수 계산 중 오류: {e}")

    styles = [factor for factor, score in scores.items() if score > 0]
    return ','.join(styles) if styles else 'N/A'

def classify_stocks_pro():
    """DB의 모든 주식을 전문가 수준의 5대 팩터로 분류하고 업데이트합니다."""
    print("📈 전문가용 주식 스타일 분류를 시작합니다 (5대 팩터 기반)...")
    
    conn = db_handler.get_db_connection()
    if not conn: return

    try:
        # --- [수정된 부분] ---
        # 이 파일에서 직접 감성 분석을 호출하는 코드를 삭제했습니다.
        # --- [수정된 부분 끝] ---
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT ticker FROM stock_master WHERE is_active = TRUE")
            tickers = [row[0] for row in cursor.fetchall()]

            print(f"총 {len(tickers)}개 종목에 대한 분류를 진행합니다.")
            update_count = 0
            for ticker_symbol in tickers:
                try:
                    style_str = get_stock_factors(ticker_symbol, conn)
                    update_sql = "UPDATE stock_master SET style = %s WHERE ticker = %s"
                    cursor.execute(update_sql, (style_str, ticker_symbol))
                    print(f"  - {ticker_symbol}: {style_str}")
                    update_count += 1
                except Exception as e:
                    print(f"  - {ticker_symbol} 처리 중 오류 발생 (데이터 부족 등): {e}")

            conn.commit()
            print(f"\n✅ 총 {update_count}개 종목의 스타일 분류 및 업데이트 완료!")

    except Exception as e:
        print(f"❌ 전체 프로세스 중 오류 발생: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    classify_stocks_pro()