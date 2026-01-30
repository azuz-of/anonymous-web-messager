import React from 'react';
import MessageItem from './MessageItem';
import './MessageList.css';

function MessageList({ messages }) {
  if (messages.length === 0) {
    return (
      <div className="message-list empty">
        <p>No messages yet. Start the conversation!</p>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
    </div>
  );
}

export default MessageList;
