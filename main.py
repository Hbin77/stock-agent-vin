import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utils import db_handler
from features import builder
from models import trainer
from strategies import backtester
from data import economic_collector # economic_collector 임포트 추가

def plot_feature_importance(model, feature_names):
    """학습된 모델의 피처 중요도를 시각화합니다."""
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    plt.figure(figsize=(12, 6))
    plt.title("Feature Importances")
    plt.bar(range(len(indices)), importances[indices], align="center")
    plt.xticks(range(len(indices)), [feature_names[i] for i in indices], rotation=90)
    plt.tight_layout()
    plt.show()

def run_system_for_ticker(ticker):
    """LSTM 기반 최종 시스템을 실행합니다."""
    stock_df = db_handler.load_stock_data(ticker)
    if stock_df.empty: return
    
    features_df, scaler = builder.add_features_and_target(stock_df.copy())
    
    training_results = trainer.train_and_evaluate(features_df)
    if training_results[0] is None:
        print("\n❌ 모델 학습에 실패하여 백테스팅을 중단합니다.")
        return
    
    model, test_indices, y_test, y_pred, accuracy, report, feature_names = training_results
    
    print(f"\n--- {ticker} LSTM 모델 학습 결과 ---")
    print(f"정확도: {accuracy:.2%}")
    print(report)
    
    test_period_df = stock_df.loc[test_indices]
    backtester.run_backtest(test_period_df, y_pred)

if __name__ == "__main__":
    economic_collector.fetch_and_store_economic_data()
    run_system_for_ticker('AAPL')