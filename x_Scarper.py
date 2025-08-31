import sys
import time
import json
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
TWITTER_VERIFICATION_EMAIL = os.getenv("TWITTER_VERIFICATION_EMAIL")

SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
CHROME_PROFILE_PATH = os.path.join(SCRIPTS_DIR, "scraper_profile")

TWEETS_TO_SCRAPE_PER_QUERY = 25
OUTPUT_FILENAME = "scraped_data.json"

class TwitterScraper:
    def __init__(self, username, password, verification_email, profile_path):
      self.username = username
      self.password = password
      self.verification_email = verification_email
      
      service = Service(ChromeDriverManager().install())
      options = webdriver.ChromeOptions()
      
      options.add_argument(f"user-data-dir={profile_path}")
      user_agents = [
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
      ]
      options.add_argument(f"user-agent={random.choice(user_agents)}")
      options.add_argument("--disable-blink-features=AutomationControlled")
      options.add_experimental_option("excludeSwitches", ["enable-automation"])
      options.add_experimental_option('useAutomationExtension', False)
      
      options.add_argument("--no-sandbox")
      options.add_argument("--disable-dev-shm-usage")
      options.add_argument("--disable-gpu")
      options.add_argument("--headless")
      options.add_argument("--window-size=1920,1080")
      
      self.driver = webdriver.Chrome(service=service, options=options)
      self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
      self.wait = WebDriverWait(self.driver, 20) 

    def handle_verification(self):
        try:
            verification_input = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]'))
            )
            print("[x_Scarper.py INFO]: Unusual activity detected. Entering verification email.")
            verification_input.send_keys(self.verification_email)
            verification_input.send_keys(Keys.ENTER)
            time.sleep(random.uniform(3, 5))
            return True
        except Exception:
            return False

    def login(self):
      self.driver.get("https://twitter.com/home")
      time.sleep(random.uniform(2, 4))
      try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="AppTabBar_Home_Link"]')))
            print("[x_Scarper.py INFO]: Already logged in via saved profile.")
            return True
      except Exception:
            print("[x_Scarper.py INFO]: Not logged in via profile. Attempting programmatic login.")

      try:
          self.driver.get("https://twitter.com/login")
          time.sleep(random.uniform(3, 5))
          
          username_field = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
          username_field.send_keys(self.username)
          username_field.send_keys(Keys.ENTER)
          time.sleep(random.uniform(2, 4))

          self.handle_verification()

          password_field = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
          password_field.send_keys(self.password)
          password_field.send_keys(Keys.ENTER)
          
          self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="AppTabBar_Home_Link"]')))
          print("[x_Scarper.py INFO]: Programmatic login successful!")
          return True
      except Exception as e:
          print(f"[x_Scarper.py ERROR]: Login failed: {e}")
          self.driver.save_screenshot('login_error.png')
          return False

    def search(self, query):
        print(f"[x_Scarper.py INFO]: Searching for: {query}")
        search_query = query.replace('#', '%23')
        search_url = f"https://twitter.com/search?q={search_query}&src=typed_query&f=live"
        self.driver.get(search_url)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]')))
        time.sleep(random.uniform(3, 5))

    def extract_tweet_data(self, tweet_element):
      try:
          author = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]').text
          content = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]').text
          hashtags = [tag.text for tag in tweet_element.find_elements(By.CSS_SELECTOR, 'a[href*="/hashtag/"]') if tag.text.startswith('#')]
          
          try:
              comments = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="reply"] span span span').text
          except Exception:
              comments = "0"
          try:
              reposts = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="retweet"] span span span').text
          except Exception:
              reposts = "0"

          return { "author": author, "content": content, "hashtags": hashtags, "comments": comments, "reposts": reposts }
      except Exception:
          return None

    def scrape_tweets(self, num_tweets, query):
      print(f"[x_Scarper.py INFO]: Scraping {num_tweets} tweets for '{query}'...")
      scraped_data = []
      unique_tweets = set()
      last_height = self.driver.execute_script("return document.body.scrollHeight")

      while len(scraped_data) < num_tweets:
          tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
          for tweet in tweet_elements:
              if len(scraped_data) >= num_tweets: break
              tweet_data = self.extract_tweet_data(tweet)
              if tweet_data and tweet_data['content'] not in unique_tweets:
                  unique_tweets.add(tweet_data['content'])
                  tweet_data["search_query"] = query
                  scraped_data.append(tweet_data)
          
          self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
          time.sleep(random.uniform(3, 5))
          
          new_height = self.driver.execute_script("return document.body.scrollHeight")
          if new_height == last_height:
              print("[x_Scarper.py INFO]: Reached end of page.")
              break
          last_height = new_height
      return scraped_data

    def save_to_json(self, data, filename):
        print(f"[x_Scarper.py INFO]: Saving {len(data)} tweets to {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[x_Scarper.py INFO]: Data successfully saved.")

    def close(self):
      if self.driver:
          self.driver.quit()
          print("[x_Scarper.py INFO]: Browser closed.")

if __name__ == "__main__":
    if not all([TWITTER_USERNAME, TWITTER_PASSWORD, TWITTER_VERIFICATION_EMAIL]):
        print("[x_Scarper.py ERROR]: Missing credentials in .env file. Please set TWITTER_USERNAME, TWITTER_PASSWORD, and TWITTER_VERIFICATION_EMAIL.")
        sys.exit(1)

    if len(sys.argv) > 1:
        SEARCH_QUERIES = sys.argv[1:]
    else:
        print("[x_Scarper.py ERROR]: No hashtags provided.")
        sys.exit(1)
    
    scraper = TwitterScraper(
        username=TWITTER_USERNAME,
        password=TWITTER_PASSWORD,
        verification_email=TWITTER_VERIFICATION_EMAIL,
        profile_path=CHROME_PROFILE_PATH
    )
    all_scraped_data = []
    
    try:
        if not scraper.login():
            print("[x_Scarper.py ERROR]: Exiting due to login failure.")
            sys.exit(1)

        for i, query in enumerate(SEARCH_QUERIES):
            print(f"\n--- Processing query {i+1}/{len(SEARCH_QUERIES)}: '{query}' ---")
            scraper.search(query)
            tweet_data = scraper.scrape_tweets(TWEETS_TO_SCRAPE_PER_QUERY, query)
            all_scraped_data.extend(tweet_data)
            if i < len(SEARCH_QUERIES) - 1:
                time.sleep(random.uniform(5, 10))
            
        scraper.save_to_json(all_scraped_data, OUTPUT_FILENAME)
    except Exception as e:
        print(f"[x_Scarper.py ERROR]: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()