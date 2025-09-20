# models/trainer.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

def train_and_evaluate(df):
    """'메타 라벨'을 예측하도록 모델을 학습하고 평가합니다."""
    print("\n🧠 메타 라벨 예측 모델 학습을 시작합니다...")
    
    features = [
        'RSI_14', 'MACD_12_26_9', 'BBP_20_2.0_2.0',
        'STOCHk_14_3_3', 'STOCHd_14_3_3',
        'ATRr_14', 'OBV'
    ]
    target = 'meta_target' # 타겟 변수 변경

    X = df[features]
    y = df[target]
    
    if len(df) < 20: # 학습할 데이터가 너무 적으면 중단
        print("⚠️ 학습할 데이터가 부족합니다.")
        return None, None, None, None, None, None, None

    split_index = int(len(X) * 0.8)
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]
    
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, class_weight='balanced')
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=['Fail', 'Success'])
    
    print("✅ 모델 학습 및 평가 완료!")
    return model, X_test, y_test, y_pred, accuracy, report, features