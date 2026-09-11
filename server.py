import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

PORT = 8000
BASE_DIR = Path(__file__).resolve().parent
EXPECTED_HEADER = "日付,商品名,カテゴリ,地域,数量,単価,売上金額"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = FastAPI()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@app.get("/api/csvs")
def list_csvs():
    names = []
    for path in sorted(BASE_DIR.glob("*.csv")):
        try:
            with open(path, encoding="utf-8") as f:
                header = f.readline().strip()
        except (OSError, UnicodeDecodeError):
            continue
        if header == EXPECTED_HEADER:
            names.append(path.name)
    return names


@app.post("/api/chat")
def chat(req: ChatRequest):
    if openai_client is None:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY が設定されていません。.env.example を .env にコピーしてAPIキーを設定してください。",
        )
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages is empty")

    system_prompt = {
        "role": "system",
        "content": "あなたは売上ダッシュボードのアシスタントです。ユーザーの質問に簡潔に日本語で答えてください。",
    }
    openai_messages = [system_prompt] + [m.model_dump() for m in req.messages]

    try:
        completion = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=openai_messages,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API呼び出しに失敗しました: {e}")

    return {"reply": completion.choices[0].message.content}


# 静的ファイル(index.html, CSVなど)の配信。APIルートの後にマウントすること。
app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    print(f"売上ダッシュボードを配信中: http://127.0.0.1:{PORT}/")
    uvicorn.run(app, host="127.0.0.1", port=PORT)
