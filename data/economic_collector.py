import sys
import os
import pandas as pd
import pandas_datareader.data as web
from datetime import datetime
import psycopg2

# 프로젝트 최상위 폴더를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import db_handler

def fetch_and_store_economic_data():
    """FRED에서 주요 거시 경제 지표를 가져와 DB에 저장합니다."""
    print("\n🏛️ FRED에서 거시 경제 지표 데이터 수집을 시작합니다...")
    
    start_date = "2020-01-01"
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    series_codes = {
        'DFF': 'fed_rate',
        'DEXKOUS': 'usd_krw'
    }
    
    try:
        df_econ = web.DataReader(list(series_codes.keys()), 'fred', start_date, end_date)
        df_econ.rename(columns=series_codes, inplace=True)
        df_econ.ffill(inplace=True)
        
        print(f"✅ 총 {len(df_econ)}일의 경제 지표 데이터를 성공적으로 가져왔습니다.")

        conn = db_handler.get_db_connection()
        if not conn:
            return

        with conn.cursor() as cursor:
            sql = """
            INSERT INTO economic_indicators (time, fed_rate, usd_krw)
            VALUES (%s, %s, %s)
            ON CONFLICT (time) DO UPDATE SET
                fed_rate = EXCLUDED.fed_rate,
                usd_krw = EXCLUDED.usd_krw;
            """
            for index, row in df_econ.iterrows():
                if row.isnull().any():
                    continue
                
                # ▼▼▼ [수정된 부분] ▼▼▼
                # NumPy 타입을 파이썬 기본 float으로 변환하여 오류 해결
                fed_rate_val = float(row['fed_rate']) if pd.notna(row['fed_rate']) else None
                usd_krw_val = float(row['usd_krw']) if pd.notna(row['usd_krw']) else None
                # ▲▲▲ [수정된 부분] ▲▲▲
                
                cursor.execute(sql, (index, fed_rate_val, usd_krw_val))
            
            conn.commit()
            print("✅ 경제 지표 데이터를 데이터베이스에 저장 완료!")

    except Exception as e:
        print(f"❌ 경제 지표 수집 또는 저장 중 오류 발생: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    fetch_and_store_economic_data()