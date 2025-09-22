# data/collector.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import yfinance as yf
import psycopg2
import requests
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_nasdaq100_tickers():
    """Wikipedia에서 NASDAQ 100 종목 티커 및 회사 이름을 가져옵니다."""
    print("📜 Wikipedia에서 NASDAQ 100 종목 목록을 가져옵니다...")
    try:
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        # read_html은 페이지의 모든 테이블을 list of DataFrame 형태로 반환합니다.
        # NASDAQ 100 구성종목 테이블은 일반적으로 4번째에 위치합니다.
        tables = pd.read_html(requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text)
        # 테이블 인덱스는 페이지 구조 변경에 따라 달라질 수 있습니다.
        # 만약 아래 코드가 실패하면, tables[3], tables[5] 등을 시도해보세요.
        nasdaq_df = tables[4]
        print(f"✅ 총 {len(nasdaq_df)}개의 NASDAQ 100 종목 정보를 성공적으로 가져왔습니다.")
        # DataFrame에서 필요한 'Ticker'와 'Company' 컬럼만 선택
        return nasdaq_df[['Ticker', 'Company']]
    except Exception as e:
        print(f"❌ Wikipedia에서 NASDAQ 100 목록을 가져오는 중 오류 발생: {e}")
        return None

def update_stock_master(conn, tickers_df):
    """DB의 stock_master 테이블을 최신 종목 목록으로 업데이트합니다."""
    print(f"🔄 {len(tickers_df)}개 종목으로 stock_master 테이블을 업데이트합니다...")
    with conn.cursor() as cursor:
        # 1. 모든 종목을 비활성(is_active=FALSE) 상태로 초기화
        cursor.execute("UPDATE stock_master SET is_active = FALSE")
        
        updated_count = 0
        # 2. NASDAQ 100 목록을 순회하며 DB에 업데이트 또는 신규 삽입
        for _, row in tickers_df.iterrows():
            # ON CONFLICT 구문을 사용하여 티커가 이미 존재하면 회사 이름과 활성 상태를 업데이트하고,
            # 존재하지 않으면 새로운 레코드를 삽입합니다 (UPSERT).
            sql = """
            INSERT INTO stock_master (ticker, company_name, is_active)
            VALUES (%s, %s, TRUE)
            ON CONFLICT (ticker) DO UPDATE
            SET company_name = EXCLUDED.company_name, is_active = TRUE;
            """
            cursor.execute(sql, (row['Ticker'], row['Company']))
            updated_count += 1
        
        conn.commit()
        print(f"✅ {updated_count}개 종목을 stock_master 테이블에 업데이트 완료.")

def run_full_pipeline():
    """전체 데이터 수집 파이프라인을 실행합니다."""
    conn = None
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        print("\n🔌 데이터베이스 연결 성공.")
        
        # 1. NASDAQ 100 종목 목록 가져오기
        nasdaq_tickers_df = get_nasdaq100_tickers()
        
        # 2. stock_master 테이블 업데이트
        if nasdaq_tickers_df is not None and not nasdaq_tickers_df.empty:
            update_stock_master(conn, nasdaq_tickers_df)
        else:
            print("⚠️ NASDAQ 100 종목 정보를 가져오지 못해 주가 데이터 수집을 건너뜁니다.")
            return

        # 3. 주가 데이터 수집
        with conn.cursor() as cursor:
            cursor.execute("SELECT ticker FROM stock_master WHERE is_active = TRUE")
            tickers_to_fetch = [row[0] for row in cursor.fetchall()]

        print(f"\n📈 총 {len(tickers_to_fetch)}개 활성 종목의 주가 데이터 수집을 시작합니다.")
        for ticker in tickers_to_fetch:
            print(f"----- {ticker} 데이터 다운로드 중 -----")
            # yfinance를 통해 2020년 1월 1일부터 오늘까지의 데이터 다운로드
            df = yf.download(ticker, start="2020-01-01", end=pd.to_datetime('today').strftime('%Y-%m-%d'))
            
            if df.empty:
                print(f"⚠️ {ticker}: yfinance에서 데이터를 가져올 수 없습니다. 건너뜁니다.")
                continue

            # 수집한 데이터를 stock_price_daily 테이블에 저장
            with conn.cursor() as insert_cursor:
                for index, row in df.iterrows():
                    sql = """INSERT INTO stock_price_daily (time, ticker, open, high, low, close, volume) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (time, ticker) DO NOTHING;"""
                    data = (
                        index.to_pydatetime(), # Timestamp를 Python datetime 객체로 변환
                        ticker,
                        float(row['Open']),
                        float(row['High']),
                        float(row['Low']),
                        float(row['Close']),
                        int(row['Volume'])
                    )
                    insert_cursor.execute(sql, data)
                conn.commit()
            print(f"✅ {ticker}: 데이터 {len(df)}건 저장 완료.")

    except psycopg2.OperationalError as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")
        print("    config.py 파일의 DB 접속 정보가 올바른지 확인해주세요.")
    except Exception as e:
        print(f"❌ 전체 파이프라인 실행 중 오류 발생: {e}")
    finally:
        if conn:
            conn.close()
            print("\n🔌 데이터베이스 연결이 종료되었습니다.")

# 이 스크립트가 직접 실행될 때 run_full_pipeline 함수를 호출
if __name__ == "__main__":
    run_full_pipeline()