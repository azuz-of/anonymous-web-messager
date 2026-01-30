import React from 'react';
import { sessionService } from '../services/session';
import './MessageItem.css';

function MessageItem({ message }) {
  const isOwnMessage = sessionService.getNickname() === message.session_nickname;
  const timestamp = new Date(message.timestamp);
  const timeString = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className={`message-item ${isOwnMessage ? 'own' : ''}`}>
      <div className="message-content">
        {!isOwnMessage && (
          <div className="message-sender">{message.session_nickname}</div>
        )}
        <div className="message-text">{message.content}</div>
        <div className="message-time">{timeString}</div>
      </div>
    </div>
  );
}

export default MessageItem;
