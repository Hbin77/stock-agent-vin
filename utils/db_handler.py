# 🗄️ 데이터베이스 연결 및 쿼리 실행을 전담
import psycopg2
import pandas as pd
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_db_connection():
    """데이터베이스 커넥션을 생성하여 반환합니다."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ 데이터베이스 연결에 실패했습니다: {e}")
        return None

def load_stock_data(ticker):
    """특정 티커의 전체 주가 데이터를 DataFrame으로 로드합니다."""
    print(f"🗄️ 데이터베이스에서 '{ticker}' 데이터를 로드합니다...")
    conn = get_db_connection()
    if conn:
        try:
            sql = f"SELECT * FROM stock_price_daily WHERE ticker = '{ticker}' ORDER BY time;"
            df = pd.read_sql(sql, conn, index_col='time')
            print(f"✅ '{ticker}' 데이터 로드 완료: {len(df)}개 행")
            return df
        except Exception as e:
            print(f"❌ 데이터 로드 중 오류 발생: {e}")
            return pd.DataFrame() # 오류 시 빈 DataFrame 반환
        finally:
            conn.close()
    return pd.DataFrame()
def load_news_data(ticker):
    """특정 티커의 전체 뉴스 데이터를 DataFrame으로 로드합니다."""
    print(f"🗄️ 데이터베이스에서 '{ticker}' 뉴스 데이터를 로드합니다...")
    conn = get_db_connection()
    if conn:
        try:
            # 뉴스를 날짜별로 그룹화하여 평균 감성 점수를 계산
            sql = f"""
            SELECT
                DATE(published_at AT TIME ZONE 'UTC') AS date,
                AVG(sentiment_score) AS avg_sentiment_score,
                COUNT(*) AS news_count
            FROM stock_news
            WHERE ticker = '{ticker}' AND sentiment_score IS NOT NULL
            GROUP BY DATE(published_at AT TIME ZONE 'UTC')
            ORDER BY date;
            """
            df = pd.read_sql(sql, conn, index_col='date')
            # 인덱스 타입을 datetime으로 변경하여 나중에 주가 데이터와 병합할 수 있도록 함
            df.index = pd.to_datetime(df.index)
            print(f"✅ '{ticker}' 뉴스 데이터 로드 및 집계 완료: {len(df)}개 날짜")
            return df
        except Exception as e:
            print(f"❌ 뉴스 데이터 로드 중 오류 발생: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()