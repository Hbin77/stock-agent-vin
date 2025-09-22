# models/lgbm_trainer.py

import lightgbm as lgb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE

def train_and_evaluate(df):
    """LightGBM 모델을 생성, 학습하고 평가합니다."""
    print("\n🌳 LightGBM 모델 학습을 시작합니다 (SMOTE 적용)...")
    
    # 1. 피처와 타겟 설정
    # LightGBM은 딥러닝 모델과 달리 시퀀스 데이터가 아닌, 현재 시점의 데이터만 사용합니다.
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
        return None, None, None

    # 2. 데이터 분할 (훈련/테스트)
    # stratify=y 옵션은 훈련/테스트 데이터의 타겟 비율을 원본과 동일하게 유지해줍니다.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. SMOTE를 사용한 오버샘플링
    print(f"SMOTE 적용 전 훈련 데이터 클래스 분포: {y_train.value_counts().to_dict()}")
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    print(f"SMOTE 적용 후 훈련 데이터 클래스 분포: {pd.Series(y_train_resampled).value_counts().to_dict()}")

    # 4. LightGBM 모델 학습
    lgb_clf = lgb.LGBMClassifier(random_state=42)
    lgb_clf.fit(X_train_resampled, y_train_resampled)

    # 5. 모델 평가
    y_pred = lgb_clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=['Fail', 'Success'], zero_division=0)
    
    print("✅ LightGBM 모델 학습 및 평가 완료!")
    
    # 백테스팅에 사용할 수 있도록 전체 데이터에 대한 예측을 반환합니다.
    full_predictions = lgb_clf.predict(X)
    
    return lgb_clf, accuracy, report, pd.Series(full_predictions, index=X.index)