-- Create admin user for project spaces
INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'admin', 
    'admin@company.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3/4BjL0jSi',
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP
) ON CONFLICT (username) DO NOTHING;
