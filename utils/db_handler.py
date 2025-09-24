import psycopg2
import pandas as pd
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_db_connection():
    # ... (이전과 동일)
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ 데이터베이스 연결에 실패했습니다: {e}")
        return None

def load_stock_data(ticker):
    # ... (이전과 동일)
    print(f"\n🗄️ 데이터베이스에서 '{ticker}' 주가 데이터를 로드합니다...")
    conn = get_db_connection()
    if conn:
        try:
            sql = f"SELECT * FROM stock_price_daily WHERE ticker = '{ticker}' ORDER BY time;"
            df = pd.read_sql(sql, conn, index_col='time')
            if not df.empty:
                df.index = df.index.tz_localize(None)
            print(f"✅ '{ticker}' 주가 데이터 로드 완료: {len(df)}개 행")
            return df
        except Exception as e:
            print(f"❌ 주가 데이터 로드 중 오류 발생: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def load_news_data(ticker):
    # ... (이전과 동일)
    print(f"🗄️ 데이터베이스에서 '{ticker}' 뉴스 데이터를 로드합니다...")
    conn = get_db_connection()
    # ... (함수 내용은 이전과 동일)

def load_economic_data():
    """전체 경제 지표 데이터를 DataFrame으로 로드합니다."""
    print("🗄️ 데이터베이스에서 거시 경제 지표 데이터를 로드합니다...")
    conn = get_db_connection()
    if conn:
        try:
            sql = "SELECT * FROM economic_indicators ORDER BY time;"
            df = pd.read_sql(sql, conn, index_col='time')
            
            # ▼▼▼ [수정된 부분] ▼▼▼
            # 데이터프레임이 비어있지 않을 때만 타임존 제거를 실행
            if not df.empty:
                df.index = df.index.tz_localize(None)
            # ▲▲▲ [수정된 부분] ▲▲▲
                
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