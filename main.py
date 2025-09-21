# main.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utils import db_handler
from features import builder
from models import trainer
from strategies import backtester

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
    """특정 티커에 대해 데이터 로드부터 백테스팅까지 전체 시스템을 실행합니다."""
    stock_df = db_handler.load_stock_data(ticker)
    news_df = db_handler.load_news_data(ticker)
    if stock_df.empty: return

    # builder는 이제 하나의 완성된 DataFrame만 반환합니다.
    features_df = builder.add_features_and_target(stock_df, news_df)    
    # trainer는 이 features_df로 바로 학습합니다.
    training_results = trainer.train_and_evaluate(features_df)
    if training_results[0] is None:
        print("\n❌ 모델 학습에 실패했거나 데이터가 부족하여 백테스팅을 중단합니다.")
        return
    
    model, X_test, y_test, y_pred, accuracy, report, feature_names = training_results
    
    print(f"\n--- {ticker} 모델 학습 결과 ---")
    print(f"정확도: {accuracy:.2%}")
    print(report)
    
    plot_feature_importance(model, feature_names)

    # 백테스팅은 X_test 기간에 해당하는 원본 데이터(features_df)를 사용합니다.
    test_period_df = features_df.loc[X_test.index]
    # backtester 호출 방식을 수정하여 y_pred를 직접 전달합니다.
    backtester.run_backtest(test_period_df, y_pred)

if __name__ == "__main__":
    run_system_for_ticker('TSLA')