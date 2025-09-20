import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas_ta as ta

# DB 연결 정보
db_host = "localhost"
db_port = "5432"
db_name = "postgres"
db_user = "postgres"
db_password = "0306" # 설정했던 비밀번호

# DB에서 특정 티커의 데이터 불러오기
try:
    conn = psycopg2.connect(
        host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_password
    )
    # SQL 쿼리를 이용해 데이터를 Pandas DataFrame으로 직접 로드
    sql = "SELECT time, open, high, low, close, volume FROM stock_price_daily WHERE ticker = 'AAPL' ORDER BY time;"
    df = pd.read_sql(sql, conn, index_col='time')
    print("✅ AAPL 데이터 로드 성공!")
    print(df.head())

except Exception as e:
    print(f"❌ 데이터 로드 중 오류: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()

# 데이터 시각화 (종가 그래프)
plt.style.use('seaborn-v0_8-darkgrid') # 그래프 스타일 설정
fig, ax = plt.subplots(figsize=(15, 7))
ax.plot(df.index, df['close'], label='AAPL Close Price', color='cyan')
ax.set_title('Apple Inc. (AAPL) Stock Price History', fontsize=16)
ax.set_ylabel('Price (USD)')
ax.set_xlabel('Date')
ax.legend()

# x축 날짜 형식 설정
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
fig.autofmt_xdate()

# 위 코드에 이어서...

# 이동평균선 계산 (20일, 60일)
df['MA20'] = df['close'].rolling(window=20).mean()
df['MA60'] = df['close'].rolling(window=60).mean()

# 이동평균선과 함께 시각화
ax.plot(df.index, df['MA20'], label='20-Day MA', color='orange', linestyle='--')
ax.plot(df.index, df['MA60'], label='60-Day MA', color='magenta', linestyle='--')
ax.legend() # 범례 다시 표시
df.ta.rsi(length=14, append=True)

# MACD 계산하여 관련 컬럼들('MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9') 추가
df.ta.macd(fast=12, slow=26, append=True)

# 볼린저 밴드(Bollinger Bands) 계산하여 관련 컬럼들 추가
df.ta.bbands(length=20, append=True)

# 새로 추가된 피처(컬럼)들 확인
print("\n--- 피처 엔지니어링 후 데이터 ---")
# 소수점 2자리까지만 표시
print(df.tail().round(2))

# 다시 그래프 보여주기 (위의 plt.show()를 이 코드로 대체하거나, 새 창에서 실행)
plt.show()