import os
from openai import OpenAI

def generate_ai_reply(tweet_content: str, author: str) -> str:
    """
    Generate a context-aware, human-like reply to the given tweet content using OpenAI API.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return f"@{author} Interesting point! AI error: OpenAI API key not set"
    
    client = OpenAI(api_key=api_key)
    prompt = (
        f"You are a friendly, witty Twitter user. "
        f"Reply to the following tweet in a human-like, context-aware, and conversational way. "
        f"Keep it short and engaging.\n"
        f"Tweet from @{author}: '{tweet_content}'"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful, witty Twitter user."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=60,
            temperature=0.8,
        )
        reply = response.choices[0].message.content.strip()
        return reply
    except Exception as e:
        return f"@{author} Interesting thought! (AI error: {e})" 