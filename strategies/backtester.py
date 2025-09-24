import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_backtest_for_dashboard(df_test_period, predictions, initial_cash=10000):
    """
    Streamlit 대시보드용으로 백테스팅을 수행하고, 결과 데이터를 반환합니다.
    (기존 run_backtest와 거의 동일하지만, plt.show() 대신 결과값을 return 합니다.)
    """
    stop_loss_pct = 0.03
    take_profit_pct = 0.07
    volume_threshold = 1.5
    investment_pct = 0.5

    df = df_test_period.copy()
    # 예측 신호가 있는 기간만 필터링하여 백테스팅
    predictions_series = pd.Series(predictions, index=df.index).dropna()
    df = df.loc[predictions_series.index]
    
    df['volume_ma20'] = df['volume'].rolling(window=20).mean()
    
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

    final_value = portfolio_values[-1]
    total_return = (final_value - initial_cash) / initial_cash
    buy_and_hold_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
    
    return portfolio_values, total_return, buy_and_hold_return