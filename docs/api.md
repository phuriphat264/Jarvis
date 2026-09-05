# API Documentation

## Auth
- `POST /api/v1/auth/register`: Register new user
- `POST /api/v1/auth/login`: Authenticate and get JWT
- `GET /api/v1/auth/me`: Get current user info

## Conversations
- `POST /api/v1/conversations/`: Create conversation
- `GET /api/v1/conversations/`: List conversations
- `GET /api/v1/conversations/{id}`: Get conversation details
- `POST /api/v1/conversations/{id}/messages`: Send message (gets mock AI response)
- `GET /api/v1/conversations/{id}/messages`: List messages

## System
- `GET /health`: Basic health check
- `GET /api/v1/system/status`: Detailed subsystem status
