-- Users table
CREATE TABLE twitter_users (
    id SERIAL PRIMARY KEY,
    twitter_handle VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tweets table
CREATE TABLE tweets (
    id SERIAL PRIMARY KEY,
    tweet_id VARCHAR(50) UNIQUE NOT NULL,
    author_id INTEGER REFERENCES twitter_users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP,
    metadata JSONB,
    UNIQUE(tweet_id)
);

-- Sessions table (each bot run)
CREATE TABLE twitter_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES twitter_users(id),
    session_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Actions table (repost, reply, etc.)
CREATE TABLE tweet_actions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES twitter_sessions(id),
    tweet_id INTEGER REFERENCES tweets(id),
    action_type VARCHAR(20) NOT NULL, -- e.g., 'repost', 'reply'
    ai_reply TEXT,
    likes INTEGER,
    retweets INTEGER,
    replies INTEGER,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra JSONB
);

-- Indexes for performance
CREATE INDEX idx_tweets_author_id ON tweets(author_id);
CREATE INDEX idx_actions_session_id ON tweet_actions(session_id); 