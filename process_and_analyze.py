import pandas as pd
import json
import re
import emoji
import time
import sys
from deep_translator import GoogleTranslator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langdetect import detect, LangDetectException

KEYWORD_SCORES = {
    'genocide': 3, 'fascist': 3, 'nazi': 3, 'apartheid': 3,
    'terrorism': 2, 'terrorist': 2, 'propaganda': 2, 'warmonger': 2,
    'occupation': 2, 'siege': 2, 'human rights violation': 2,
    'boycott': 1, 'shame': 1, 'fail': 1, 'dictator': 1, 'oppression': 1,
}

def clean_tweet_content(text):
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+', '', text)
    text = re.sub(r'#', ' ', text)
    text = emoji.demojize(text, delimiters=(" ", " "))
    text = text.replace('\n', ' ').strip()
    return text

def get_language_and_translate(text):
    if not text or not isinstance(text, str) or text.isspace():
        return 'unknown', text
    try:
        lang = detect(text)
        if lang != 'en':
            for attempt in range(3):
                try:
                    return lang, GoogleTranslator(source='auto', target='en').translate(text)
                except Exception as e:
                    print(f"[WARN]: Translation attempt {attempt+1} failed. Retrying... Error: {e}")
                    time.sleep(3)
            return lang, text
        else:
            return 'en', text
    except LangDetectException:
        return 'unknown', text
    except Exception:
        return 'error', text

def parse_author_info(author_text):
    parts = author_text.split('\n')
    return (parts[1], parts[0]) if len(parts) >= 2 else ("unknown", author_text)

def calculate_keyword_score(text):
    return sum(value for keyword, value in KEYWORD_SCORES.items() if keyword in text.lower())

def run_pipeline(run_id, final_report_path, final_user_report_path):
    print(f"[INFO] Starting pipeline for run_id: {run_id}")
    
    input_json = f"scraped_data_{run_id}.json"
    temp_preprocessed_csv = f"preprocessed_twitter_data_{run_id}.csv"

    try:
        with open(input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR]: Input file '{input_json}' not found. Aborting.")
        sys.exit(1)

    df = pd.DataFrame(data)
    if df.empty:
        print("[WARN]: Input JSON is empty.")
        return

    print(f"[INFO] Preprocessing {len(df)} tweets...")
    df['cleaned_content'] = df['content'].apply(clean_tweet_content)
    
    translations = [get_language_and_translate(text) for text in df['cleaned_content']]
    df['language'], df['cleaned_content'] = zip(*translations)
    
    author_info = [parse_author_info(author) for author in df['author']]
    df['username'], df['display_name'] = zip(*author_info)
    
    analyzer = SentimentIntensityAnalyzer()
    df['sentiment_score'] = df['cleaned_content'].apply(lambda x: analyzer.polarity_scores(x)['compound'])
    
    df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    df['hashtag_count'] = df['hashtags'].apply(lambda x: len(x.split(',')) if x else 0)
    
    df['comments'] = pd.to_numeric(df['comments'], errors='coerce').fillna(0).astype(int)
    df['reposts'] = pd.to_numeric(df['reposts'], errors='coerce').fillna(0).astype(int)
    
    df = df.rename(columns={'content': 'original_content'})
    
    final_df = df[['username', 'display_name', 'cleaned_content', 'sentiment_score', 'comments', 'reposts']]
    final_df.to_csv(temp_preprocessed_csv, index=False, encoding='utf-8')
    print(f"[INFO] Preprocessing complete. Saved to {temp_preprocessed_csv}")

    print("[INFO] Starting campaign analysis...")
    df_processed = pd.read_csv(temp_preprocessed_csv)
    
    df_processed['keyword_score'] = df_processed['cleaned_content'].apply(calculate_keyword_score)
    
    df_processed['repost_to_comment_ratio'] = df_processed['reposts'] / (df_processed['comments'] + 1)
    df_processed['is_suspicious_engagement'] = (df_processed['repost_to_comment_ratio'] > 20) & (df_processed['reposts'] > 10)
    
    user_post_counts = df_processed[df_processed['sentiment_score'] < -0.1]['username'].value_counts().to_dict()
    df_processed['user_negative_post_count'] = df_processed['username'].map(user_post_counts).fillna(0)
    
    print("[INFO] Calculating final suspicion scores...")
    df_processed['suspicion_score'] = (
        df_processed['keyword_score'] * 1.5 +
        abs(df_processed['sentiment_score']) * (df_processed['sentiment_score'] < 0) +
        df_processed['is_suspicious_engagement'] * 3 +
        (df_processed['user_negative_post_count'] > 5) * 2
    )
    
    df_sorted = df_processed.sort_values(by='suspicion_score', ascending=False)
    df_sorted.to_csv(final_report_path, index=False, encoding='utf-8')
    print(f"[INFO] Main analysis report saved to {final_report_path}")

    user_scores = df_sorted.groupby('username')['suspicion_score'].sum().reset_index()
    user_scores.columns = ['username', 'total_suspicion_score']
    user_scores_sorted = user_scores.sort_values(by='total_suspicion_score', ascending=False)
    
    user_scores_sorted.head(20).to_csv(final_user_report_path, index=False, encoding='utf-8')
    print(f"[INFO] Suspicious users report saved to {final_user_report_path}")
    print(f"[INFO] Pipeline for run_id: {run_id} complete.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python process_and_analyze.py <run_id> <final_report_path> <final_user_report_path>")
        sys.exit(1)
    else:
        run_pipeline(sys.argv[1], sys.argv[2], sys.argv[3])