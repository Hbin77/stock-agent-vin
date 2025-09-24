# dashboard.py (Final Version)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- 시스템의 모든 구성요소들을 불러옵니다. ---
from utils import db_handler
from features import builder
from data import economic_collector, collector, news_collector
from models import lstm_trainer, gru_trainer, lgbm_trainer 
from strategies import backtester

# --- 함수 정의 ---
# Streamlit의 캐싱 기능을 사용하여, 동일한 종목에 대한 분석 결과를 저장하고 빠르게 재사용합니다.
@st.cache_data(show_spinner=False) # 스피너를 직접 제어하기 위해 False로 설정
def run_full_analysis(ticker):
    """선택된 티커에 대해 데이터 준비부터 앙상블 예측까지 모든 과정을 수행합니다."""
    
    # 1. 데이터 준비
    stock_df = db_handler.load_stock_data(ticker)
    if stock_df.empty:
        st.error(f"'{ticker}'에 대한 주가 데이터가 없습니다.")
        return None, None
    
    features_df, _ = builder.add_features_and_target(stock_df.copy())

    # 2. 모델 학습 및 예측
    with st.spinner('🧠 LSTM 모델이 과거 데이터를 학습하고 있습니다...'):
        lstm_predictions = lstm_trainer.train_and_evaluate(features_df)
    with st.spinner('🧠 GRU 모델이 과거 데이터를 학습하고 있습니다...'):
        gru_predictions = gru_trainer.train_and_evaluate(features_df)
    with st.spinner('🌳 LightGBM 모델이 과거 데이터를 학습하고 있습니다...'):
        lgbm_results = lgbm_trainer.train_and_evaluate(features_df)
    
    if lgbm_results:
        _, _, _, lgbm_predictions = lgbm_results
    else:
        lgbm_predictions = None

    if lstm_predictions is None or gru_predictions is None or lgbm_predictions is None:
        st.error("일부 모델 학습에 실패했습니다.")
        return None, None

    # 3. 앙상블 예측
    with st.spinner('🗳️ 3개 모델의 예측을 종합하여 최종 투자 신호를 생성합니다...'):
        predictions_df = pd.DataFrame({
            'LSTM': lstm_predictions,
            'GRU': gru_predictions,
            'LGBM': lgbm_predictions
        }).fillna(0)
    
        predictions_df['buy_votes'] = predictions_df.sum(axis=1)
        ensemble_predictions = (predictions_df['buy_votes'] >= 2).astype(int)
        time.sleep(1) # 작업 완료 메시지를 보여주기 위한 약간의 딜레이
    
    st.success("모든 분석이 완료되었습니다!")
    return stock_df, ensemble_predictions

# --- 대시보드 UI 구성 ---
st.set_page_config(layout="wide") # 페이지를 넓게 사용
st.title('📈 나만의 AI 주식 투자 에이전트')

st.markdown("""
이 대시보드는 **LSTM, GRU, LightGBM** 세 가지 AI 모델의 예측을 종합(앙상블)하여,
가장 확률 높은 투자 신호를 생성합니다. 아래 순서에 따라 에이전트를 실행해보세요.
""")

# --- 1. 데이터 업데이트 섹션 ---
with st.expander("1. 모든 데이터 최신 상태로 업데이트하기 (필요 시 클릭)"):
    if st.button('업데이트 실행'):
        with st.spinner('📈 주가 데이터를 업데이트하는 중... (1~2분 소요)'):
            collector.run_full_pipeline()
        with st.spinner('📰 뉴스 데이터를 업데이트하는 중... (1~2분 소요)'):
            db_conn = db_handler.get_db_connection()
            if db_conn:
                ticker_list_for_news = news_collector.get_all_tickers(db_conn)
                collected_news = news_collector.fetch_finnhub_news_for_all_tickers(ticker_list_for_news)
                news_collector.bulk_insert_news(db_conn, collected_news)
                db_conn.close()
        with st.spinner('🏛️ 경제 지표를 업데이트하는 중...'):
            economic_collector.fetch_and_store_economic_data()
        st.success('모든 데이터 업데이트 완료!')
        st.info("페이지를 새로고침하여 새로운 데이터로 분석을 시작하세요.")

# --- 2. 분석 실행 섹션 ---
st.header('2. 분석 및 백테스트 실행')

try:
    ticker_list = db_handler.get_stock_tickers()
    if ticker_list:
        selected_ticker = st.selectbox(
            '분석할 주식 티커를 선택하세요:', 
            ticker_list, 
            index=ticker_list.index('AAPL') if 'AAPL' in ticker_list else 0
        )

        if st.button(f"'{selected_ticker}' 분석 시작"):
            stock_data, final_predictions = run_full_analysis(selected_ticker)
            
            if stock_data is not None and final_predictions is not None:
                st.subheader(f"'{selected_ticker}' 백테스팅 결과")
                
                # 백테스팅 결과를 차트로 그리기
                fig, ax = plt.subplots(figsize=(15, 7))
                
                # 백테스팅 함수 호출 (이전과 동일하지만, dashboard.py 내부에서 처리)
                portfolio_values, total_return, buy_and_hold_return = backtester.run_backtest_for_dashboard(stock_data, final_predictions.values)
                
                # 차트 그리기
                valid_indices = stock_data.index[-len(portfolio_values):]
                ax.plot(valid_indices, portfolio_values, label='Ensemble AI Strategy', linewidth=2)
                ax.plot(valid_indices, (10000 / stock_data['close'].loc[valid_indices[0]]) * stock_data['close'].loc[valid_indices], label='Buy and Hold Strategy')
                ax.set_title(f'Backtesting Results for {selected_ticker}', fontsize=16)
                ax.set_ylabel('Portfolio Value ($)')
                ax.legend(fontsize=12)
                st.pyplot(fig)

                # 결과 요약 (컬럼으로 보기 좋게 정렬)
                col1, col2 = st.columns(2)
                col1.metric(label="AI 전략 최종 수익률", value=f"{total_return:.2%}")
                col2.metric(label="단순 보유 전략 수익률", value=f"{buy_and_hold_return:.2%}")

                # 오늘의 신호
                st.subheader("최신 투자 신호")
                today_signal = final_predictions.iloc[-1]
                if today_signal == 1:
                    st.success(f"📈 매수 (Buy) - AI 위원회는 '{selected_ticker}'의 상승 가능성을 높게 보고 있습니다.")
                else:
                    st.error(f"📉 매도 또는 관망 (Sell or Hold) - AI 위원회는 지금이 매수 적기가 아니라고 판단합니다.")
    else:
        st.warning("데이터베이스에서 종목 목록을 불러올 수 없습니다. '데이터 업데이트'를 먼저 실행해주세요.")
except Exception as e:
    st.error(f"대시보드를 로드하는 중 오류가 발생했습니다: {e}")