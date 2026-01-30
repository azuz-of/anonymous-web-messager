/**
 * Session management service
 * Handles session token storage and retrieval
 */

const SESSION_TOKEN_KEY = 'messenger_session_token';
const SESSION_NICKNAME_KEY = 'messenger_session_nickname';

export const sessionService = {
  getToken() {
    return localStorage.getItem(SESSION_TOKEN_KEY);
  },

  getNickname() {
    return localStorage.getItem(SESSION_NICKNAME_KEY);
  },

  setSession(token, nickname) {
    localStorage.setItem(SESSION_TOKEN_KEY, token);
    localStorage.setItem(SESSION_NICKNAME_KEY, nickname);
  },

  clearSession() {
    localStorage.removeItem(SESSION_TOKEN_KEY);
    localStorage.removeItem(SESSION_NICKNAME_KEY);
  },

  hasSession() {
    return !!this.getToken();
  },
};
