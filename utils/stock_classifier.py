# utils/stock_classifier.py

import yfinance as yf
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# db_handler를 직접 임포트하도록 수정
from utils import db_handler

# 상위 폴더를 경로에 추가
def get_stock_factors(ticker_symbol, conn): # db connection을 인자로 받도록 수정
    """지정된 티커의 5대 팩터(가치, 성장, 퀄리티, 모멘텀, 감성) 점수를 계산합니다."""
    stock = yf.Ticker(ticker_symbol)
    info = stock.info

    scores = {
        'Value': 0,
        'Growth': 0,
        'Quality': 0,
        'Momentum': 0,
        'Sentiment': 0 # Sentiment 팩터 추가
    }

    # ... (기존의 Value, Growth, Quality, Momentum 점수 계산 로직은 동일) ...

    # 1. 가치(Value) 팩터 점수
    pe_ratio = info.get('trailingPE')
    pb_ratio = info.get('priceToBook')
    if pe_ratio is not None and 0 < pe_ratio < 15: scores['Value'] += 1
    if pb_ratio is not None and 0 < pb_ratio < 2: scores['Value'] += 1

    # 2. 성장(Growth) 팩터 점수
    revenue_growth = info.get('revenueGrowth')
    earnings_growth = info.get('earningsQuarterlyGrowth')
    if revenue_growth is not None and revenue_growth > 0.1: scores['Growth'] += 1
    if earnings_growth is not None and earnings_growth > 0.1: scores['Growth'] += 1

    # 3. 퀄리티(Quality) 팩터 점수
    roe = info.get('returnOnEquity')
    debt_to_equity = info.get('debtToEquity')
    if roe is not None and roe > 0.15: scores['Quality'] += 1
    if debt_to_equity is not None and debt_to_equity < 100: scores['Quality'] += 1

    # 4. 모멘텀(Momentum) 팩터 점수
    fifty_two_week_high = info.get('fiftyTwoWeekHigh')
    fifty_two_week_low = info.get('fiftyTwoWeekLow')
    current_price = info.get('regularMarketPreviousClose')
    if all([fifty_two_week_high, fifty_two_week_low, current_price]):
        if current_price > (fifty_two_week_high - fifty_two_week_low) * 0.7 + fifty_two_week_low:
            scores['Momentum'] += 1
    if info.get('fiftyDayAverage') is not None and current_price > info.get('fiftyDayAverage'):
        scores['Momentum'] += 1

    # 5. (신규) 감성(Sentiment) 팩터 점수
    try:
        # 최근 30일간의 뉴스 감성 점수 평균을 계산
        sql = f"SELECT AVG(sentiment_score) FROM stock_news WHERE ticker = '{ticker_symbol}' AND published_at >= NOW() - INTERVAL '30 days';"
        sentiment_df = pd.read_sql(sql, conn)
        if not sentiment_df.empty and sentiment_df.iloc[0,0] is not None:
            avg_sentiment = sentiment_df.iloc[0,0]
            # 평균 점수가 0.2 이상이면 긍정적으로 판단 (임계값은 조정 가능)
            if avg_sentiment > 0.2:
                scores['Sentiment'] += 1
    except Exception as e:
        print(f"  - {ticker_symbol} 감성 점수 계산 중 오류: {e}")


    styles = [factor for factor, score in scores.items() if score > 0]

    return ','.join(styles) if styles else 'N/A'

def classify_stocks_pro():
    """DB의 모든 주식을 전문가 수준의 5대 팩터로 분류하고 업데이트합니다."""
    print("📈 전문가용 주식 스타일 분류를 시작합니다 (5대 팩터 기반)...")
    conn = db_handler.get_db_connection() # get_db_connection()으로 수정
    if not conn: return

    try:
        # sentiment_analyzer를 먼저 실행하여 모든 뉴스의 감성 점수를 계산
        print("🎭 최신 뉴스에 대한 감성 분석을 먼저 실행합니다...")
        # sentiment_analyzer 모듈과 함수를 직접 임포트
        from sentiment_analyzer import analyze_and_update_sentiment
        analyze_and_update_sentiment()


        with conn.cursor() as cursor:
            cursor.execute("SELECT ticker FROM stock_master WHERE is_active = TRUE")
            tickers = [row[0] for row in cursor.fetchall()]

            print(f"총 {len(tickers)}개 종목에 대한 분류를 진행합니다.")

            update_count = 0
            for ticker_symbol in tickers:
                try:
                    # connection을 get_stock_factors 함수에 전달
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