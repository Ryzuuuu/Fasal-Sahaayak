import { useEffect, useRef, useState } from 'react';
import { sendChat } from '../api';

// Matches the API's limit. Odd, so an alternating history ending with the user also starts with one.
const MAX_MESSAGES_SENT = 11;
const MAX_MESSAGE_CHARS = 1000;

export function ChatPanel({ t, language, farm, aiEnabled }) {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const [lastMode, setLastMode] = useState(null);
  const logRef = useRef(null);

  useEffect(() => {
    const log = logRef.current;
    if (log) log.scrollTop = log.scrollHeight;
  }, [messages, isSending]);

  const send = async (text) => {
    const content = text.trim();
    if (!content || isSending) return;

    const next = [...messages, { role: 'user', content }];
    setMessages(next);
    setDraft('');
    setError(null);
    setIsSending(true);
    try {
      const { reply, mode } = await sendChat(next.slice(-MAX_MESSAGES_SENT), language, farm);
      setLastMode(mode);
      setMessages((current) => [...current, { role: 'assistant', content: reply }]);
    } catch (caught) {
      setError(caught.kind === 'rate_limited' ? t.errorRateLimited : t.chatError);
      // Remove the unanswered message so the history stays valid, and let the user retry.
      setMessages(messages);
      setDraft(content);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <aside className="flex h-[32rem] flex-col rounded-2xl bg-white shadow-sm ring-1 ring-stone-200 lg:sticky lg:top-4 lg:h-[calc(100vh-2rem)]">
      <div className="border-b border-stone-200 p-4">
        <h2 className="text-lg font-bold text-stone-900">{t.chatTitle}</h2>
        <p className="text-xs text-stone-500">{(lastMode ? lastMode === 'llm' : aiEnabled) ? t.chatAi : t.chatOffline}</p>
      </div>

      <div ref={logRef} className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-stone-600">{t.chatWelcome}</p>
            {t.chatPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => send(prompt)}
                className="block w-full rounded-lg bg-emerald-50 px-3 py-2 text-left text-sm text-emerald-900 transition hover:bg-emerald-100 focus:outline-none focus:ring-2 focus:ring-emerald-600"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}
        {messages.map((message, index) => {
          const isUser = message.role === 'user';
          return (
            <div key={index} className={isUser ? 'text-right' : 'text-left'}>
              <span className="sr-only">{isUser ? t.chatYou : t.chatBot}: </span>
              <p
                className={`inline-block max-w-[90%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-left text-sm ${
                  isUser ? 'bg-emerald-700 text-white' : 'bg-stone-100 text-stone-900'
                }`}
              >
                {message.content}
              </p>
            </div>
          );
        })}
        {isSending && <p className="text-sm text-stone-500">{t.chatThinking}</p>}
        {error && (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        )}
      </div>

      <form
        className="flex gap-2 border-t border-stone-200 p-3"
        onSubmit={(event) => {
          event.preventDefault();
          send(draft);
        }}
      >
        <input
          type="text"
          value={draft}
          maxLength={MAX_MESSAGE_CHARS}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={t.chatPlaceholder}
          aria-label={t.chatPlaceholder}
          className="min-w-0 flex-1 rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
        />
        <button
          type="submit"
          disabled={isSending || !draft.trim()}
          className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {t.chatSend}
        </button>
      </form>
    </aside>
  );
}
