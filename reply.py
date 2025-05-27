# reply.py

import os, sqlite3, logging, tweepy, time
from dotenv import load_dotenv
from google import genai

# ─── Load environment variables ─────────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
TW_BEARER_TOKEN  = os.getenv("TWITTER_BEARER_TOKEN")
TW_API_KEY       = os.getenv("TWITTER_API_KEY")
TW_API_SECRET    = os.getenv("TWITTER_API_SECRET")
TW_ACCESS_TOKEN  = os.getenv("TWITTER_ACCESS_TOKEN")
TW_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# ─── Basic logging ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# ─── Database setup ───────────────────────────────────────────────────────────────
def setup_db():
    conn = sqlite3.connect('history.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tweets (
            id TEXT PRIMARY KEY
        )
    ''')
    conn.commit()
    return conn, cursor

# ─── GeminiClient (same as before) ────────────────────────────────────────────────
class GeminiClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"
    def generate(self, prompt: str) -> str:
        try:
            resp = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return resp.text.strip()
        except Exception as e:
            logging.error(f"Gemini generate error: {e}")
            return ""

def main():
    conn, cursor = setup_db()
    gemini = GeminiClient(GEMINI_API_KEY)

    client = tweepy.Client(
        bearer_token=TW_BEARER_TOKEN,
        consumer_key=TW_API_KEY,
        consumer_secret=TW_API_SECRET,
        access_token=TW_ACCESS_TOKEN,
        access_token_secret=TW_ACCESS_SECRET,
        wait_on_rate_limit=True
    )
    me = client.get_me()
    user_id = me.data['id'] if isinstance(me.data, dict) else me.data.id
    logging.info(f"reply.py running for user {user_id}")

    try:
        mentions_resp = client.get_users_mentions(
            user_id,
            max_results=5,
            expansions=['author_id'],
            user_fields=['username']
        )
        mentions = mentions_resp.data or []
        users_map = {}
        if mentions_resp.includes and 'users' in mentions_resp.includes:
            for u in mentions_resp.includes['users']:
                users_map[u['id']] = u['username']

        for m in reversed(mentions):
            mid = str(m['id']) if isinstance(m, dict) else str(m.id)
            # Check if we already replied
            if not cursor.execute('SELECT 1 FROM tweets WHERE id=?', (mid,)).fetchone():
                author_id = m['author_id'] if isinstance(m, dict) else m.author_id
                author_username = users_map.get(author_id)
                if author_username is None:
                    user_info = client.get_user(id=author_id, user_fields=['username'])
                    author_username = user_info.data['username'] if isinstance(user_info.data, dict) else user_info.data.username

                text_to_reply = m['text'] if isinstance(m, dict) else m.text
                generated = gemini.generate(text_to_reply)
                reply_text = f"@{author_username} {generated}"

                try:
                    client.create_tweet(text=reply_text, in_reply_to_tweet_id=mid)
                    cursor.execute('INSERT INTO tweets(id) VALUES(?)', (mid,))
                    conn.commit()
                    logging.info(f"Replied to mention {mid} (@{author_username})")
                    time.sleep(2)
                except Exception as e:
                    logging.error(f"Reply error to {mid}: {e}")
    except Exception as e:
        logging.error(f"Mention fetch error: {e}")

if __name__ == "__main__":
    main()
