# models/trainer.py
import numpy as np
import pandas as pd 
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
from features.builder import create_lstm_dataset

def train_and_evaluate(df):
    """SMOTE를 적용하여 LSTM 딥러닝 모델을 생성, 학습하고 평가합니다."""
    print("\n🧠 LSTM 딥러닝 모델 학습을 시작합니다 (SMOTE 적용)...")
    
    features = ['close', 'RSI_14', 'MACD_12_26_9', 'BBP_20_2.0_2.0', 'OBV', 'OBV_MA10']
    target = 'target'

    X = df[features]
    y = df[target]
    
    time_steps = 60
    X_seq, y_seq = create_lstm_dataset(X, y, time_steps)
    
    if len(X_seq) == 0:
        print("⚠️ 시퀀스 데이터 생성에 실패했습니다 (데이터 부족).")
        return None, None, None, None, None, None, None

    split_index = int(len(X_seq) * 0.8)
    X_train, X_test = X_seq[:split_index], X_seq[split_index:]
    y_train, y_test = y_seq[:split_index], y_seq[split_index:]
    
    # SMOTE 적용을 위해 훈련 데이터를 2D로 변환
    nsamples, nx, ny = X_train.shape
    X_train_2d = X_train.reshape((nsamples, nx * ny))
    
    print(f"SMOTE 적용 전 훈련 데이터 클래스 분포: {pd.Series(y_train).value_counts().to_dict()}")
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_2d, y_train)
    print(f"SMOTE 적용 후 훈련 데이터 클래스 분포: {pd.Series(y_train_resampled).value_counts().to_dict()}")
    
    # 다시 LSTM 입력 형태(3D)로 복원
    X_train_resampled = X_train_resampled.reshape((X_train_resampled.shape[0], nx, ny))
    
    # [수정된 부분] LSTM 모델 아키텍처 명시
    model = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=(X_train_resampled.shape[1], X_train_resampled.shape[2])),
        Dropout(0.2),
        LSTM(units=50, return_sequences=False),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1, activation='sigmoid') 
    ])
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    print("모델 학습을 시작합니다...")
    model.fit(X_train_resampled, y_train_resampled, epochs=25, batch_size=32, validation_data=(X_test, y_test), verbose=0)
    
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=['Fail', 'Success'], zero_division=0)
    
    print("✅ LSTM 모델 학습 및 평가 완료!")
    test_indices = df.index[split_index + time_steps:]
    return model, test_indices, y_test, y_pred, accuracy, report, features