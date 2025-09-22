# strategies/backtester.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_backtest(df_test_period, predictions):
    """AI의 예측에만 기반하여 백테스팅을 수행합니다."""
    print("\n📈 AI 예측 기반 전략 백테스팅을 시작합니다...")
    
    predictions_series = pd.Series(predictions.flatten(), index=df_test_period.index)
    
    initial_cash = 10000
    cash = initial_cash
    shares = 0
    portfolio_values = []

    for date, row in df_test_period.iterrows():
        if date in predictions_series.index and predictions_series.loc[date] == 1 and shares == 0:
            shares_to_buy = cash / row['open']
            shares += shares_to_buy
            cash = 0
        elif date in predictions_series.index and predictions_series.loc[date] == 0 and shares > 0:
            cash += shares * row['open']
            shares = 0
        
        current_value = cash + shares * row['close']
        portfolio_values.append(current_value)

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