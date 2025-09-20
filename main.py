# main.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utils import db_handler
from features import builder
from models import trainer
from strategies import backtester

def plot_feature_importance(model, feature_names):
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    plt.figure(figsize=(12, 6))
    plt.title("Feature Importances")
    plt.bar(range(len(indices)), importances[indices], align="center")
    plt.xticks(range(len(indices)), [feature_names[i] for i in indices], rotation=90)
    plt.tight_layout()
    plt.show()

def run_system_for_ticker(ticker):
    stock_df = db_handler.load_stock_data(ticker)
    if stock_df.empty: return

    full_df, learning_df = builder.add_features_and_target(stock_df.copy())

    training_results = trainer.train_and_evaluate(learning_df)
    if training_results[0] is None:
        print("❌ 모델 학습에 실패했거나 데이터가 부족하여 백테스팅을 중단합니다.")
        return
    
    model, X_test, y_test, y_pred, accuracy, report, feature_names = training_results
    
    print(f"\n--- {ticker} 메타 모델 학습 결과 ---")
    print(f"정확도 (신호 성공/실패 예측): {accuracy:.2%}")
    print(report)
    
    plot_feature_importance(model, feature_names)

    # 백테스팅은 X_test 기간에 해당하는 전체 데이터(full_df)를 사용해야 합니다.
    test_period_df = full_df.loc[X_test.index]
    backtester.run_backtest(test_period_df, X_test, y_pred)

if __name__ == "__main__":
    run_system_for_ticker('AAPL')