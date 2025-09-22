import pandas as pd
import pandas_ta as ta
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from utils import db_handler # db_handler 임포트 추가

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
    
    # ▼▼▼ [수정된 부분 시작] ▼▼▼
    # 1. 경제 지표 데이터 로드 및 병합
    df_econ = db_handler.load_economic_data()
    if not df_econ.empty:
        # 주가 데이터(df)의 인덱스를 기준으로 경제 지표(df_econ)를 합칩니다.
        df = pd.merge(df, df_econ, left_index=True, right_index=True, how='left')
        df.ffill(inplace=True) # 병합 후 누락된 값(주말 등)을 이전 값으로 채웁니다.
        print("✅ 주가 데이터와 경제 지표 데이터 병합 완료.")
    # ▲▲▲ [수정된 부분 끝] ▲▲▲

    # 2. 기술적 지표 추가
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, append=True)
    df.ta.bbands(length=20, append=True)
    df.ta.obv(append=True)
    df['OBV_MA10'] = df['OBV'].rolling(window=10).mean()
    df.ta.atr(length=14, append=True)
    df.ta.stoch(k=14, d=3, append=True)

    # 3. 타겟 변수 생성 (기존과 동일)
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
    
    # 4. 데이터 정규화
    # ▼▼▼ [수정된 부분] 새로 추가된 경제 지표 피처를 정규화 대상에 포함 ▼▼▼
    features_to_scale = [
        'close', 'RSI_14', 'MACD_12_26_9', 'BBP_20_2.0_2.0', 
        'OBV', 'OBV_MA10', 'ATRr_14', 'STOCHk_14_3_3', 'STOCHd_14_3_3',
        'fed_rate', 'usd_krw' # 경제 지표 추가
    ]
    # ▲▲▲ [수정된 부분] ▲▲▲
    
    # 존재하지 않는 컬럼은 정규화 대상에서 제외 (데이터 병합 실패 시 대비)
    features_to_scale = [col for col in features_to_scale if col in df.columns]

    scaler = MinMaxScaler(feature_range=(0, 1))
    df[features_to_scale] = scaler.fit_transform(df[features_to_scale])
    
    print("✅ 피처 엔지니어링 및 데이터 전처리 완료!")
    return df, scaler