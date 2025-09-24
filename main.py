# main.py (GUI-Free, Deadlock-Free Final Version)

import os

# ▼▼▼ [최종 수정] macOS 교착상태 방지를 위한 환경 변수 설정 ▼▼▼
# 다른 어떤 코드보다도 가장 먼저 실행되어야 합니다.
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
# ▲▲▲ [최종 수정] ▲▲▲

import pandas as pd
import numpy as np

# --- 시스템의 모든 구성요소들을 불러옵니다 (GUI 관련 제외) ---
from utils import db_handler, screener, stock_classifier
from features import builder
from data import economic_collector
from models import lstm_trainer, gru_trainer, lgbm_trainer
from strategies import backtester

def run_ensemble_system_for_ticker(ticker):
    """3개의 AI 모델을 사용한 앙상블 시스템을 실행합니다."""
    print(f"\n{'='*50}\n🔬 '{ticker}'에 대한 상세 분석을 시작합니다.\n{'='*50}")

    stock_df = db_handler.load_stock_data(ticker)
    if stock_df.empty:
        print(f"❌ '{ticker}'에 대한 주가 데이터가 없어 시스템을 중단합니다.")
        return

    features_df, _ = builder.add_features_and_target(stock_df.copy())
    if features_df.empty:
        print(f"❌ '{ticker}' 피처 생성 실패. 데이터가 부족할 수 있습니다.")
        return

    # --- 각 AI 전문가 모델 학습 및 예측 ---
    lstm_predictions = lstm_trainer.train_and_evaluate(features_df)
    gru_predictions = gru_trainer.train_and_evaluate(features_df)
    lgbm_predictions = lgbm_trainer.train_and_evaluate(features_df)

    if lstm_predictions is None or gru_predictions is None or lgbm_predictions is None:
        print("\n❌ 일부 모델 학습 실패로 백테스팅을 중단합니다.")
        return

    # --- 앙상블 (다수결 투표) ---
    print("\n🗳️ 세 모델의 예측을 종합하여 최종 투자 결정을 내립니다 (다수결)...")

    predictions_df = pd.DataFrame({
        'LSTM': lstm_predictions,
        'GRU': gru_predictions,
        'LGBM': lgbm_predictions
    }).fillna(0) # 예측이 없는 구간(NaN)은 0(매도)으로 처리

    predictions_df['buy_votes'] = predictions_df.sum(axis=1)
    ensemble_predictions = (predictions_df['buy_votes'] >= 2).astype(int)

    print("✅ 최종 앙상블 신호 생성 완료!")

    # --- 최종 앙상블 신호로 백테스팅 실행 (GUI 없음) ---
    backtester.run_backtest(stock_df, ensemble_predictions.values)


if __name__ == "__main__":
    # 1. (필수) 주식 스타일 정보를 최신 상태로 업데이트합니다.
    stock_classifier.classify_stocks_pro()

    # 2. (필수) 경제 지표 데이터를 최신으로 업데이트합니다.
    economic_collector.fetch_and_store_economic_data()
    
    # 3. AI 스크리너를 통해 오늘 투자할 유망 종목을 추천받습니다.
    recommended_tickers = screener.screen_stocks()

    # 4. 추천받은 모든 종목에 대해 상세 분석 및 백테스팅을 자동으로 실행합니다.
    if recommended_tickers:
        for ticker in recommended_tickers:
            run_ensemble_system_for_ticker(ticker)
    else:
        print("\n💡 오늘은 추천 종목이 없으므로 상세 분석을 진행하지 않습니다.")