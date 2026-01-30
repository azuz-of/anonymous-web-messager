import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { sessionService } from '../services/session';
import './HomePage.css';

function HomePage() {
  const navigate = useNavigate();
  const [nickname, setNickname] = useState('');
  const [roomCode, setRoomCode] = useState('');
  const [mode, setMode] = useState('create'); // 'create' or 'join'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hasSession, setHasSession] = useState(false);

  useEffect(() => {
    // Check if user has existing session
    if (sessionService.hasSession()) {
      setHasSession(true);
      setNickname(sessionService.getNickname());
    }
  }, []);

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!nickname.trim()) {
      setError('Please enter a nickname');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await apiService.createSession(nickname.trim());
      setHasSession(true);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create session');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    if (!hasSession) {
      setError('Please create a session first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const room = await apiService.createRoom('', 30, null);
      navigate(`/room/${room.code}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create room');
      setLoading(false);
    }
  };

  const handleJoinRoom = async (e) => {
    e.preventDefault();
    if (!hasSession) {
      setError('Please create a session first');
      return;
    }

    if (!roomCode.trim()) {
      setError('Please enter a room code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const room = await apiService.joinRoom(roomCode.trim().toUpperCase());
      navigate(`/room/${room.code}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to join room');
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <div className="home-container">
        <h1 className="home-title">Anonymous Messenger</h1>
        <p className="home-subtitle">Private, secure, anonymous messaging</p>

        {!hasSession ? (
          <form onSubmit={handleCreateSession} className="home-form">
            <div className="form-group">
              <label htmlFor="nickname">Choose a nickname</label>
              <input
                id="nickname"
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="Enter your nickname"
                maxLength={30}
                required
                disabled={loading}
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? 'Creating...' : 'Start Chatting'}
            </button>
          </form>
        ) : (
          <div className="home-actions">
            <div className="mode-toggle">
              <button
                className={mode === 'create' ? 'active' : ''}
                onClick={() => setMode('create')}
              >
                Create Room
              </button>
              <button
                className={mode === 'join' ? 'active' : ''}
                onClick={() => setMode('join')}
              >
                Join Room
              </button>
            </div>

            {mode === 'create' ? (
              <form onSubmit={handleCreateRoom} className="home-form">
                <p className="info-text">Create a new chat room</p>
                {error && <div className="error-message">{error}</div>}
                <button type="submit" disabled={loading} className="btn btn-primary">
                  {loading ? 'Creating...' : 'Create Room'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleJoinRoom} className="home-form">
                <div className="form-group">
                  <label htmlFor="roomCode">Room Code</label>
                  <input
                    id="roomCode"
                    type="text"
                    value={roomCode}
                    onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                    placeholder="Enter room code"
                    maxLength={8}
                    required
                    disabled={loading}
                    style={{ textTransform: 'uppercase' }}
                  />
                </div>
                {error && <div className="error-message">{error}</div>}
                <button type="submit" disabled={loading} className="btn btn-primary">
                  {loading ? 'Joining...' : 'Join Room'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default HomePage;
