import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import helper
import zipfile
import io

st.title("WhatsApp Chat Analyzer")

# File Upload Section (Expanded for better visibility on mobile)
with st.expander("Upload WhatsApp Chat File"):
    uploaded_file = st.file_uploader("Choose a .txt or .zip file")

if uploaded_file is not None:

    # Handling ZIP files
    if uploaded_file.name.endswith('.zip'):
        try:
            with zipfile.ZipFile(io.BytesIO(uploaded_file.getvalue()), 'r') as z:
                file_names = z.namelist()

                # Look for a text file inside the ZIP
                txt_files = [f for f in file_names if f.endswith('.txt')]
                if txt_files:
                    with z.open(txt_files[0]) as f:
                        data = f.read().decode(errors="ignore")  # Ignore encoding errors
                else:
                    st.error("No valid WhatsApp chat text file found in the ZIP.")
                    st.stop()
        except zipfile.BadZipFile:
            st.error("Invalid ZIP file. Please upload a valid WhatsApp chat export.")
            st.stop()
    else:
        bytes_data = uploaded_file.getvalue()
        data = bytes_data.decode(errors="ignore")

    # Preprocess Data
    df = helper.preprocess(data)

    # User Selection Toggle (Better for Mobile)
    user_analysis = st.toggle("Analyze Specific User", value=False)

    if user_analysis:
        user_list = df['user'].unique().tolist()
        if 'group_notification' in user_list:
            user_list.remove('group_notification')
        user_list.sort()
        user_list.insert(0, "Overall")
        selected_user = st.selectbox("Select a user", user_list)
    else:
        selected_user = "Overall"

    if st.button("Show Analysis"):
        num_messages, length, media_len, len_links = helper.calculate_stats(selected_user, df)

        # Top Statistics - Adjusted for Mobile
        st.subheader("Chat Summary")
        col1, col2 = st.columns(2)

        with col1:
            st.metric(label="Total Messages", value=num_messages)
            st.metric(label="Media Shared", value=media_len)

        with col2:
            st.metric(label="Total Words", value=length)
            st.metric(label="Links Shared", value=len_links)

        # Monthly Activity
        st.subheader("Monthly Activity")
        temp = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(temp['time'], temp['message'], color='green', marker='o', linestyle='dashed')
        plt.xticks(rotation=45)
        plt.xlabel("Month-Year")
        plt.ylabel("Messages")
        st.pyplot(fig)

        # Daily Activity
        st.subheader("Daily Activity")
        daily_temp = helper.daily_activity(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(daily_temp['date'], daily_temp['message'], color='red', marker='o', linestyle='dashed')
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Messages")
        st.pyplot(fig)

        # Weekly Heatmap
        st.subheader("Weekly Activity Heatmap")
        heatmap = helper.weekly_activity_heatmap(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.heatmap(heatmap, cmap="Blues", linewidths=0.3, annot=True, fmt=".0f")
        plt.ylabel("Day of the Week")
        plt.xlabel("Hour of the Day")
        st.pyplot(fig)

        # Hourly Message Distribution
        st.subheader("Hourly Message Distribution")
        hourly = helper.hourly_distribution(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(hourly.index, hourly.values, color='purple', alpha=0.7)
        plt.xlabel("Hour of the Day")
        plt.ylabel("Number of Messages")
        plt.xticks(range(24))
        st.pyplot(fig)

        # Wordcloud
        st.subheader("Wordcloud")
        wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

        # Most Common Words
        st.subheader("Most Common Words")
        top_words = helper.most_common_words(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.barh(top_words[0], top_words[1], color='orange', alpha=0.7)
        plt.xlabel("Frequency")
        plt.ylabel("Words")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Emoji Analysis
        st.subheader("Emoji Analysis")
        col1, col2 = st.columns(2)
        with col1:
            emojis = helper.emoji_counter(selected_user, df)
            st.dataframe(emojis)
        with col2:
            fig, ax = plt.subplots()
            ax.pie(emojis[1], labels=emojis[0], autopct='%0.2f')
            st.pyplot(fig)
