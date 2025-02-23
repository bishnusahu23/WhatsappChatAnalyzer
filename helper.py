import pandas as pd
import re
from wordcloud import WordCloud
import emoji
from collections import Counter

import re

import string




def preprocess(chat):
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}'
    date = re.findall(pattern, chat)
    date = [x.replace(" - ", "") for x in date]
    text = re.split(pattern, chat)[1:]
    text = [x.replace(" - ", "") for x in text]

    df = pd.DataFrame({'date': date, 'text': text})
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y, %H:%M')

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

    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.strftime('%b')
    df['day'] = df['date'].dt.day
    df['hour'] = df['date'].dt.hour
    df['weekday'] = df['date'].dt.day_name()

    return df

def calculate_stats(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]
    num_messages = df.shape[0]
    media_len = df[df['message'] == '<Media omitted>\n'].shape[0]
    word_count = sum(df['message'].str.split().str.len())
    link_count = df['message'].str.contains("http").sum()
    return num_messages, word_count, media_len, link_count

def daily_activity(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]
    return df.groupby(df['date'].dt.date)['message'].count().reset_index()

def weekly_activity_heatmap(user, df):
    if user != 'Overall':
        df = df[df['user'] == user]
    heatmap_data = df.groupby(['weekday', 'hour'])['message'].count().unstack().fillna(0)
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
    temp_df = temp_df[temp_df['message'] != '<Media omitted>\n']
    temp_df = temp_df[~temp_df['message'].str.strip().isin(['null', 'null\n', ''])]

    # remove urls and punctuation

    def remove_extras(text):
        text = re.sub(r'http[s]?://\S+', '', text)  # Remove URLs
        text = re.sub(r'@\d{10,}', '', text)  # Remove numbers like @1234567890
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

    wc = WordCloud(width=400, height=200, min_font_size=7, background_color='white',max_words=150).generate(" ".join(words))
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




