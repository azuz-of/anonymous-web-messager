import React, { useState } from 'react';
import './MessageInput.css';

function MessageInput({ onSendMessage }) {
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
      setIsTyping(false);
    }
  };

  const handleChange = (e) => {
    setMessage(e.target.value);
    // You could implement typing indicators here
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="message-input-container">
      <form onSubmit={handleSubmit} className="message-input-form">
        <input
          type="text"
          value={message}
          onChange={handleChange}
          onKeyPress={handleKeyPress}
          placeholder="Type a message..."
          maxLength={1000}
          className="message-input"
        />
        <button type="submit" disabled={!message.trim()} className="send-button">
          Send
        </button>
      </form>
    </div>
  );
}

export default MessageInput;
