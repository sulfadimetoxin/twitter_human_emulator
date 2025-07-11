# Twitter Human Emulator

## Overview
A Python app that emulates a human interacting with Twitter: scrapes feed, analyzes tweets, reposts, and replies using AI.

## Setup (LOCAL)
1. Clone the repo
2. Install dependencies:
   ```bash
   poetry install
   poetry run playwright install
   ```
3. Set environment variables:
   - `TWITTER_USERNAME`
   - `TWITTER_PASSWORD`
   - `DATABASE_URL` (e.g., `postgresql://user:pass@host:port/dbname`)
   - `OPENAI_API_KEY`
4. Running the Script
   ```bash
   poetry run python main.py
   ```

## Setup (DOCKER)
1. Clone the repo
2. Set environment variables:
   - `TWITTER_USERNAME`
   - `TWITTER_PASSWORD`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_DB`
   - `DATABASE_URL` (e.g., `postgresql+psycopg2://user:pass@db:port/dbname`)
   - `OPENAI_API_KEY`
3. Running the Script
   ```bash
   docker-compose up -d
   ```

## Example Output
- Reposted tweet: "https://x.com/PopBase/status/1943359510329893163"
- AI reply: "https://x.com/JASONDOWOFF/status/1943614245100237014"

## SQL Schema
See `schema.sql` for the database structure. 