import pandas as pd
import re
from wordcloud import WordCloud
import emoji
from collections import Counter
import re
import string
import numpy as np
from PIL import Image, ImageDraw


def preprocess(chat):
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s?[APM\u202F]*'
    date = re.findall(pattern, chat)
    text = re.split(pattern, chat)[1:]
    text = [re.sub(r'\s*-\s*', '', x) for x in text]
    df = pd.DataFrame({'timestamp': date, 'text': text})

    df['text'] = df['text'].str.strip()
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')

    name, message = [], []
    for i in df['text']:
        match = re.match(r'([\w\W]+?):\s', i)
        if match:
            name.append(match.group(1))
            message.append(i[len(match.group(0)):])
        else:
            name.append('group_notification')
            message.append(i)

    df['user'] = name
    df['message'] = message
    df.drop(columns=['text'], inplace=True)

    df['year'] = df['timestamp'].dt.year
    df['month'] = df['timestamp'].dt.strftime('%b')
    df['day'] = df['timestamp'].dt.day
    df['hour'] = df['timestamp'].dt.hour
    df['Day_name'] = df['timestamp'].dt.day_name()
    df["date"] = df["timestamp"].dt.date

    return df

def calculate_stats(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]

    num_messages = df.shape[0]
    media_len = df[df['message'] == '<Media omitted>\n'].shape[0]
    df['message'] = df['message'].astype(str)
    word_count = sum(df['message'].str.split().str.len())
    link_count = df['message'].str.contains("http").sum()
    return num_messages, word_count, media_len, link_count

def daily_activity(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]
    return df.groupby(df['date'])['message'].count().reset_index()

def weekly_activity_heatmap(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]
    heatmap_data = df.groupby(['Day_name', 'hour'])['message'].count().unstack().fillna(0)
    return heatmap_data

def hourly_distribution(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]
    return df.groupby('hour')['message'].count()

# cleaning like removing url, punctuation, stopwords, group notification, medias
def cleaned_message(df):
    with open(r"stopwords_hindi-english-telugu.txt", 'r') as file:
        stopwords = file.read()

    temp_df = df[df['user'] != 'group_notification']
    temp_df = temp_df[temp_df['message'] != '<Media omitted>']
    temp_df = temp_df[temp_df['message'] != 'This message was deleted']
    temp_df = temp_df[~temp_df['message'].str.strip().isin(['null', 'null\n', ''])]

    # remove urls and punctuation

    def remove_extras(text):
        text = re.sub(r'http[s]?://\S+', '', text)  # Remove URLs
        text = re.sub(r'[@]?\d{10,}', '', text)  # Remove numbers like @1234567890
        text = re.sub(r'<.*?>', '', text)  # Remove HTML tags

        tokens = text.split()  # Tokenize text (split into words)

        tokens = [word for word in tokens if word not in string.punctuation]  # Remove punctuation
        tokens = [word for word in tokens if word.lower() not in stopwords]  # Remove stopwords

        cleaned_text = " ".join(tokens)  # Reconstruct text
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()  # Normalize spaces

        return cleaned_text

    temp_df['message'] = temp_df['message'].apply(remove_extras)

    words = []
    for message in temp_df['message']:
        for word in message.lower().split():
            if word not in stopwords:
                words.append(word)
    return words

def most_common_words(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]
    words = cleaned_message(df)
    words=[word for word in words if word not in emoji.EMOJI_DATA]
    word_df=pd.DataFrame(Counter(words).most_common(20))
    return word_df

def create_wordcloud(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]
    words=cleaned_message(df)

    mask_size = (800, 800)  # Define the size of the word cloud
    mask = Image.new("L", mask_size, 255)  # Create a white canvas
    draw = ImageDraw.Draw(mask)
    draw.ellipse((50, 100, 750, 700), fill=0)  # Draw an ellipse (adjust for best shape)
    mask = np.array(mask)

    wc = WordCloud(min_font_size=7,width=800, height=800,mode='RGBA', background_color=None,mask=mask,max_words=150).generate(" ".join(words))
    return wc

def emoji_counter(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]
    emojis = [c for message in df['message'] for c in message if c in emoji.EMOJI_DATA]
    return pd.DataFrame(Counter(emojis).most_common(10))

def monthly_timeline(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]

    # Group messages by year and month
    temp = df.groupby(['year', 'month']).size().reset_index(name='message')  # Ensure 'message' column exists

    # Create 'time' column in YYYY-MMM format (e.g., "2024-Jan")
    temp['time'] = temp['year'].astype(str) + "-" + temp['month'].astype(str)

    return temp


def most_active_user(df):
    users=list(df['user'].unique())
    if any(users[users=='group_notification']):
        users.remove('group_notification')
    elif any(users[users=='Meta AI']):
        users.remove('Meta AI')
    else:
        pass
    names=[]
    counts=[]
    for user in users:
        count=len(df[df['user']==user])
        names.append(user)
        counts.append(count)
    return {'names':names,'counts':counts}


def calculate_response_time(df):
    df = df[df["user"] != "group_notification"]
    df = df[df["user"] != "Meta AI"]

    df = df.sort_values("timestamp")
    df["prev_user"] = df["user"].shift(1)
    df["prev_timestamp"] = df["timestamp"].shift(1)

    # Compute Response Time (only when user changes and same-day chat)
    df["Response time (minutes)"] = (df["timestamp"] - df["prev_timestamp"]).dt.total_seconds() / 60  # Convert to minutes

    # Ignore consecutive messages from the same user
    df.loc[df["user"] == df["prev_user"], "Response time (minutes)"] = None

    df.loc[df["Response time (minutes)"] > 240, "Response time (minutes)"] = None

    # Drop columns
    df.drop(columns=["prev_user", "prev_timestamp"], inplace=True)
    df['Response time (minutes)'] = df['Response time (minutes)'].fillna(0)
    return df

# Calculate average response time per user
def average_response_time_user(df):
    df=calculate_response_time(df)
    avg_response_time = df.groupby("user")["Response time (minutes)"].mean().dropna().reset_index()
    avg_response_time.columns = ["User", "Avg Response Time (minutes)"]
    return avg_response_time


def day_wise_response_time(df):
    df = calculate_response_time(df)
    day_wise_response = df.groupby("Day_name")["Response time (minutes)"].mean().reset_index()

    return day_wise_response


def find_links(df, user):
    if user != 'Overall':
        df = df[df['user'] == user]

    links = []
    dates = []

    for _, row in df.iterrows():
        message = row['message']
        link_list = re.findall(r'http[s]?://\S+', message)  # Extract links

        for link in link_list:  # Ensure each link gets a corresponding date entry
            dates.append(row['date'])
            links.append(link)

    return pd.DataFrame({"Date": dates, "Links": links})