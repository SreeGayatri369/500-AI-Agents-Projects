import { NextRequest } from "next/server"

export async function POST(req: NextRequest) {
  const body = await req.json()

  const response = await fetch("http://localhost:3000/api/chat/custom", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  })

  const data = await response.json()

  return new Response(JSON.stringify(data), {
    headers: { "Content-Type": "application/json" }
  })
}