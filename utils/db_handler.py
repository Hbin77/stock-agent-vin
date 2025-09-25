# utils/db_handler.py

import psycopg2
import pandas as pd
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_db_connection():
    """데이터베이스 연결을 반환합니다."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

def load_stock_data(ticker):
    """특정 티커의 주가 데이터를 로드합니다."""
    print(f"🗄️ 데이터베이스에서 '{ticker}' 주가 데이터를 로드합니다...")
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = """
        SELECT time, open, high, low, close, volume 
        FROM stock_price_daily 
        WHERE ticker = %s 
        ORDER BY time
        """
        df = pd.read_sql(sql, conn, params=[ticker], index_col='time')
        print(f"✅ '{ticker}' 주가 데이터 로드 완료: {len(df)}개 행")
        return df
    except Exception as e:
        print(f"❌ '{ticker}' 주가 데이터 로드 실패: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def load_economic_data():
    """거시 경제 지표 데이터를 로드합니다."""
    print("🗄️ 데이터베이스에서 거시 경제 지표 데이터를 로드합니다...")
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = "SELECT time, fed_rate, usd_krw FROM economic_indicators ORDER BY time"
        df = pd.read_sql(sql, conn, index_col='time')
        print(f"✅ 경제 지표 데이터 로드 완료: {len(df)}개 행")
        return df
    except Exception as e:
        print(f"❌ 경제 지표 데이터 로드 실패: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def load_news_data(ticker):
    """특정 티커의 뉴스 데이터를 로드합니다."""
    print(f"🗄️ 데이터베이스에서 '{ticker}' 뉴스 데이터를 로드합니다...")
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = """
        SELECT published_at, sentiment_score 
        FROM stock_news 
        WHERE ticker = %s AND sentiment_score IS NOT NULL
        ORDER BY published_at
        """
        df = pd.read_sql(sql, conn, params=[ticker])
        print(f"✅ '{ticker}' 뉴스 데이터 로드 완료: {len(df)}개 행")
        return df
    except Exception as e:
        print(f"❌ '{ticker}' 뉴스 데이터 로드 실패: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_stock_tickers():
    """활성화된 모든 주식 티커를 반환합니다."""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT ticker FROM stock_master WHERE is_active = TRUE ORDER BY ticker")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ 티커 목록 로드 실패: {e}")
        return []
    finally:
        conn.close()