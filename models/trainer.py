# models/trainer.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import GridSearchCV # GridSearchCV 임포트

def train_and_evaluate(df):
    """GridSearchCV로 하이퍼파라미터를 튜닝하여 최적의 모델을 학습하고 평가합니다."""
    print("\n🧠 모델 학습 및 평가를 시작합니다 (하이퍼파라미터 튜닝 적용)...")
    
    features = [
        'RSI_14', 'MACD_12_26_9', 'BBP_20_2.0_2.0',
        'ATRr_14', 'OBV', 'OBV_MA5', 'OBV_MA10'
    ]
    target = 'target'
    X = df[features]
    y = df[target]
    
    if len(df) < 20 or len(y.unique()) < 2:
        print("⚠️ 학습할 데이터가 부족하거나 타겟 클래스가 하나뿐입니다.")
        return None, None, None, None, None, None, None

    split_index = int(len(X) * 0.8)
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    
    # [수정된 부분] 하이퍼파라미터 튜닝 설정
    # 테스트할 파라미터 조합을 정의합니다.
    param_grid = {
        'n_estimators': [100, 200],      # 나무의 개수
        'max_depth': [10, 20, None],     # 나무의 최대 깊이
        'min_samples_leaf': [1, 2, 4]    # 리프 노드의 최소 샘플 수
    }
    
    # GridSearchCV 객체 생성
    # cv=3은 교차 검증을 3번 수행한다는 의미입니다.
    # n_jobs=-1은 모든 CPU 코어를 사용하라는 의미입니다.
    grid_search = GridSearchCV(estimator=RandomForestClassifier(random_state=42),
                               param_grid=param_grid, cv=3, n_jobs=-1, scoring='f1_weighted')
    
    print("하이퍼파라미터 튜닝을 시작합니다. 시간이 다소 소요될 수 있습니다...")
    # 튜닝 시작 (가장 좋은 파라미터를 찾음)
    grid_search.fit(X_train_resampled, y_train_resampled)
    
    # 가장 성능이 좋았던 모델을 best_model로 저장
    best_model = grid_search.best_estimator_
    print(f"최적의 파라미터: {grid_search.best_params_}")
    
    # 최적의 모델로 예측 및 평가
    y_pred = best_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=['Fail', 'Success'], zero_division=0)
    
    print("✅ 모델 학습 및 평가 완료!")
    return best_model, X_test, y_test, y_pred, accuracy, report, features