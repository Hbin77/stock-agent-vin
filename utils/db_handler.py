# features/builder.py

import pandas as pd
import pandas_ta as ta
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from utils import db_handler
import yfinance as yf

def create_lstm_dataset(X, y, time_steps=60):
    """LSTM 모델 학습을 위한 시퀀스 데이터셋을 생성합니다."""
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        v = X.iloc[i:(i + time_steps)].values
        Xs.append(v)
        ys.append(y.iloc[i + time_steps])
    return np.array(Xs), np.array(ys)

def add_features_and_target(df, ticker):
    """LSTM 모델에 맞게 피처, 타겟을 생성하고 데이터를 정규화합니다."""
    print("\n🛠️ LSTM을 위한 피처 엔지니어링 및 데이터 전처리를 시작합니다...")

    # 1. 경제 지표 데이터 로드 및 병합
    df_econ = db_handler.load_economic_data()
    if not df_econ.empty:
        df = pd.merge(df, df_econ, left_index=True, right_index=True, how='left')
        df.ffill(inplace=True)
        print("✅ 주가 데이터와 경제 지표 데이터 병합 완료.")

    # 2. 뉴스 감성 데이터 로드 및 피처 생성
    df_news = db_handler.load_news_data(ticker)
    if not df_news.empty:
        sentiment_daily = df_news.groupby(df_news['published_at'].dt.date)['sentiment_score'].mean().reset_index()
        sentiment_daily.rename(columns={'published_at': 'time', 'sentiment_score': 'sentiment_avg'}, inplace=True)
        sentiment_daily['time'] = pd.to_datetime(sentiment_daily['time'])
        sentiment_daily.set_index('time', inplace=True)

        df = pd.merge(df, sentiment_daily, left_index=True, right_index=True, how='left')
        # ChainedAssignmentError 방지를 위해 수정
        df['sentiment_avg'] = df['sentiment_avg'].fillna(0)
        df['sentiment_ma5'] = df['sentiment_avg'].rolling(window=5).mean()
        print("✅ 뉴스 감성 데이터 병합 및 피처 생성 완료.")

    # 3. 시장 상황(Market Regime) 피처 추가
    try:
        spy_df = yf.download('SPY', start=df.index.min(), end=df.index.max(), auto_adjust=True)
        spy_ma200 = spy_df['Close'].rolling(window=200).mean()

        # reindex를 사용하여 df의 인덱스에 맞게 spy_ma200을 정렬 (오류 해결의 핵심)
        aligned_spy_ma200 = spy_ma200.reindex(df.index, method='ffill')

        df['market_regime'] = (df['close'] > aligned_spy_ma200).astype(int)
        df['market_regime'].fillna(method='ffill', inplace=True) # 혹시 모를 NaN 값을 이전 값으로 채움
        print("✅ 시장 상황(Market Regime) 피처 생성 완료.")
    except Exception as e:
        print(f"⚠️ 시장 상황 피처 생성 실패: {e}")
        df['market_regime'] = 0

    # 4. 기술적 지표 추가
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, append=True)
    df.ta.bbands(length=20, append=True)
    df.ta.obv(append=True)
    df['OBV_MA10'] = df['OBV'].rolling(window=10).mean()
    df.ta.atr(length=14, append=True)
    df.ta.stoch(k=14, d=3, append=True)

    # 5. 타겟 변수 생성
    look_forward_period = 10
    target_return = 0.05
    stop_loss_return = -0.02
    df['target'] = 0

    for i in range(len(df) - look_forward_period):
        entry_price = df['close'].iloc[i]
        future_prices = df['close'].iloc[i+1 : i+1+look_forward_period]
        take_profit_price = entry_price * (1 + target_return)
        stop_loss_price = entry_price * (1 + stop_loss_return)
        for price in future_prices:
            if price >= take_profit_price:
                df.loc[df.index[i], 'target'] = 1; break
            elif price <= stop_loss_price:
                df.loc[df.index[i], 'target'] = 0; break

    df.dropna(inplace=True)

    # 6. 데이터 정규화
    features_to_scale = [
        'close', 'RSI_14', 'MACD_12_26_9', 'BBP_20_2.0_2.0',
        'OBV', 'OBV_MA10', 'ATRr_14', 'STOCHk_14_3_3', 'STOCHd_14_3_3',
        'fed_rate', 'usd_krw',
        'sentiment_avg', 'sentiment_ma5', 'market_regime'
    ]

    features_to_scale = [col for col in features_to_scale if col in df.columns]

    if not features_to_scale:
        print("⚠️ 정규화할 피처가 없습니다.")
        return pd.DataFrame(), None

    scaler = MinMaxScaler(feature_range=(0, 1))
    df[features_to_scale] = scaler.fit_transform(df[features_to_scale])

    print("✅ 피처 엔지니어링 및 데이터 전처리 완료!")
    return df, scaler