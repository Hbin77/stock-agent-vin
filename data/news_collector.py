import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import psycopg2
from datetime import datetime, timedelta
from utils import db_handler
from config import NEWS_API_KEY

def fetch_and_store_news(ticker, company_name):
    """NewsAPI를 통해 특정 종목의 뉴스를 가져와 DB에 저장합니다."""
    print(f"\n📰 '{ticker}'에 대한 뉴스 수집을 시작합니다...")
    
    # 검색 기간 설정 (예: 최근 30일)
    to_date = datetime.now()
    from_date = to_date - timedelta(days=30)
    
    url = (f'https://newsapi.org/v2/everything?'
           f'q="{company_name}"&' # 정확도를 위해 회사 이름에 따옴표 추가
           f'from={from_date.strftime("%Y-%m-%d")}&'
           f'to={to_date.strftime("%Y-%m-%d")}&'
           f'language=en&'
           f'sortBy=publishedAt&'
           f'apiKey={NEWS_API_KEY}')
           
    conn = None
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        
        if not articles:
            print(f"'{ticker}'에 대한 뉴스를 찾을 수 없습니다.")
            return

        conn = db_handler.get_db_connection()
        with conn.cursor() as cursor:
            new_news_count = 0
            for article in articles:
                # 제목이나 URL이 없는 뉴스는 건너뜀
                if not article.get('title') or not article.get('url'):
                    continue

                sql = """
                INSERT INTO stock_news (ticker, published_at, title, url, source_name)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
                """
                published_time = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                
                data = (
                    ticker,
                    published_time,
                    article['title'],
                    article['url'],
                    article.get('source', {}).get('name')
                )
                cursor.execute(sql, data)
                # 실제로 새로운 행이 추가되었는지 확인
                if cursor.rowcount > 0:
                    new_news_count += 1

            conn.commit()
        print(f"✅ '{ticker}' 뉴스 {len(articles)}건 처리 완료 (신규 저장: {new_news_count}건).")

    except requests.exceptions.HTTPError as e:
        print(f"❌ 뉴스 API 요청 실패: {e}. API 키 또는 요청 제한을 확인하세요.")
    except Exception as e:
        print(f"❌ 뉴스 저장 중 오류 발생: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    conn = db_handler.get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT ticker, company_name FROM stock_master WHERE is_active = TRUE")
            tickers = cursor.fetchall()
        conn.close()

        for ticker, company_name in tickers:
            # 뉴스 검색용 회사 이름 정제
            clean_company_name = company_name.replace(' Inc.', '').replace(' Corporation', '').replace(',','').split(' ')[0]
            fetch_and_store_news(ticker, clean_company_name)