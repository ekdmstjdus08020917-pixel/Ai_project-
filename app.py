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

# 환경 변수 로드
load_dotenv()

app = FastAPI()

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

def callOllamaModel(imageBytes, promptText):
    """ 로컬 Ollama(gemma4:e2b) 모델을 호출하여 이미지를 분석합니다. """
    try:
        modelName = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
        response = ollama.generate(
            model=modelName,
            prompt=promptText,
            images=[imageBytes]
        )
        return response['response']
    except Exception as e:
        return str(e)

@app.post("/analyze")
async def analyzeImage(prompt: str = Form(...), file: UploadFile = File(...)):
    """ 
    이미지 파일과 질문을 받아 지정된 모델로 분석합니다. 
    가이드에 따라 에러 처리 JSON 형식을 준수합니다.
    """
    try:
        # 파일 데이터 읽기
        fileContent = await file.read()
        useModel = os.getenv("USE_MODEL", "OLLAMA")
        
        # 분석 결과 변수 초기화
        analysisResult = ""

        # 모델 스위칭 로직 (if-elif-else 명확히 구분)
        if useModel == "GPT":
            # GPT 호출을 위한 base64 인코딩
            imageBase64 = base64.b64encode(fileContent).decode('utf-8')
            analysisResult = callGptModel(imageBase64, prompt)
        elif useModel == "OLLAMA":
            # Ollama 호출
            analysisResult = callOllamaModel(fileContent, prompt)
        else:
            analysisResult = "지원하지 않는 모델 설정입니다."

        # (가이드 준수 예시) 특정 반복 작업이 필요할 경우 리스트 컴프리헨션 금지
        # 예: 결과 텍스트의 길이를 리스트 형태로 저장할 경우
        wordList = analysisResult.split()
        wordLengths = []
        for i in range(0, len(wordList)):
            wordLengths.append(len(wordList[i]))

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


