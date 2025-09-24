# models/lgbm_trainer.py (Final Version)

import lightgbm as lgb
import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE

def train_and_evaluate(df):
    """LightGBM 모델을 생성, 학습하고 최종 예측 결과를 반환합니다."""
    print("\n🌳 LightGBM 모델 학습을 시작합니다 (SMOTE 적용)...")
    
    features = [
        'close', 'RSI_14', 'MACD_12_26_9', 'BBP_20_2.0_2.0', 'OBV', 'OBV_MA10',
        'ATRr_14', 'STOCHk_14_3_3', 'STOCHd_14_3_3', 'fed_rate', 'usd_krw'
    ]
    target = 'target'
    
    features = [f for f in features if f in df.columns]
    
    X = df[features]
    y = df[target]

    if X.empty or y.empty:
        print("⚠️ LightGBM 학습을 위한 데이터가 부족합니다.")
        return None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    
    lgb_clf = lgb.LGBMClassifier(random_state=42, verbosity=-1) # 로그 출력을 끔
    lgb_clf.fit(X_train_resampled, y_train_resampled)
    
    print("✅ LightGBM 모델 학습 완료!")
    
    full_predictions = lgb_clf.predict(X)
    
    return pd.Series(full_predictions, index=X.index)