import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import helper

st.sidebar.title("📊 WhatsApp Chat Analyzer")
uploaded_file = st.sidebar.file_uploader("📁 Choose a file")

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")
    df = helper.preprocess(data)

    user_list = df['user'].unique().tolist()
    if 'group_notification' in user_list:
        user_list.remove('group_notification')
    user_list.sort()
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("👤 Select a user", user_list)

    if st.sidebar.button("🔍 Show Analysis"):
        num_messages, length, media_len, len_links = helper.calculate_stats(selected_user, df)

        # Top Statistics
        st.title("📊 Chat Summary")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
         st.subheader("Total Messages")
         st.markdown(f"<p style='font-size:24px; font-weight:bold;'>{num_messages}</p>", unsafe_allow_html=True)

        with col2:
         st.subheader("Total Words")
         st.markdown(f"<p style='font-size:24px; font-weight:bold;'>{length}</p>", unsafe_allow_html=True)

        with col3:
         st.subheader("Media Shared")
         st.markdown(f"<p style='font-size:24px; font-weight:bold;'>{media_len}</p>", unsafe_allow_html=True)

        with col4:
         st.subheader("Links Shared")
         st.markdown(f"<p style='font-size:24px; font-weight:bold;'>{len_links}</p>", unsafe_allow_html=True)

        # Monthly Timeline
        st.title("📆 Monthly Activity")
        temp = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(temp['time'], temp['message'], color='green', marker='o', linestyle='dashed')
        plt.xticks(rotation=45)
        plt.xlabel("Month-Year")
        plt.ylabel("Messages")
        st.pyplot(fig)

        # Daily Activity
        st.title("📅 Daily Activity")
        daily_temp = helper.daily_activity(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(daily_temp['date'], daily_temp['message'], color='red', marker='o', linestyle='dashed')
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Messages")
        st.pyplot(fig)

        # Weekly Heatmap
        st.title("🔥 Weekly Activity Heatmap")
        heatmap = helper.weekly_activity_heatmap(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.heatmap(heatmap, cmap="Blues", linewidths=0.3, annot=True, fmt=".0f")
        plt.ylabel("Day of the Week")
        plt.xlabel("Hour of the Day")
        st.pyplot(fig)

        # Hourly Message Distribution
        st.title("⏰ Hourly Message Distribution")
        hourly = helper.hourly_distribution(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(hourly.index, hourly.values, color='purple', alpha=0.7)
        plt.xlabel("Hour of the Day")
        plt.ylabel("Number of Messages")
        plt.xticks(range(24))
        st.pyplot(fig)

        # Wordcloud
        st.title("☁️ Wordcloud")
        wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(wc, interpolation="bi-linear")
        ax.axis("off")
        st.pyplot(fig)

        # Top words used (bar chart)
        st.title("🔠 Most Common Words")
        top_words = helper.most_common_words(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.barh(top_words[0], top_words[1], color='orange', alpha=0.7)
        plt.xlabel("Frequency")
        plt.ylabel("Words")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Emoji Analysis
        st.title("😀 Emoji Analysis")
        col1, col2 = st.columns(2)
        with col1:
            emojis = helper.emoji_counter(selected_user, df)
            st.dataframe(emojis)
        with col2:
            fig, ax = plt.subplots()
            ax.pie(emojis[1], labels=emojis[0], autopct='%0.2f')
            st.pyplot(fig)
