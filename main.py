# main.py (Ensemble Version - Final)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. 시스템의 모든 구성요소들을 불러옵니다. ---
from utils import db_handler
from features import builder
from data import economic_collector

# models 폴더에서 각 전문가(trainer)들을 모두 불러옵니다.
from models import lstm_trainer, gru_trainer, lgbm_trainer 

from strategies import backtester

def run_ensemble_system_for_ticker(ticker):
    """
    3개의 모델(LSTM, GRU, LightGBM)을 모두 사용하여 앙상블 예측을 수행하고,
    '다수결 원칙'에 따라 최종 투자 결정을 내리는 시스템입니다.
    """
    # --- 2. 데이터 준비 (모든 모델이 공유) ---
    stock_df = db_handler.load_stock_data(ticker)
    if stock_df.empty:
        print(f"❌ '{ticker}'에 대한 주가 데이터가 없어 시스템을 중단합니다.")
        return
    
    features_df, scaler = builder.add_features_and_target(stock_df.copy())

    # --- 3. 각 AI 전문가 모델 학습 및 예측 ---
    # 각 모델로부터 전체 기간에 대한 예측 'Series'만 받도록 통일합니다.
    lstm_predictions = lstm_trainer.train_and_evaluate(features_df)
    gru_predictions = gru_trainer.train_and_evaluate(features_df)
    
    # ▼▼▼ [수정된 부분] lgbm_trainer를 올바르게 호출하고, 마지막 값인 예측 Series만 받습니다. ▼▼▼
    lgbm_results = lgbm_trainer.train_and_evaluate(features_df)
    if lgbm_results is None:
        lgbm_predictions = None
    else:
        _, _, _, lgbm_predictions = lgbm_results
    # ▲▲▲ [수정된 부분] ▲▲▲

    if lstm_predictions is None or gru_predictions is None or lgbm_predictions is None:
        print("\n❌ 일부 모델 학습에 실패하여 앙상블 백테스팅을 중단합니다.")
        return

    # --- 4. 앙상블 (다수결 투표) ---
    print("\n🗳️ 세 모델의 예측을 종합하여 최종 투자 결정을 내립니다 (다수결)...")
    
    predictions_df = pd.DataFrame({
        'LSTM': lstm_predictions,
        'GRU': gru_predictions,
        'LGBM': lgbm_predictions
    }).fillna(0) # 딥러닝 모델의 예측 시작 전 빈 값을 0으로 채웁니다.
    
    predictions_df['buy_votes'] = predictions_df.sum(axis=1)
    ensemble_predictions = (predictions_df['buy_votes'] >= 2).astype(int)
    
    print("✅ 최종 앙상블 신호 생성 완료!")

    # --- 5. 최종 앙상블 신호로 백테스팅 실행 ---
    # 백테스팅 기간을 앙상블 예측이 있는 기간으로 필터링합니다.
    valid_backtest_df = stock_df.loc[ensemble_predictions.index]
    backtester.run_backtest(valid_backtest_df, ensemble_predictions.values)


if __name__ == "__main__":
    economic_collector.fetch_and_store_economic_data()
    run_ensemble_system_for_ticker('TSLA')