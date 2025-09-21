# features/builder.py
import pandas_ta as ta
import numpy as np

def add_features_and_target(df):
    """모든 거래일에 대해 피처와 타겟 변수를 추가합니다."""
    print("\n🛠️ 피처 엔지니어링 (모든 거래일 학습 방식)을 시작합니다...")
    
    # 1. 기술적 지표 추가
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, append=True)
    df.ta.bbands(length=20, append=True)
    df.ta.atr(length=14, append=True)
    df.ta.obv(append=True)
    df['OBV_MA5'] = df['OBV'].rolling(window=5).mean()
    df['OBV_MA10'] = df['OBV'].rolling(window=10).mean()
    
    # 2. 모든 날에 대해 '메타 라벨' 타겟 생성
    look_forward_period = 10
    target_return = 0.05
    stop_loss_return = -0.02
    
    df['target'] = 0 # 기본값은 0(실패 또는 관망)
    
    for i in range(len(df) - look_forward_period):
        entry_price = df['close'].iloc[i]
        future_prices = df['close'].iloc[i+1 : i+1+look_forward_period]
        
        take_profit_price = entry_price * (1 + target_return)
        stop_loss_price = entry_price * (1 + stop_loss_return)

        for price in future_prices:
            if price >= take_profit_price:
                # .loc를 사용하여 정확한 위치에 값을 할당합니다.
                df.loc[df.index[i], 'target'] = 1 # 성공
                break
            elif price <= stop_loss_price:
                df.loc[df.index[i], 'target'] = 0 # 실패
                break
    
    # 지표 계산 초기에 발생하는 NaN 값 제거
    df.dropna(inplace=True)
    
    print("✅ 피처 엔지니어링 완료!")
    # 이제 하나의 완성된 데이터프레임만 반환합니다.
    return df