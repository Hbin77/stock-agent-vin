import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from utils import db_handler

def analyze_and_update_sentiment():
    """DB에서 감성 점수가 없는 뉴스를 가져와 점수를 계산하고 업데이트합니다."""
    print("\n🎭 감성 분석을 시작합니다...")
    
    # 1. 사전 학습된 FinBERT 모델 및 토크나이저 로드
    # 이 과정은 처음 실행 시 모델 파일을 다운로드하므로 시간이 걸릴 수 있습니다.
    print("FinBERT 모델을 로드합니다...")
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    print("✅ 모델 로드 완료!")

    conn = None
    try:
        conn = db_handler.get_db_connection()
        with conn.cursor() as cursor:
            # 2. 아직 감성 분석이 수행되지 않은 뉴스만 선택
            cursor.execute("SELECT id, title FROM stock_news WHERE sentiment_score IS NULL")
            news_to_analyze = cursor.fetchall()

            if not news_to_analyze:
                print("💡 분석할 새로운 뉴스가 없습니다.")
                return

            print(f"{len(news_to_analyze)}건의 뉴스에 대한 감성 분석을 진행합니다.")
            
            # 3. 각 뉴스 제목에 대해 감성 점수 계산
            for news_id, title in news_to_analyze:
                inputs = tokenizer(title, return_tensors="pt", padding=True, truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = model(**inputs)
                
                # 소프트맥스 함수를 적용하여 확률로 변환
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                # 점수 계산: (긍정 확률 - 부정 확률)
                # 결과는 -1(매우 부정적) ~ +1(매우 긍정적) 사이의 값이 됨
                sentiment_score = probs[0][1].item() - probs[0][0].item()
                
                # 4. 계산된 점수를 DB에 업데이트
                update_sql = "UPDATE stock_news SET sentiment_score = %s WHERE id = %s"
                cursor.execute(update_sql, (sentiment_score, news_id))

            conn.commit()
            print(f"✅ {len(news_to_analyze)}건의 뉴스 감성 점수 업데이트 완료!")

    except Exception as e:
        print(f"❌ 감성 분석 중 오류 발생: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    analyze_and_update_sentiment()