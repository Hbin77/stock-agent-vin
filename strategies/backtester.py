# strategies/backtester.py (GUI-Free Final Version)

import numpy as np
import pandas as pd

def run_backtest(df_test_period, predictions, initial_cash=10000):
    """
    (수정됨) GUI/matplotlib 없이 터미널에서 백테스팅을 수행하고, 결과를 텍스트로 출력합니다.
    """
    print("\n📈 전문가용 고급 전략 백테스팅을 시작합니다...")

    # --- 전략 파라미터 ---
    stop_loss_pct = 0.03
    take_profit_pct = 0.07
    volume_threshold = 1.5
    investment_pct = 0.5

    # --- 데이터 준비 ---
    df = df_test_period.copy()
    # predictions는 numpy 배열이므로, 길이를 기준으로 df의 인덱스와 맞춥니다.
    # dropna()를 통해 예측값이 없는 앞부분을 제외하고 백테스팅합니다.
    predictions_series = pd.Series(predictions.flatten(), index=df.index[-len(predictions):]).dropna()
    df = df.loc[predictions_series.index]

    if df.empty:
        print("백테스팅할 데이터가 없습니다.")
        return

    df['volume_ma20'] = df['volume'].rolling(window=20).mean()
    
    # --- 시뮬레이션 ---
    cash = initial_cash
    shares = 0
    portfolio_values = []
    purchase_price = 0

    for date, row in df.iterrows():
        current_price = row['open']
        portfolio_value = cash + shares * row['close']
        
        if shares > 0:
            if current_price <= purchase_price * (1 - stop_loss_pct):
                cash += shares * current_price
                shares = 0
            elif current_price >= purchase_price * (1 + take_profit_pct):
                cash += shares * current_price
                shares = 0

        if date in predictions_series.index:
            if (predictions_series.loc[date] == 1 and 
                shares == 0 and 
                row['volume'] > row['volume_ma20'] * volume_threshold):
                
                investment_amount = portfolio_value * investment_pct
                if cash >= investment_amount:
                    shares_to_buy = investment_amount / current_price
                    shares += shares_to_buy
                    cash -= investment_amount
                    purchase_price = current_price
            
            elif predictions_series.loc[date] == 0 and shares > 0:
                cash += shares * current_price
                shares = 0

        portfolio_values.append(cash + shares * row['close'])

    if not portfolio_values:
        print("백테스팅 결과가 없습니다.")
        return

    # --- 최종 결과 분석 및 출력 ---
    final_value = portfolio_values[-1]
    total_return = (final_value - initial_cash) / initial_cash
    buy_and_hold_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
    
    print("\n--- 백테스팅 결과 ---")
    print(f"최종 포트폴리오 가치: ${final_value:,.2f}")
    print(f"AI 모델 전략 총 수익률: {total_return:.2%}")
    print(f"단순 보유 전략 총 수익률: {buy_and_hold_return:.2%}")
    print(f"--- 백테스팅 완료 ---\n")

# 대시보드용 함수는 더 이상 필요 없으므로 삭제합니다.