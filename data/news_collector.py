import sys
import os
import yfinance as yf
from datetime import datetime
import psycopg2

# 프로젝트 최상위 폴더를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import db_handler

def fetch_and_store_yf_news(ticker):
    """yfinance를 통해 특정 종목의 뉴스를 가져와 DB에 저장합니다."""
    print(f"\n📰 '{ticker}'에 대한 뉴스 수집을 시작합니다 (from yfinance)...")
    
    conn = None
    try:
        stock = yf.Ticker(ticker)
        news_list = stock.news
        
        if not news_list:
            print(f"'{ticker}'에 대한 뉴스를 찾을 수 없습니다.")
            return

        conn = db_handler.get_db_connection()
        with conn.cursor() as cursor:
            new_news_count = 0
            for news_item in news_list:
                # 필수 정보인 'title'과 'link'가 없는 뉴스는 건너뜀
                if not news_item.get('title') or not news_item.get('link'):
                    continue

                sql = """
                INSERT INTO stock_news (ticker, published_at, title, url, source_name)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
                """
                # yfinance는 타임스탬프(초 단위)로 시간을 제공
                published_time = datetime.fromtimestamp(news_item['providerPublishTime'])
                
                data = (
                    ticker,
                    published_time,
                    news_item['title'],
                    news_item['link'],
                    news_item.get('publisher') # 출처는 'publisher' 키에 있음
                )
                cursor.execute(sql, data)
                # 실제로 새로운 행이 추가되었는지 확인
                if cursor.rowcount > 0:
                    new_news_count += 1

            conn.commit()
        print(f"✅ '{ticker}' 뉴스 {len(news_list)}건 처리 완료 (신규 저장: {new_news_count}건).")

    except Exception as e:
        print(f"❌ '{ticker}' 뉴스 저장 중 오류 발생: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    conn = db_handler.get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT ticker FROM stock_master WHERE is_active = TRUE")
                tickers = [row[0] for row in cursor.fetchall()]
            
            for ticker in tickers:
                fetch_and_store_yf_news(ticker)

        except Exception as e:
            print(f"❌ DB에서 티커 목록을 가져오는 중 오류 발생: {e}")
        finally:
            conn.close()