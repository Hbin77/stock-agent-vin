# models/lstm_trainer.py (Final Version)

import numpy as np
import pandas as pd
import os
import random
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from imblearn.over_sampling import SMOTE
from features.builder import create_lstm_dataset

# 재현성을 위한 시드 고정
seed_value = 42
os.environ['PYTHONHASHSEED'] = str(seed_value)
random.seed(seed_value)
np.random.seed(seed_value)
tf.random.set_seed(seed_value)

def train_and_evaluate(df):
    """SMOTE를 적용하여 LSTM 딥러닝 모델을 생성, 학습하고 예측 결과를 반환합니다."""
    print("\n🧠 LSTM 딥러닝 모델 학습을 시작합니다 (SMOTE 적용)...")
    
    features = [
        'close', 'RSI_14', 'MACD_12_26_9', 'BBP_20_2.0_2.0', 'OBV', 'OBV_MA10',
        'ATRr_14', 'STOCHk_14_3_3', 'STOCHd_14_3_3', 'fed_rate', 'usd_krw'
    ]
    target = 'target'
    
    features = [f for f in features if f in df.columns]

    X = df[features]
    y = df[target]
    
    time_steps = 60
    X_seq, y_seq = create_lstm_dataset(X, y, time_steps)
    
    if len(X_seq) == 0:
        print("⚠️ 시퀀스 데이터 생성에 실패했습니다 (데이터 부족).")
        return None

    split_index = int(len(X_seq) * 0.8)
    X_train, X_test = X_seq[:split_index], X_seq[split_index:]
    y_train, y_test = y_seq[:split_index], y_seq[split_index:]
    
    nsamples, nx, ny = X_train.shape
    X_train_2d = X_train.reshape((nsamples, nx * ny))
    
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_2d, y_train)
    X_train_resampled = X_train_resampled.reshape((X_train_resampled.shape[0], nx, ny))
    
    model = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=(X_train_resampled.shape[1], X_train_resampled.shape[2])),
        Dropout(0.2),
        LSTM(units=50, return_sequences=False),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1, activation='sigmoid') 
    ])
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X_train_resampled, y_train_resampled, epochs=25, batch_size=32, validation_data=(X_test, y_test), verbose=0)
    
    print("✅ LSTM 모델 학습 완료!")
    
    # 백테스팅에 사용할 수 있도록 전체 기간에 대한 예측을 생성
    full_pred_proba = model.predict(X_seq)
    full_predictions = (full_pred_proba > 0.5).astype(int)
    
    # 예측 결과는 시퀀스 길이(60일)만큼 앞부분이 비게 되므로, 이를 원본 데이터프레임 길이에 맞게 패딩 추가
    padding = np.array([np.nan] * (len(df) - len(full_predictions)))
    
    # 최종적으로 예측 결과(Series)만 반환
    return pd.Series(np.concatenate([padding, full_predictions.flatten()]), index=df.index)