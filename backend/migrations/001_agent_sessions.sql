-- Migration: Create agent_sessions table for LangGraph persistence
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS agent_sessions (
    id BIGSERIAL PRIMARY KEY,
    thread_id VARCHAR(255) UNIQUE NOT NULL,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    messages JSONB DEFAULT '[]',
    state JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_thread ON agent_sessions(thread_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user ON agent_sessions(user_id);

COMMENT ON TABLE agent_sessions IS 'Stores LangGraph agent conversation sessions for WhatsApp persistence';