import { NextResponse } from "next/server"

export async function POST(req: Request) {
  try {
    const body = await req.json()

    const lastMessage =
      body.messages?.[body.messages.length - 1]?.content || ""

    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        query: lastMessage,
        chat_id: "chat-ui"
      })
    })

    const text = await response.text()

    // ✅ IMPORTANT: return JSON (not raw stream)
    return NextResponse.json({
      role: "assistant",
      content: text
    })

  } catch (error) {
    console.error("API ERROR:", error)

    return NextResponse.json({
      role: "assistant",
      content: "Error connecting to backend"
    })
  }
}
``