from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agent import build_graph
from db import init_db, save_messages, load_messages

app = FastAPI()

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = build_graph()


class Request(BaseModel):
    query: str
    chat_id: str


@app.post("/chat")
def chat(req: Request):

    def generate():
        try:
            data = load_messages(req.chat_id)

            result = agent.invoke({
                "query": req.query,
                "messages": data.get("messages", []),
                "history": data.get("history", []),
                "search_results": [],
                "report": ""
            })

            save_messages(req.chat_id, {
                "messages": result["messages"],
                "history": result["history"]
            })

            yield result["report"]

        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")