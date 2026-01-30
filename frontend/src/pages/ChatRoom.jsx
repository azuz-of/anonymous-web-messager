import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { sessionService } from '../services/session';
import { WebSocketService } from '../services/websocket';
import MessageList from '../components/MessageList';
import MessageInput from '../components/MessageInput';
import RoomHeader from '../components/RoomHeader';
import './ChatRoom.css';

function ChatRoom() {
  const { roomCode } = useParams();
  const navigate = useNavigate();
  const [room, setRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [wsService, setWsService] = useState(null);
  const messagesEndRef = useRef(null);
  const [isOwner, setIsOwner] = useState(false);

  useEffect(() => {
    // Check session
    if (!sessionService.hasSession()) {
      navigate('/');
      return;
    }

    loadRoom();
    return () => {
      if (wsService) {
        wsService.disconnect();
      }
    };
  }, [roomCode]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadRoom = async () => {
    try {
      const roomData = await apiService.getRoom(roomCode);
      setRoom(roomData);
      
      // Check if current session is owner
      // owner_session in the response is the session token UUID
      const token = sessionService.getToken();
      setIsOwner(roomData.owner_session && roomData.owner_session.toString() === token);

      // Load message history
      const messagesData = await apiService.getRoomMessages(roomCode);
      setMessages(messagesData.results.reverse()); // Reverse to show oldest first

      // Connect WebSocket
      connectWebSocket(roomData);
      
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load room');
      setLoading(false);
    }
  };

  const connectWebSocket = (roomData) => {
    const token = sessionService.getToken();
    const ws = new WebSocketService(
      roomCode,
      token,
      handleNewMessage,
      handleWebSocketError,
      handleWebSocketClose
    );
    
    ws.connect();
    setWsService(ws);
  };

  const handleNewMessage = (messageData) => {
    setMessages((prev) => [...prev, messageData]);
  };

  const handleWebSocketError = (errorMessage) => {
    console.error('WebSocket error:', errorMessage);
    setError(errorMessage);
  };

  const handleWebSocketClose = () => {
    console.log('WebSocket closed, attempting to reconnect...');
  };

  const handleSendMessage = (content) => {
    if (wsService && wsService.sendMessage(content)) {
      // Message sent via WebSocket
      return true;
    } else {
      // Fallback to REST API
      apiService.sendMessage(roomCode, content)
        .then((message) => {
          handleNewMessage({
            id: message.id,
            session_nickname: message.session_nickname,
            content: message.content,
            timestamp: message.timestamp,
          });
        })
        .catch((err) => {
          setError(err.response?.data?.error || 'Failed to send message');
        });
      return false;
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleCopyRoomCode = () => {
    navigator.clipboard.writeText(roomCode);
    // You could show a toast notification here
  };

  if (loading) {
    return (
      <div className="chat-room loading">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  if (error && !room) {
    return (
      <div className="chat-room error">
        <div className="error-container">
          <p>{error}</p>
          <button onClick={() => navigate('/')} className="btn btn-primary">
            Go Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-room">
      <RoomHeader
        roomCode={roomCode}
        roomName={room?.name}
        isOwner={isOwner}
        onCopyCode={handleCopyRoomCode}
      />
      
      {error && <div className="error-banner">{error}</div>}
      
      <div className="chat-messages-container">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>
      
      <MessageInput onSendMessage={handleSendMessage} />
    </div>
  );
}

export default ChatRoom;
