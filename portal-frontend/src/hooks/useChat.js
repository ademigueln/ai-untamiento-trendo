import { useRef, useState } from "react";
import { api } from "../services/api";

const welcome = {
  role: "assistant",
  content:
    "Soy el asistente del AI-untamiento de Trendo. Puedo orientarte sobre trámites y documentación municipal. Esta es una demostración sin acceso a expedientes reales.",
};

export function useChat(onComplete) {
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [messages, setMessages] = useState([welcome]);
  const token = useRef(null); // Token efímero por pestaña; no persiste en almacenamiento compartido.
  const busy = useRef(false);

  const sendChatMessage = async (forcedMessage = null) => {
    const message = (forcedMessage ?? chatInput).trim();
    if (!message || busy.current) return;
    busy.current = true;
    setChatLoading(true);
    setChatInput("");
    setMessages((previous) => [
      ...previous,
      { role: "user", content: message },
      { role: "assistant", content: "Preparando respuesta…", temporary: true },
    ]);
    try {
      const data = await api("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, conversation_id: token.current }),
      });
      token.current = data.conversation_id;
      setMessages((previous) => [
        ...previous.filter((item) => !item.temporary),
        { role: "assistant", content: data.reply, ...data },
      ]);
    } catch (error) {
      if (error.data?.conversation_id) token.current = error.data.conversation_id;
      if (error.status === 404) token.current = null;
      setMessages((previous) => [
        ...previous.filter((item) => !item.temporary),
        {
          role: "assistant",
          content: error.message,
          guard_action: error.data?.guard_action,
          guard_reason: error.data?.guard_reason,
        },
      ]);
    } finally {
      busy.current = false;
      setChatLoading(false);
      onComplete();
    }
  };

  const clearConversation = async () => {
    if (busy.current) return;
    busy.current = true;
    setChatLoading(true);
    try {
      if (token.current) await api(`/api/chat/${token.current}`, { method: "DELETE" });
      token.current = null;
      setMessages([welcome]);
      setChatInput("");
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        { role: "assistant", content: `No se ha podido borrar la conversación: ${error.message}` },
      ]);
    } finally {
      busy.current = false;
      setChatLoading(false);
    }
  };
  return { chatInput, setChatInput, chatLoading, messages, sendChatMessage, clearConversation };
}
