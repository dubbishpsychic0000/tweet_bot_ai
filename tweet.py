import os
import logging
import tweepy
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Configure Gemini (Google Generative AI)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

def generate_tweet():
    prompt = "What is a short, original, clever tweet I could post right now?"
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        logging.info("Generated tweet: %s", text)
        return text
    except Exception as e:
        logging.error(f"Error generating tweet: {e}")
        return None

def post_to_twitter(text):
    try:
        client = tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
        )
        response = client.create_tweet(text=text)
        logging.info(f"Tweet posted: {response}")
        print(f"Tweet posted successfully: {text}")
    except Exception as e:
        logging.error(f"Error posting tweet: {e}")
        print(f"Error posting tweet: {e}")

def main():
    print("Starting tweet bot...")
    tweet = generate_tweet()
    if tweet:
        post_to_twitter(tweet)
    else:
        print("Tweet generation failed. Exiting.")

if __name__ == "__main__":
    main()
