# main.py (Ensemble Version)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. 시스템의 모든 구성요소들을 불러옵니다. ---
from models import lstm_trainer
from utils import db_handler
from features import builder
from data import economic_collector

# models 폴더에서 각 전문가(trainer)들을 모두 불러옵니다.
from models import lstm_trainer, gru_trainer 

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
    
    # 피처 엔지니어링 (기술적 지표 + 경제 지표)
    features_df, scaler = builder.add_features_and_target(stock_df.copy())

    # --- 3. 각 AI 전문가 모델 학습 및 예측 ---
    # 각 모델로부터 전체 기간에 대한 예측 결과를 받습니다.
    lstm_predictions = lstm_trainer.train_and_evaluate(features_df)
    gru_predictions = gru_trainer.train_and_evaluate(features_df)
    _, _, _, lgbm_predictions = lstm_trainer.train_and_evaluate(features_df) # lgbm은 결과 4개를 반환

    # 모델 중 하나라도 학습에 실패하면 시스템을 중단합니다.
    if lstm_predictions is None or gru_predictions is None or lgbm_predictions is None:
        print("\n❌ 일부 모델 학습에 실패하여 앙상블 백테스팅을 중단합니다.")
        return

    # --- 4. 앙상블 (다수결 투표) ---
    print("\n🗳️ 세 모델의 예측을 종합하여 최종 투자 결정을 내립니다 (다수결)...")
    
    # 각 모델의 예측을 하나의 DataFrame으로 합칩니다.
    predictions_df = pd.DataFrame({
        'LSTM': lstm_predictions,
        'GRU': gru_predictions,
        'LGBM': lgbm_predictions
    })
    
    # 각 날짜별로 '매수(1)' 신호의 개수를 셉니다.
    predictions_df['buy_votes'] = predictions_df.sum(axis=1)
    
    # "3명 중 2명 이상이 '매수'에 투표하면 최종 '매수'로 결정"
    ensemble_predictions = (predictions_df['buy_votes'] >= 2).astype(int)
    
    print("✅ 최종 앙상블 신호 생성 완료!")

    # --- 5. 최종 앙상블 신호로 백테스팅 실행 ---
    # 백테스팅은 원본 주가 데이터와 최종 신호를 사용합니다.
    # 테스트 기간은 예측이 시작되는 시점부터로 자동 필터링됩니다.
    backtester.run_backtest(stock_df, ensemble_predictions.values)


if __name__ == "__main__":
    economic_collector.fetch_and_store_economic_data()
    run_ensemble_system_for_ticker('AAPL')