import sys
import os
import requests
import time
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values

# 프로젝트 최상위 폴더를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import db_handler
from config import FINNHUB_API_KEY # 새로 추가한 FinnHub 키를 불러옵니다.

def get_all_tickers(conn):
    """DB에서 수집할 모든 활성 티커 목록을 가져옵니다."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT ticker FROM stock_master WHERE is_active = TRUE")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ DB에서 티커 목록을 가져오는 중 오류 발생: {e}")
        return []

def fetch_finnhub_news_for_all_tickers(tickers):
    """
    모든 티커에 대한 뉴스를 FinnHub API를 통해 가져와 리스트에 저장합니다.
    API 요청 제한(분당 60회)을 준수하기 위해 요청 사이에 딜레이를 줍니다.
    """
    all_news_data = []
    to_date = datetime.now()
    from_date = to_date - timedelta(days=365) # 최근 1년치 뉴스 검색
    
    print(f"\n📰 총 {len(tickers)}개 종목의 뉴스 수집을 시작합니다 (from FinnHub)...")

    for i, ticker in enumerate(tickers):
        print(f"({i+1}/{len(tickers)}) '{ticker}' 뉴스 수집 중...")
        try:
            url = 'https://finnhub.io/api/v1/company-news'
            params = {
                'symbol': ticker,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'token': FINNHUB_API_KEY
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            articles = response.json()

            for article in articles:
                # 필수 정보가 없으면 건너뜀
                if not all(k in article for k in ['headline', 'url', 'source', 'datetime']):
                    continue
                
                # DB에 저장할 형태로 데이터 가공 (튜플)
                all_news_data.append((
                    ticker,
                    datetime.fromtimestamp(article['datetime']),
                    article['headline'],
                    article['url'],
                    article['source']
                ))
            
            # API 요청 제한을 피하기 위해 각 요청 후 1초 대기
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"  ❌ '{ticker}' 뉴스 요청 실패: {e}")
        except Exception as e:
            print(f"  ❌ '{ticker}' 처리 중 알 수 없는 오류: {e}")

    print(f"\n✅ 총 {len(all_news_data)}개의 뉴스 기사를 성공적으로 수집했습니다.")
    return all_news_data

def bulk_insert_news(conn, news_data):
    """
    수집된 모든 뉴스 데이터를 DB에 한 번에 효율적으로 삽입합니다.
    삽입 전 테이블을 깨끗하게 비웁니다.
    """
    if not news_data:
        print("💡 DB에 저장할 새로운 뉴스가 없습니다.")
        return

    print("\n⏳ 데이터베이스에 뉴스 저장을 시작합니다...")
    with conn.cursor() as cursor:
        try:
            # 1. 기존 데이터를 모두 삭제 (가장 확실한 방법)
            print("  - 기존 뉴스 데이터를 삭제합니다...")
            cursor.execute("TRUNCATE TABLE stock_news RESTART IDENTITY;")

            # 2. 수집한 모든 데이터를 한 번의 SQL로 삽입 (매우 효율적)
            print(f"  - {len(news_data)}개의 신규 뉴스를 삽입합니다...")
            sql = """
            INSERT INTO stock_news (ticker, published_at, title, url, source_name)
            VALUES %s
            ON CONFLICT (url) DO NOTHING;
            """
            execute_values(cursor, sql, news_data)
            
            conn.commit()
            print(f"✅ 데이터베이스 저장 완료! (총 {cursor.rowcount}건 신규 저장)")

        except Exception as e:
            print(f"❌ 데이터베이스 저장 중 심각한 오류 발생: {e}")
            conn.rollback()

if __name__ == "__main__":
    if not FINNHUB_API_KEY or FINNHUB_API_KEY == "방금 FinnHub에서 발급받은 API 키":
        print("🚨 [에러] config.py 파일에 FINNHUB_API_KEY를 설정해주세요!")
    else:
        db_conn = db_handler.get_db_connection()
        if db_conn:
            try:
                # 1. DB에서 티커 목록 가져오기
                ticker_list = get_all_tickers(db_conn)
                
                if ticker_list:
                    # 2. 인터넷에서 모든 뉴스 데이터 수집하기
                    collected_news = fetch_finnhub_news_for_all_tickers(ticker_list)
                    # 3. 수집한 뉴스를 DB에 한 번에 저장하기
                    bulk_insert_news(db_conn, collected_news)
            finally:
                db_conn.close()
                print("\n🔌 데이터베이스 연결이 종료되었습니다.")