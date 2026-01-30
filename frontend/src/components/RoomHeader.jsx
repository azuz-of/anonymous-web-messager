import React from 'react';
import { useNavigate } from 'react-router-dom';
import './RoomHeader.css';

function RoomHeader({ roomCode, roomName, isOwner, onCopyCode }) {
  const navigate = useNavigate();

  return (
    <div className="room-header">
      <div className="room-header-content">
        <button onClick={() => navigate('/')} className="back-button">
          ← Back
        </button>
        <div className="room-info">
          <h2 className="room-code" onClick={onCopyCode} title="Click to copy">
            {roomCode}
          </h2>
          {roomName && <p className="room-name">{roomName}</p>}
          {isOwner && <span className="owner-badge">Owner</span>}
        </div>
        <button onClick={onCopyCode} className="copy-button" title="Copy room code">
          📋
        </button>
      </div>
    </div>
  );
}

export default RoomHeader;
