from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
from typing import Optional, Dict

Base = declarative_base()

class TwitterUser(Base):
    __tablename__ = 'twitter_users'
    id = Column(Integer, primary_key=True)
    twitter_handle = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    tweets = relationship('Tweet', back_populates='author')
    sessions = relationship('TwitterSession', back_populates='user')

class Tweet(Base):
    __tablename__ = 'tweets'
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(50), unique=True, nullable=False)
    author_id = Column(Integer, ForeignKey('twitter_users.id'))
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP)
    tweet_metadata = Column("metadata", JSON)
    author = relationship('TwitterUser', back_populates='tweets')
    actions = relationship('TweetAction', back_populates='tweet')

class TwitterSession(Base):
    __tablename__ = 'twitter_sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('twitter_users.id'))
    session_timestamp = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    user = relationship('TwitterUser', back_populates='sessions')
    actions = relationship('TweetAction', back_populates='session')

class TweetAction(Base):
    __tablename__ = 'tweet_actions'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('twitter_sessions.id'))
    tweet_id = Column(Integer, ForeignKey('tweets.id'))
    action_type = Column(String(20), nullable=False)
    ai_reply = Column(Text)
    likes = Column(Integer)
    retweets = Column(Integer)
    replies = Column(Integer)
    action_timestamp = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    extra = Column(JSON)
    session = relationship('TwitterSession', back_populates='actions')
    tweet = relationship('Tweet', back_populates='actions')

class TwitterDBLogger:
    """
    Handles logging of session and operation data to PostgreSQL using SQLAlchemy ORM.
    """
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def upsert_user(self, twitter_handle: str, display_name: Optional[str] = None) -> int:
        session = self.Session()
        user = session.query(TwitterUser).filter_by(twitter_handle=twitter_handle).first()
        if not user:
            user = TwitterUser(twitter_handle=twitter_handle, display_name=display_name)
            session.add(user)
            session.commit()
        elif display_name and user.display_name != display_name:
            user.display_name = display_name
            session.commit()
        user_id = user.id
        session.close()
        return user_id

    def upsert_tweet(self, tweet_id: str, author_id: int, content: str, created_at: Optional[datetime] = None, metadata: Optional[Dict] = None) -> int:
        session = self.Session()
        tweet = session.query(Tweet).filter_by(tweet_id=tweet_id).first()
        if not tweet:
            tweet = Tweet(tweet_id=tweet_id, author_id=author_id, content=content, created_at=created_at, tweet_metadata=metadata)
            session.add(tweet)
            session.commit()
        else:
            tweet.content = content
            tweet.tweet_metadata = metadata
            session.commit()
        tweet_db_id = tweet.id
        session.close()
        return tweet_db_id

    def create_session(self, user_id: int, session_timestamp: datetime) -> int:
        session = self.Session()
        sess = TwitterSession(user_id=user_id, session_timestamp=session_timestamp)
        session.add(sess)
        session.commit()
        session_id = sess.id
        session.close()
        return session_id

    def log_action(
        self,
        session_id: int,
        tweet_db_id: int,
        action_type: str,
        ai_reply: Optional[str] = None,
        likes: Optional[int] = None,
        retweets: Optional[int] = None,
        replies: Optional[int] = None,
        extra: Optional[Dict] = None
    ) -> None:
        session = self.Session()
        action = TweetAction(
            session_id=session_id,
            tweet_id=tweet_db_id,
            action_type=action_type,
            ai_reply=ai_reply,
            likes=likes,
            retweets=retweets,
            replies=replies,
            extra=extra
        )
        session.add(action)
        session.commit()
        session.close()

    def close(self):
        self.engine.dispose() 