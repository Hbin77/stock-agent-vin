# strategies/backtester.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_backtest(df_test_period, predictions, initial_cash=10000):
    """
    거래량, 변동성, 자금 관리를 포함한 고도화된 백테스팅을 수행합니다.
    """
    print("\n📈 전문가용 고급 전략 백테스팅을 시작합니다...")
    
    # --- 1. 전략 파라미터 설정 ---
    stop_loss_pct = 0.03       # 손절매 비율 (-3%)
    take_profit_pct = 0.07     # 익절 비율 (+7%)
    volume_threshold = 1.5     # 거래량 가중치 (평소 거래량의 1.5배 이상일 때만 진입)
    investment_pct = 0.5       # 1회 매수 시 투자 비중 (전체 자산의 50%)

    # --- 2. 데이터 준비 ---
    predictions_series = pd.Series(predictions.flatten(), index=df_test_period.index)
    df = df_test_period.copy()
    
    # 거래량 이동평균(20일) 계산
    df['volume_ma20'] = df['volume'].rolling(window=20).mean()
    
    # --- 3. 백테스팅 시뮬레이션 ---
    cash = initial_cash
    shares = 0
    portfolio_values = []
    purchase_price = 0

    for date, row in df.iterrows():
        current_price = row['open']
        portfolio_value = cash + shares * row['close'] # 현재 포트폴리오 가치 (자금 관리용)
        
        # 1. 보유 주식의 손절/익절 조건 확인
        if shares > 0:
            if current_price <= purchase_price * (1 - stop_loss_pct):
                print(f"  - {date.date()}: 손절매 실행 (가격: ${current_price:.2f})")
                cash += shares * current_price
                shares = 0
            elif current_price >= purchase_price * (1 + take_profit_pct):
                print(f"  - {date.date()}: 익절 실행 (가격: ${current_price:.2f})")
                cash += shares * current_price
                shares = 0

        # 2. AI 모델의 매매 신호 확인
        if date in predictions_series.index:
            # 매수 신호 + 추가 조건(거래량) 충족 시
            if (predictions_series.loc[date] == 1 and 
                shares == 0 and 
                row['volume'] > row['volume_ma20'] * volume_threshold): # 거래량 조건
                
                investment_amount = portfolio_value * investment_pct # 자산의 50%만 투자
                shares_to_buy = investment_amount / current_price
                
                if cash >= investment_amount:
                    print(f"  - {date.date()}: 매수 신호 발생 (가격: ${current_price:.2f}, 수량: {shares_to_buy:.2f}주)")
                    shares += shares_to_buy
                    cash -= investment_amount
                    purchase_price = current_price
            
            # 매도 신호
            elif predictions_series.loc[date] == 0 and shares > 0:
                print(f"  - {date.date()}: 매도 신호 발생 (가격: ${current_price:.2f})")
                cash += shares * current_price
                shares = 0

        portfolio_values.append(cash + shares * row['close'])

    # --- 4. 최종 결과 분석 및 시각화 ---
    final_value = portfolio_values[-1]
    total_return = (final_value - initial_cash) / initial_cash
    buy_and_hold_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
    
    print("\n--- 백테스팅 결과 ---")
    print(f"최종 포트폴리오 가치: ${final_value:,.2f}")
    print(f"AI 모델 전략 총 수익률: {total_return:.2%}")
    print(f"단순 보유 전략 총 수익률: {buy_and_hold_return:.2%}")

    plt.figure(figsize=(15, 7))
    plt.plot(df.index, portfolio_values, label='Advanced AI Strategy')
    plt.plot(df.index, (initial_cash / df['close'].iloc[0]) * df['close'], label='Buy and Hold Strategy')
    plt.title('Backtesting Results: Advanced AI Strategy vs. Buy and Hold')
    plt.legend()
    plt.show()

    return final_value, total_return