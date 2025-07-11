from datetime import datetime, timezone

def select_most_viral(tweets):
    """
    Select the most viral tweet using a weighted, time-normalized score:
    score = (retweets * 2.5 + likes + replies * 0.5) / age_in_minutes
    Falls back gracefully if created_at is missing or malformed.
    """
    def score(t):
        likes = t.get('likes', 0)
        retweets = t.get('retweets', 0)
        replies = t.get('replies', 0)
        created_at = t.get('created_at')
        age_minutes = 1
        if created_at:
            dt = None
            if isinstance(created_at, datetime):
                dt = created_at
            elif isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at)
                except Exception:
                    dt = None
            if dt:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                age_minutes = (now - dt).total_seconds() / 60
                age_minutes = max(age_minutes, 1)
        # Weighted score
        return (retweets * 2.5 + likes + replies * 0.5) / age_minutes

    return max(tweets, key=score) if tweets else None 