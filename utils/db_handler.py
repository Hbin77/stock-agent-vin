# utils/db_handler.py

import psycopg2
import pandas as pd
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ 데이터베이스 연결에 실패했습니다: {e}")
        return None

def load_stock_data(ticker):
    print(f"\n🗄️ 데이터베이스에서 '{ticker}' 주가 데이터를 로드합니다...")
    conn = get_db_connection()
    if conn:
        try:
            sql = f"SELECT * FROM stock_price_daily WHERE ticker = '{ticker}' ORDER BY time;"
            df = pd.read_sql(sql, conn, index_col='time')
            if not df.empty:
                # Naive datetime으로 변환 (타임존 정보 제거)
                df.index = pd.to_datetime(df.index).tz_localize(None)
            print(f"✅ '{ticker}' 주가 데이터 로드 완료: {len(df)}개 행")
            return df
        except Exception as e:
            print(f"❌ 주가 데이터 로드 중 오류 발생: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def load_news_data(ticker):
    """지정된 티커의 뉴스 데이터를 DataFrame으로 로드합니다."""
    print(f"🗄️ 데이터베이스에서 '{ticker}' 뉴스 데이터를 로드합니다...")
    conn = get_db_connection()
    if conn:
        try:
            # 특정 티커에 대한 뉴스만 시간 순으로 정렬하여 가져옵니다.
            sql = f"SELECT * FROM stock_news WHERE ticker = '{ticker}' ORDER BY published_at;"
            df = pd.read_sql(sql, conn)
            print(f"✅ '{ticker}' 뉴스 데이터 로드 완료: {len(df)}개 행")
            return df
        except Exception as e:
            print(f"❌ 뉴스 데이터 로드 중 오류 발생: {e}")
            return pd.DataFrame() # 오류 발생 시 빈 데이터프레임 반환
        finally:
            conn.close()
    return pd.DataFrame() # DB 연결 실패 시 빈 데이터프레임 반환


def load_economic_data():
    """전체 경제 지표 데이터를 DataFrame으로 로드합니다."""
    print("🗄️ 데이터베이스에서 거시 경제 지표 데이터를 로드합니다...")
    conn = get_db_connection()
    if conn:
        try:
            sql = "SELECT * FROM economic_indicators ORDER BY time;"
            df = pd.read_sql(sql, conn, index_col='time')

            if not df.empty:
                df.index = df.index.tz_localize(None)

            print(f"✅ 경제 지표 데이터 로드 완료: {len(df)}개 행")
            return df
        except Exception as e:
            print(f"❌ 경제 지표 데이터 로드 중 오류 발생: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def get_stock_tickers():
    """DB에 저장된 모든 활성 주식 티커 목록을 반환합니다."""
    conn = get_db_connection()
    if conn:
        try:
            sql = "SELECT ticker FROM stock_master WHERE is_active = TRUE ORDER BY ticker;"
            df = pd.read_sql(sql, conn)
            return df['ticker'].tolist()
        finally:
            conn.close()
    return []