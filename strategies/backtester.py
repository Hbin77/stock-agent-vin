# strategies/backtester.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ▼▼▼ [수정된 부분] 손절(-3%), 익절(+7%) 파라미터 추가 ▼▼▼
def run_backtest(df_test_period, predictions, stop_loss_pct=0.03, take_profit_pct=0.07):
    """AI 예측과 손절/익절 규칙을 기반으로 백테스팅을 수행합니다."""
    print(f"\n📈 AI 예측 기반 전략 백테스팅을 시작합니다 (손절: {stop_loss_pct:.0%}, 익절: {take_profit_pct:.0%})...")
    
    predictions_series = pd.Series(predictions.flatten(), index=df_test_period.index)
    
    initial_cash = 10000
    cash = initial_cash
    shares = 0
    portfolio_values = []
    purchase_price = 0 # 매수 가격 추적

    for date, row in df_test_period.iterrows():
        current_price = row['open'] # 당일 시가를 기준으로 거래

        # 1. 손절 또는 익절 조건 확인 (주식을 보유한 경우)
        if shares > 0:
            if current_price <= purchase_price * (1 - stop_loss_pct): # 손절 조건
                cash += shares * current_price
                shares = 0
                purchase_price = 0
            elif current_price >= purchase_price * (1 + take_profit_pct): # 익절 조건
                cash += shares * current_price
                shares = 0
                purchase_price = 0
        
        # 2. 모델의 예측에 따른 매매 신호 확인
        if date in predictions_series.index:
            # 매수 신호 (주식을 보유하지 않은 경우)
            if predictions_series.loc[date] == 1 and shares == 0:
                shares_to_buy = cash / current_price
                shares += shares_to_buy
                cash = 0
                purchase_price = current_price # 매수 가격 기록
            # 매도 신호 (주식을 보유한 경우)
            elif predictions_series.loc[date] == 0 and shares > 0:
                cash += shares * current_price
                shares = 0
                purchase_price = 0

        current_value = cash + shares * row['close']
        portfolio_values.append(current_value)

    # ▲▲▲ [수정된 부분] ▲▲▲

    final_value = portfolio_values[-1]
    total_return = (final_value - initial_cash) / initial_cash
    buy_and_hold_return = (df_test_period['close'][-1] - df_test_period['close'][0]) / df_test_period['close'][0]
    
    print("--- 백테스팅 결과 ---")
    print(f"최종 포트폴리오 가치: ${final_value:,.2f}")
    print(f"AI 모델 전략 총 수익률: {total_return:.2%}")
    print(f"단순 보유 전략 총 수익률: {buy_and_hold_return:.2%}")

    plt.figure(figsize=(15, 7))
    plt.plot(df_test_period.index, portfolio_values, label='AI Strategy')
    plt.plot(df_test_period.index, (initial_cash / df_test_period['close'][0]) * df_test_period['close'], label='Buy and Hold Strategy')
    plt.title('Backtesting Results: AI Strategy vs. Buy and Hold')
    plt.legend()
    plt.show()

    return final_value, total_return