import React, { useState, useRef, useEffect } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";

function App() {
  const [sessions, setSessions] = useState({ "Chat 1": [] });
  const [currentChat, setCurrentChat] = useState("Chat 1");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const messages = sessions[currentChat] || [];
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ✅ SEND MESSAGE
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    const updatedMessages = [...messages, userMessage];

    setSessions((prev) => ({
      ...prev,
      [currentChat]: updatedMessages,
    }));

    setInput("");
    setLoading(true);

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: input,
          chat_id: currentChat,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let botMessage = "";

      setSessions((prev) => ({
        ...prev,
        [currentChat]: [
          ...updatedMessages,
          { role: "assistant", content: "" },
        ],
      }));

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        botMessage += decoder.decode(value);

        setSessions((prev) => {
          const updated = [...updatedMessages];
          updated.push({
            role: "assistant",
            content: botMessage,
          });

          return {
            ...prev,
            [currentChat]: updated,
          };
        });
      }

    } catch (err) {
      console.error(err);
    }

    setLoading(false);
  };

  // ✅ NEW CHAT
  const newChat = () => {
    const id = `Chat ${Object.keys(sessions).length + 1}`;

    setSessions((prev) => ({
      ...prev,
      [id]: [],
    }));

    setCurrentChat(id);
  };

  return (
    <div className="container">

      {/* Sidebar */}
      <div className="sidebar">
        <h2>💬 Chats</h2>
        <button onClick={newChat}>+ New Chat</button>

        {Object.keys(sessions).map((chat) => (
          <div
            key={chat}
            className={`chat-item ${chat === currentChat ? "active" : ""}`}
            onClick={() => setCurrentChat(chat)}
          >
            {chat}
          </div>
        ))}
      </div>

      {/* Chat Area */}
      <div className="chat-area">

        {/* Messages */}
        <div className="messages">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`message ${msg.role === "user" ? "user" : "bot"}`}
            >
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          ))}

          {loading && (
            <div className="message bot typing">Typing...</div>
          )}

          <div ref={endRef}></div>
        </div>

        {/* Input */}
        <div className="input-box">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything (research)..."
          />
          <button onClick={sendMessage}>Send</button>
        </div>

      </div>
    </div>
  );
}

export default App;
