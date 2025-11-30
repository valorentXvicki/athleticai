
import React, { useState } from 'react';

const messagesInitial = [
    { sender: 'bot', text: 'Welcome! I am your AI Coach. How can I help you today?' }
];

function Chatbot() {
    const [messages, setMessages] = useState(messagesInitial);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSend = async () => {
        if (!input.trim()) return;
        const userMsg = { sender: 'user', text: input };
        setMessages(msgs => [...msgs, userMsg]);
        setInput('');
        setLoading(true);
        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: input, user_id: 'webuser' })
            });
            const data = await res.json();
            setMessages(msgs => [...msgs, { sender: 'bot', text: data.response || 'Sorry, I could not understand that.' }]);
        } catch (err) {
            setMessages(msgs => [...msgs, { sender: 'bot', text: 'Sorry, there was a problem connecting to the AI.' }]);
        }
        setLoading(false);
    };

    return (
        <div style={{ maxWidth: 400, margin: 'auto', fontFamily: 'sans-serif' }}>
            <h2>Sports Chatbot</h2>
            <div style={{ border: '1px solid #ccc', padding: 10, height: 300, overflowY: 'auto', marginBottom: 10 }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '5px 0' }}>
                        <span style={{
                            display: 'inline-block',
                            background: msg.sender === 'user' ? '#007bff' : '#eee',
                            color: msg.sender === 'user' ? '#fff' : '#333',
                            borderRadius: 10,
                            padding: '6px 12px',
                        }}>
                            {msg.text}
                        </span>
                    </div>
                ))}
                {loading && (
                    <div style={{ textAlign: 'left', margin: '5px 0' }}>
                        <span style={{
                            display: 'inline-block',
                            background: '#eee',
                            color: '#333',
                            borderRadius: 10,
                            padding: '6px 12px',
                            opacity: 0.7
                        }}>
                            Thinking...
                        </span>
                    </div>
                )}
            </div>
            <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                style={{ width: '80%', padding: 8 }}
                placeholder="Type your message..."
                disabled={loading}
            />
            <button onClick={handleSend} style={{ width: '18%', marginLeft: '2%', padding: 8 }} disabled={loading}>Send</button>
        </div>
    );
}

export default Chatbot;
