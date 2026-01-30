# Anonymous Web Messenger

A privacy-focused web-based messenger that enables real-time communication without requiring users to enter personal data.

## Features

- **Anonymous Sessions**: No phone number, email, or real name required
- **Real-time Messaging**: WebSocket-based instant messaging
- **Room Management**: Create and join chat rooms via room codes
- **Configurable Message Retention**: Auto-delete messages after configurable period
- **Moderation Tools**: Report messages, block sessions, room owner controls
- **Admin Panel**: Monitor usage, manage abuse controls, view security logs
- **Security**: TLS transport, rate limiting, input sanitization, audit logging

## Tech Stack

- **Backend**: Django 5.2 + Django Channels (WebSockets)
- **Frontend**: React.js with Vite
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Real-time**: Django Channels with ASGI

## Setup Instructions

### Backend Setup

1. **Create and activate virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run migrations**:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create superuser** (for admin panel):
```bash
python manage.py createsuperuser
```

5. **Run development server**:
```bash
python manage.py runserver
```

For WebSocket support, use an ASGI server:
```bash
pip install daphne
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Run development server**:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. **Create a Session**: Enter a nickname to create an anonymous session
2. **Create or Join Room**: Create a new room or join with a room code
3. **Start Chatting**: Send messages in real-time via WebSocket
4. **Share Room**: Copy the room code to share with others

## Admin Panel

Access the admin panel at `/admin/` to:
- View system statistics
- Manage rooms and messages
- Monitor audit logs
- Ban/unban sessions
- Configure moderation settings

## Message Cleanup

Run the cleanup command to delete messages older than their room's retention period:

```bash
python manage.py cleanup_messages
```

For production, set up a cron job or Celery task to run this daily.

## Production Deployment

1. **Set environment variables**:
   - `SECRET_KEY`: Django secret key
   - `DEBUG=False`
   - `ALLOWED_HOSTS`: Your domain
   - Database credentials

2. **Update settings.py**:
   - Enable `SECURE_SSL_REDIRECT`
   - Set `SESSION_COOKIE_SECURE = True`
   - Configure Redis for channel layers
   - Set up PostgreSQL database

3. **Build frontend**:
```bash
cd frontend
npm run build
```

4. **Collect static files**:
```bash
python manage.py collectstatic
```

5. **Run with ASGI server** (Daphne/Uvicorn):
```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

## Security Features

- TLS/HTTPS enforcement (production)
- CSRF protection
- Input validation and sanitization
- Rate limiting (10 messages/min, 3 rooms/hour, 5 sessions/hour)
- Secure session token generation
- SQL injection prevention (Django ORM)
- XSS prevention
- Audit logging for security events
- Security headers (HSTS, CSP, X-Frame-Options)

## API Endpoints

- `POST /api/session/create/` - Create anonymous session
- `GET /api/session/validate/` - Validate session token
- `POST /api/rooms/create/` - Create room
- `POST /api/rooms/join/` - Join room
- `GET /api/rooms/{code}/` - Get room details
- `GET /api/rooms/{code}/messages/` - Get message history
- `POST /api/messages/send/` - Send message
- `POST /api/messages/{id}/report/` - Report message
- `POST /api/moderation/block-session/` - Block session
- `GET /api/moderation/reports/` - Get reports

## WebSocket

Connect to: `ws://localhost:8000/ws/chat/{room_code}/?token={session_token}`

Message format:
```json
{
  "type": "chat_message",
  "content": "Hello world"
}
```

## License

This project is for educational purposes.
