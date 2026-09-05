# Database Schema (Phase 1)

## users
- id (PK)
- email
- hashed_password
- full_name
- created_at
- updated_at

## conversations
- id (PK)
- user_id (FK -> users)
- title
- created_at
- updated_at

## messages
- id (PK)
- conversation_id (FK -> conversations)
- role (user, assistant, system)
- content (text)
- created_at

## activity_logs
- id (PK)
- user_id (FK -> users)
- action
- details (json)
- created_at
