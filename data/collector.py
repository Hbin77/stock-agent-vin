def run_full_pipeline():
    """전체 데이터 수집 파이프라인을 실행합니다."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_password
        )
        
        nasdaq_tickers_df = get_nasdaq100_tickers()
        
        if nasdaq_tickers_df is not None:
            update_stock_master(conn, nasdaq_tickers_df)
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT ticker FROM stock_master WHERE is_active = TRUE")
            tickers_to_fetch = [row[0] for row in cursor.fetchall()]

        print(f"\n📈 총 {len(tickers_to_fetch)}개 종목의 데이터 수집을 시작합니다.")
        for ticker in tickers_to_fetch:
            print(f"----- {ticker} 데이터 다운로드 중 -----")
            df = yf.download(ticker, start="2020-01-01", end=pd.to_datetime('today').strftime('%Y-%m-%d'))
            
            if df.empty:
                print(f"⚠️ {ticker}: 데이터 없음. 건너뜁니다.")
                continue

            with conn.cursor() as insert_cursor:
                for index, row in df.iterrows():
                    sql = """INSERT INTO stock_price_daily (time, ticker, open, high, low, close, volume) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (ticker, time) DO NOTHING;"""
                    data = (
                        index,
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

    except Exception as e:
        print(f"❌ 전체 파이프라인 실행 중 오류 발생: {e}")
    finally:
        if conn:
            conn.close()
            print("\n🔌 데이터베이스 연결이 종료되었습니다.")