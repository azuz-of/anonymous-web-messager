/**
 * WebSocket service for real-time messaging
 */

export class WebSocketService {
  constructor(roomCode, sessionToken, onMessage, onError, onClose) {
    this.roomCode = roomCode;
    this.sessionToken = sessionToken;
    this.onMessage = onMessage;
    this.onError = onError;
    this.onClose = onClose;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.isManualClose = false;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.roomCode}/?token=${this.sessionToken}`;
    
    try {
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'chat_message' && this.onMessage) {
            this.onMessage(data.data);
          } else if (data.type === 'typing' && this.onTyping) {
            this.onTyping(data);
          } else if (data.type === 'error') {
            if (this.onError) {
              this.onError(data.message);
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (this.onError) {
          this.onError('WebSocket connection error');
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        if (this.onClose) {
          this.onClose();
        }
        
        // Auto-reconnect if not manually closed
        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
          setTimeout(() => this.connect(), delay);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      if (this.onError) {
        this.onError('Failed to create WebSocket connection');
      }
    }
  }

  sendMessage(content) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'chat_message',
        content: content,
      }));
      return true;
    }
    return false;
  }

  sendTyping(isTyping) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'typing',
        is_typing: isTyping,
      }));
    }
  }

  disconnect() {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}
