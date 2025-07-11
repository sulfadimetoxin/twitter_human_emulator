import os
import sys
import asyncio
from dotenv import load_dotenv
from twitter_bot.playwright_client import PlaywrightTwitterClient
from twitter_bot.tweet_analyzer import select_most_viral
from twitter_bot.ai_reply import generate_ai_reply
from twitter_bot.db import TwitterDBLogger
from datetime import datetime, timezone

# Load environment variables from .env file
load_dotenv()

"""
Main script to orchestrate Twitter automation, AI reply, and logging (async version).
"""

async def main():
    # Load credentials and DB URL from environment
    username = os.getenv('TWITTER_USERNAME')
    password = os.getenv('TWITTER_PASSWORD')
    db_url = os.getenv('DATABASE_URL')
    proxies = os.getenv('PROXIES')  # comma-separated list, optional
    proxy_list = [p.strip() for p in proxies.split(',')] if proxies else []

    # Check for missing environment variables
    if not username or not password or not db_url:
        print("Error: Please set TWITTER_USERNAME, TWITTER_PASSWORD, and DATABASE_URL environment variables.")
        sys.exit(1)

    db_logger = TwitterDBLogger(db_url)

    async with PlaywrightTwitterClient(username, password, proxies=proxy_list) as twitter:
        # Login and scrape feed
        await twitter.login()
        print("Logged in")
        print("Scraping feed....")
        tweets = await twitter.scrape_feed(count=20)

        # Analyze and select most viral tweet
        best_tweet = select_most_viral(tweets)
        print(f"Selected most viral tweet: {best_tweet}")
        if not best_tweet:
            print('No tweets found.')
            return

        # Generate AI reply
        ai_reply = generate_ai_reply(best_tweet['content'], best_tweet['author'])

        if "AI error" in ai_reply:      
            print(f"AI error: {ai_reply}")
            return

        # Repost and reply
        await twitter.repost_tweet(best_tweet['url'])
        print("Reposted")
        await twitter.reply_to_tweet(best_tweet['url'], ai_reply)
        print(f"Replied: {ai_reply}")

        # --- DB logic using SQLAlchemy ORM ---
        # 1. Upsert user
        user_id = db_logger.upsert_user(twitter_handle=best_tweet['author'])
        # 2. Upsert tweet
        tweet_db_id = db_logger.upsert_tweet(
            tweet_id=best_tweet.get('tweet_id', best_tweet['url']),  # fallback to URL if no tweet_id
            author_id=user_id,
            content=best_tweet['content'],
            created_at=best_tweet.get('created_at'),
            metadata={
                'url': best_tweet['url'],
                'likes': best_tweet['likes'],
                'retweets': best_tweet['retweets'],
                'replies': best_tweet['replies']
            }
        )
        # 3. Create session
        session_id = db_logger.create_session(user_id=user_id, session_timestamp=datetime.now(timezone.utc))
        # 4. Log repost action
        db_logger.log_action(
            session_id=session_id,
            tweet_db_id=tweet_db_id,
            action_type='repost',
            likes=best_tweet['likes'],
            retweets=best_tweet['retweets'],
            replies=best_tweet['replies'],
            extra={'url': best_tweet['url']}
        )
        # 5. Log reply action
        db_logger.log_action(
            session_id=session_id,
            tweet_db_id=tweet_db_id,
            action_type='reply',
            ai_reply=ai_reply,
            likes=best_tweet['likes'],
            retweets=best_tweet['retweets'],
            replies=best_tweet['replies'],
            extra={'url': best_tweet['url']}
        )
        print("Logged to DB")
    db_logger.close()

if __name__ == '__main__':
    asyncio.run(main()) 