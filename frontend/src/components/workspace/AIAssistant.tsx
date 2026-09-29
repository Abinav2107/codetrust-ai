import { useEffect, useRef, useState, type ChangeEvent, type KeyboardEvent } from 'react';
import type { ChatMessage } from '../../types';
import { askAssistant } from '../../services/chatService';
import { Button } from '../ui/Button';
import { Icon } from '../ui/Icon';
import { copyText } from '../../utils/clipboard';

export function AIAssistant({ file, onOpenIssue }: { file: string; onOpenIssue: (id: string) => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([{ id: 'welcome', role: 'assistant', content: 'I can inspect the highlighted lines, explain the issue, or suggest a safer fix.' }]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);
  useEffect(() => { if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight; }, [messages, typing]);
  const send = async () => {
    const q = input.trim();
    if (!q || typing) return;
    const id = crypto.randomUUID();
    setMessages(m => [...m, { id, role: 'user', content: q }]);
    setInput(''); setTyping(true);
    try {
      const reply = await askAssistant(q, file);
      setMessages(m => [...m, { id: crypto.randomUUID(), role: 'assistant', content: reply }]);
    } catch {
      setMessages(m => [...m, { id: crypto.randomUUID(), role: 'assistant', content: 'I could not reach the local assistant right now. Try again in a moment.' }]);
    } finally { setTyping(false); }
  };
  return <div className="assistant-panel">
    <div className="chat-head"><span className="assistant-orb"><Icon name="sparkles" size={13}/></span><span>AI Assistant</span><span className="assistant-context">{file.split('/').pop()}</span></div>
    <div className="chat-body" ref={bodyRef}>{messages.map(message => <div className={`msg ${message.role}`} key={message.id}>{message.role === 'assistant' && <div className="who">Assistant</div>}<div>{message.content}</div>{message.role === 'assistant' && <button className="copy-reply" onClick={() => void copyText(message.content).then(() => undefined)}>Copy</button>}</div>)}{typing && <div className="typing"><span/><span/><span/></div>}</div>
    <div className="chat-suggestions"><button onClick={() => setInput('Why is this risky?')}>Why risky?</button><button onClick={() => setInput('Suggest a fix')}>Suggest a fix</button><button onClick={() => setInput('Explain this file')}>Explain file</button></div>
    <div className="chat-input"><input value={input} onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)} onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send(); } }} placeholder="Ask about this code…"/><Button size="sm" icon="arrow-right" onClick={() => void send()} disabled={typing || !input.trim()}>Send</Button></div>
    <button className="ghost-link" onClick={() => onOpenIssue('i1')}><Icon name="bug" size={13}/> View an issue in this file</button>
  </div>;
}
