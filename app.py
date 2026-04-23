# %% [markdown]
# # AI 분석 서버 (FastAPI + gemma4:e2b/GPT-4o)
# ### 필수 패키지 설치 가이드
# ```bash
# # pip install fastapi uvicorn ollama openai python-multipart python-dotenv pillow
# ```

# %%
import os
import base64
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import ollama
from openai import OpenAI
import uvicorn
import io
from PIL import Image
from chandra.model import InferenceManager
from chandra.model.schema import BatchInputItem

# 데이터베이스 모듈 임포트
from database import connectDatabase, createTable, saveAnalysisResult

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# Chandra OCR 모델 전역 변수 (지연 로딩)
chandraModel = None

def getChandraModel():
    """ Chandra OCR 모델을 초기화하고 반환합니다. """
    global chandraModel
    if chandraModel is None:
        # 허깅페이스(hf) 방식을 사용하여 모델을 로드합니다 (최초 1회)
        chandraModel = InferenceManager(method="hf")
    return chandraModel

# 서버 시작 시 DB 연결 확인 및 테이블 생성
@app.on_event("startup")
def startup_event():
    conn = connectDatabase()
    if conn and conn.is_connected():
        print("✅ 데이터베이스 연결 성공!")
        createTable()  # 테이블이 없으면 생성
        conn.close()
    else:
        print("❌ 데이터베이스 연결 실패! .env 설정을 확인하세요.")

# CORS 설정 (가이드 준수: 모든 Origin/Method/Header 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def callGptModel(imageBase64, promptText):
    """ OpenAI GPT-4o 모델을 호출하여 이미지를 분석합니다. """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": promptText},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imageBase64}"}}
                    ]
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

def callOllamaModel(imageBytes, promptText, modelName="gemma4:e2b"):
    """ 로컬 Ollama 모델을 호출하여 이미지를 분석합니다. """
    try:
        response = ollama.generate(
            model=modelName,
            prompt=promptText,
            images=[imageBytes]
        )
        return response['response']
    except Exception as e:
        return str(e)

def callChandraOcrModel(imageBytes, promptText):
    """ Chandra OCR 2 모델을 호출하여 이미지에서 텍스트를 추출하고 분석합니다. """
    try:
        # 바이트 데이터를 PIL 이미지로 변환
        image = Image.open(io.BytesIO(imageBytes))
        
        # 모델 로드 (첫 호출 시 로드)
        model = getChandraModel()
        
        # 입력 데이터 생성 (BatchInputItem 형식)
        currentPrompt = promptText if promptText else "이미지의 내용을 텍스트로 추출해줘."
        batchItem = BatchInputItem(image=image, prompt=currentPrompt)
        
        # 이미지 처리 및 결과 생성 (리스트 형태로 결과 반환됨)
        results = model.generate([batchItem])
        
        # 결과 추출
        if results and len(results) > 0:
            # BatchOutputItem 객체에는 markdown, html, raw 등의 속성이 있습니다.
            return results[0].markdown
        
        return "분석 결과가 없습니다."
    except Exception as e:
        return f"Chandra OCR 분석 오류: {str(e)}"

@app.post("/analyze")
async def analyzeImage(
    prompt: str = Form(...), 
    model: str = Form("CHANDRA"), # 기본값 설정으로 422 에러 방지
    file: UploadFile = File(...)
):
    """ 
    이미지 파일, 질문, 선택된 모델을 받아 분석합니다. 
    """
    try:
        # 파일 데이터 읽기
        fileContent = await file.read()
        useModel = model.upper() # 대문자로 통일
        
        # 분석 결과 변수 초기화
        analysisResult = ""

        # 모델 스위칭 로직
        if useModel == "GPT":
            imageBase64 = base64.b64encode(fileContent).decode('utf-8')
            analysisResult = callGptModel(imageBase64, prompt)
        elif useModel == "OLLAMA":
            analysisResult = callOllamaModel(fileContent, prompt)
        elif useModel == "CHANDRA":
            analysisResult = callChandraOcrModel(fileContent, prompt)
        else:
            analysisResult = "지원하지 않는 모델 설정입니다."

        # (가이드 준수 예시) 특정 반복 작업이 필요할 경우 리스트 컴프리헨션 금지
        # 예: 결과 텍스트의 길이를 리스트 형태로 저장할 경우
        wordList = analysisResult.split()
        wordLengths = []
        for i in range(0, len(wordList)):
            wordLengths.append(len(wordList[i]))

        # 분석 결과 저장 로직 추가
        saveAnalysisResult(prompt, useModel, analysisResult)

        return {
            "success": True,
            "message": "분석 성공",
            "data": {
                "model": useModel,
                "result": analysisResult
            }
        }
    except Exception as e:
        # 가이드 규정 에러 JSON 형식 반환
        return {"success": false, "message": str(e)}

if __name__ == "__main__":
    # 주피터 노트북 내 실행을 위한 uvicorn 설정
    # 실제 구동 시에는 셀을 실행하거나 터미널에서 구동
    uvicorn.run(app, host="0.0.0.0", port=8000)


