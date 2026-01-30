import axios from 'axios';
import { sessionService } from './session';

const API_BASE_URL = '/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add session token to requests
api.interceptors.request.use((config) => {
  const token = sessionService.getToken();
  if (token) {
    config.headers['X-Session-Token'] = token;
  }
  return config;
});

// API functions
export const apiService = {
  // Session management
  async createSession(nickname) {
    const response = await api.post('/session/create/', { nickname });
    if (response.data.session_token) {
      sessionService.setSession(response.data.session_token, response.data.nickname);
    }
    return response.data;
  },

  async validateSession() {
    const token = sessionService.getToken();
    if (!token) {
      throw new Error('No session token');
    }
    const response = await api.get('/session/validate/', { params: { token } });
    return response.data;
  },

  // Room management
  async createRoom(name, messageRetentionDays = 30, maxParticipants = null) {
    const response = await api.post('/rooms/create/', {
      name,
      message_retention_days: messageRetentionDays,
      max_participants: maxParticipants,
    });
    return response.data;
  },

  async joinRoom(roomCode) {
    const response = await api.post('/rooms/join/', { room_code: roomCode });
    return response.data;
  },

  async getRoom(roomCode) {
    const response = await api.get(`/rooms/${roomCode}/`);
    return response.data;
  },

  async getRoomMessages(roomCode, page = 1, pageSize = 50) {
    const response = await api.get(`/rooms/${roomCode}/messages/`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  // Messaging
  async sendMessage(roomCode, content) {
    const response = await api.post('/messages/send/', {
      room_code: roomCode,
      content,
    });
    return response.data;
  },

  async reportMessage(messageId, reason = '') {
    const response = await api.post(`/messages/${messageId}/report/`, { reason });
    return response.data;
  },

  // Moderation
  async blockSession(roomCode, targetSessionToken, reason = '') {
    const response = await api.post('/moderation/block-session/', {
      room_code: roomCode,
      target_session_token: targetSessionToken,
      reason,
    });
    return response.data;
  },

  async getReports(roomCode) {
    const response = await api.get('/moderation/reports/', {
      params: { room_code: roomCode },
    });
    return response.data;
  },
};

export default api;
