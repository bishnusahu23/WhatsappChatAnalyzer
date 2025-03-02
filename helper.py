import pandas as pd
import re
from wordcloud import WordCloud
import emoji
from collections import Counter
import string


# ==========================
# 📌 Preprocessing Chat Data
# ==========================

def preprocess_chat(chat):
    """Parses the WhatsApp chat data and extracts timestamps, users, and messages."""
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}'
    timestamps = re.findall(pattern, chat)
    timestamps = [x.replace(" - ", "") for x in timestamps]
    messages = re.split(pattern, chat)[1:]
    messages = [x.replace(" - ", "") for x in messages]

    df = pd.DataFrame({'timestamp': timestamps, 'text': messages})
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m/%d/%y, %H:%M')

    users, message_content = [], []
    for msg in df['text']:
        match = re.match(r'([\w\W]+?):\s', msg)
        if match:
            users.append(match.group(1))
            message_content.append(msg[len(match.group(0)):])
        else:
            users.append('group_notification')
            message_content.append(msg)

    df['user'] = users
    df['message'] = message_content
    df.drop(columns=['text'], inplace=True)

    df['year'] = df['timestamp'].dt.year
    df['month'] = df['timestamp'].dt.strftime('%b')
    df['day'] = df['timestamp'].dt.day
    df['hour'] = df['timestamp'].dt.hour
    df['weekday'] = df['timestamp'].dt.day_name()
    df['date'] = df['timestamp'].dt.date

    return df


# =============================
# 📌 Chat Statistics & Activity
# =============================

def chat_statistics(user, df):
    """Computes total messages, word count, media count, and links shared."""
    if user != 'Overall':
        df = df[df['user'] == user]

    num_messages = df.shape[0]
    media_count = df[df['message'] == '<Media omitted>\n'].shape[0]
    word_count = df['message'].astype(str).str.split().str.len().sum()
    link_count = df['message'].str.contains("http").sum()

    return num_messages, word_count, media_count, link_count


def daily_message_count(user, df):
    """Counts messages sent per day."""
    if user != 'Overall':
        df = df[df['user'] == user]
    return df.groupby(df['date'])['message'].count().reset_index()


def weekly_activity(user, df):
    """Generates a heatmap of messages sent based on weekday and hour."""
    if user != 'Overall':
        df = df[df['user'] == user]
    heatmap_data = df.groupby(['weekday', 'hour'])['message'].count().unstack().fillna(0)
    return heatmap_data


def hourly_message_distribution(user, df):
    """Analyzes message distribution by hour."""
    if user != 'Overall':
        df = df[df['user'] == user]
    return df.groupby('hour')['message'].count()


# ================================
# 📌 Text Cleaning & Word Analysis
# ================================

def clean_messages(df):
    """Removes URLs, punctuation, stopwords, and unwanted messages."""
    with open(r"stopwords_hindi-english-telugu.txt", 'r') as file:
        stopwords = file.read().splitlines()

    temp_df = df[(df['user'] != 'group_notification') &
                 (df['message'] != '<Media omitted>\n') &
                 (df['message'] != 'This message was deleted\n') &
                 (~df['message'].str.strip().isin(['null', 'null\n', '']))]

    def clean_text(text):
        text = re.sub(r'http[s]?://\S+', '', text)  # Remove URLs
        text = re.sub(r'[@]?\d{10,}', '', text)  # Remove numbers like @1234567890
        text = re.sub(r'<.*?>', '', text)  # Remove HTML tags

        words = text.split()
        words = [word for word in words if word not in string.punctuation and word.lower() not in stopwords]

        return " ".join(words).strip()

    temp_df['message'] = temp_df['message'].apply(clean_text)

    return [word for message in temp_df['message'] for word in message.lower().split() if word not in stopwords]


def common_words(user, df):
    """Finds the most commonly used words excluding emojis."""
    if user != 'Overall':
        df = df[df['user'] == user]

    words = clean_messages(df)
    words = [word for word in words if word not in emoji.EMOJI_DATA]

    return pd.DataFrame(Counter(words).most_common(20))


def generate_wordcloud(user, df):
    """Creates a word cloud from frequently used words."""
    if user != 'Overall':
        df = df[df['user'] == user]

    words = clean_messages(df)
    wc = WordCloud(width=400, height=200, min_font_size=7, background_color='white', max_words=150).generate(
        " ".join(words))
    return wc


# ===================
# 📌 Emoji Analysis
# ===================

def emoji_usage(user, df):
    """Finds the most frequently used emojis."""
    if user != 'Overall':
        df = df[df['user'] == user]

    emojis = [c for message in df['message'] for c in message if c in emoji.EMOJI_DATA]
    return pd.DataFrame(Counter(emojis).most_common(10))


# ================================
# 📌 Response Time Analysis
# ================================

def compute_response_time(df):
    """Calculates average response time for each user."""
    df = df[(df["user"] != "group_notification") & (df["user"] != "Meta AI")]

    df["prev_user"] = df["user"].shift(1)
    df["prev_timestamp"] = df["timestamp"].shift(1)
    df["prev_date"] = df["date"].shift(1)

    df["response_time"] = (df["timestamp"] - df["prev_timestamp"]).dt.total_seconds() / 60
    df.loc[df["user"] == df["prev_user"], "response_time"] = None
    df.loc[df["date"] != df["prev_date"], "response_time"] = None

    df.drop(columns=["prev_user", "prev_timestamp", "prev_date"], inplace=True)
    df['response_time'] = df['response_time'].fillna(0)

    return df


def average_response_time(df):
    """Finds the average response time per user."""
    return df.groupby("user")["response_time"].mean().dropna().reset_index().rename(
        columns={"response_time": "Avg Response Time (minutes)"})


def response_time_weekday_vs_weekend(df):
    """Compares response time on weekdays vs weekends."""
    df["is_weekend"] = df["weekday"].isin(["Saturday", "Sunday"])
    return df.groupby("is_weekend")["response_time"].mean().reset_index().replace({True: "Weekend", False: "Weekday"})
