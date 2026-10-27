import { useEffect, useRef } from "react";
import { suggestedQuestions } from "../data/demo";
import { useChat } from "../hooks/useChat";

export default function ChatPanel({ onComplete }) {
  const chatHistoryRef = useRef(null);
  const { chatInput, setChatInput, chatLoading, messages, sendChatMessage, clearConversation } =
    useChat(onComplete);
  useEffect(() => {
    if (chatHistoryRef.current)
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
  }, [messages]);
  return (
    <div className="card featured-chat-card">
      <div className="card-header">
        <div>
          <div className="section-label">Asistencia digital</div>
          <h3>Asistente virtual del ciudadano</h3>
        </div>
        <div className="chat-header-actions">
          <div className="tag tag-violet">IA conversacional</div>
          <button
            className="secondary-btn small-btn"
            onClick={clearConversation}
            disabled={chatLoading}
          >
            Nueva conversación
          </button>
        </div>
      </div>

      <div className="chat-area">
        <div className="chat-history" ref={chatHistoryRef} aria-live="polite">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`chat-message ${
                message.role === "user" ? "user-message" : "bot-message"
              } ${message.temporary ? "temporary-message" : ""}`}
            >
              <div className="chat-role">
                {message.role === "user" ? "Ciudadano" : "Asistente IA"}
              </div>

              <p>{message.content}</p>

              {message.role === "assistant" &&
                message.guard_action &&
                message.guard_action !== "allowed" && (
                  <div className="chat-guard-alert">
                    <strong>Trend AI Guard:</strong> {message.guard_reason || "Contenido bloqueado"}
                  </div>
                )}

              {message.role === "assistant" &&
                message.guard_action === "allowed" &&
                message.guard_source === "trend_ai_guard" && (
                  <div className="chat-guard-ok">Validado por Trend AI Guard</div>
                )}
            </div>
          ))}
        </div>

        <div className="suggested-questions">
          {suggestedQuestions.map((question) => (
            <button
              key={question}
              className="suggestion-chip"
              onClick={() => sendChatMessage(question)}
              disabled={chatLoading}
            >
              {question}
            </button>
          ))}
        </div>

        <div className="chat-input-row">
          <input
            type="text"
            aria-label="Consulta al asistente"
            maxLength={8000}
            placeholder="Escribe tu consulta al asistente municipal..."
            value={chatInput}
            onChange={(event) => setChatInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.nativeEvent.isComposing) sendChatMessage();
            }}
            disabled={chatLoading}
          />
          <button className="primary-btn" onClick={() => sendChatMessage()} disabled={chatLoading}>
            {chatLoading ? "Enviando..." : "Enviar"}
          </button>
        </div>

        <div className="micro-copy">Asistente protegido con capacidades de seguridad TrendAI</div>
      </div>
    </div>
  );
}
