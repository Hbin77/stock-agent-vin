# features/builder.py
import pandas as pd
import pandas_ta as ta
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def create_lstm_dataset(X, y, time_steps=60):
    """LSTM 모델 학습을 위한 시퀀스 데이터셋을 생성합니다."""
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        v = X.iloc[i:(i + time_steps)].values
        Xs.append(v)
        ys.append(y.iloc[i + time_steps])
    return np.array(Xs), np.array(ys)

def add_features_and_target(df):
    """LSTM 모델에 맞게 피처, 타겟을 생성하고 데이터를 정규화합니다."""
    print("\n🛠️ LSTM을 위한 피처 엔지니어링 및 데이터 전처리를 시작합니다...")
    
    # 1. 기술적 지표 추가
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, append=True)
    df.ta.bbands(length=20, append=True)
    df.ta.obv(append=True)
    df['OBV_MA10'] = df['OBV'].rolling(window=10).mean()
    
    # 2. 타겟 변수 생성 (기존과 동일)
    look_forward_period = 10
    target_return = 0.05
    stop_loss_return = -0.02
    df['target'] = 0
    
    for i in range(len(df) - look_forward_period):
        entry_price = df['close'].iloc[i]
        future_prices = df['close'].iloc[i+1 : i+1+look_forward_period]
        take_profit_price = entry_price * (1 + target_return)
        stop_loss_price = entry_price * (1 + stop_loss_return)
        for price in future_prices:
            if price >= take_profit_price:
                df.loc[df.index[i], 'target'] = 1; break
            elif price <= stop_loss_price:
                df.loc[df.index[i], 'target'] = 0; break

    df.dropna(inplace=True)
    
    # 3. 데이터 정규화
    # LSTM은 0~1 사이의 값에 민감하므로 정규화가 필수적입니다.
    features_to_scale = ['close', 'RSI_14', 'MACD_12_26_9', 'BBP_20_2.0_2.0', 'OBV', 'OBV_MA10']
    scaler = MinMaxScaler(feature_range=(0, 1))
    df[features_to_scale] = scaler.fit_transform(df[features_to_scale])
    
    print("✅ 피처 엔지니어링 및 데이터 전처리 완료!")
    # 정규화에 사용된 scaler 객체도 함께 반환해야 나중에 예측값을 원래 스케일로 되돌릴 수 있습니다.
    return df, scaler