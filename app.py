import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import helper
import zipfile
import io
import base64


# ==========================
# Set Background Image
# ==========================
def set_bg_from_local(image_path):
    with open(image_path, "rb") as img_file:
        encoded_img = base64.b64encode(img_file.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_img}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


set_bg_from_local("backgroundImage2.jpg")

# ==========================
# App Title & Description
# ==========================
st.title("WhatsApp Chat Analyzer")

with st.expander("About This App"):
    st.markdown(
        """
        This application provides in-depth insights into WhatsApp conversations, including:  
        - Message trends over time  
        - Most active participants  
        - Commonly used words and emojis  
        - Response time analysis  

        **Best Experience on PC**  
        The application is optimized for desktop use for better visualization.  

        **How to Export Your WhatsApp Chat**  
        1. Open WhatsApp on your phone.  
        2. Select the chat you want to analyze.  
        3. Tap **More > Export Chat** (choose *Without Media* for faster processing).  
        4. Upload the **.txt** or **.zip** file below.  
        """
    )

# ==========================
# File Upload Section
# ==========================
with st.expander("Upload Your Chat File"):
    uploaded_file = st.file_uploader("Choose a .txt or .zip file")

if uploaded_file is not None:
    # Handling ZIP files
    if uploaded_file.name.endswith('.zip'):
        try:
            with zipfile.ZipFile(io.BytesIO(uploaded_file.getvalue()), 'r') as z:
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                if txt_files:
                    with z.open(txt_files[0]) as f:
                        data = f.read().decode(errors="ignore")
                else:
                    st.error("No valid WhatsApp chat text file found in the ZIP.")
                    st.stop()
        except zipfile.BadZipFile:
            st.error("Invalid ZIP file. Please upload a valid WhatsApp chat export.")
            st.stop()
    else:
        data = uploaded_file.getvalue().decode(errors="ignore")

    # ==========================
    # Data Processing
    # ==========================
    df = helper.preprocess_chat(data)
    user_analysis = st.toggle("Analyze Specific User", value=False)
    selected_user = "Overall"

    if user_analysis:
        user_list = sorted(set(df['user']) - {"group_notification"})
        user_list.insert(0, "Overall")
        selected_user = st.selectbox("Select a user", user_list)

    if st.button("Show Analysis"):
        # ==========================
        # Chat Summary
        # ==========================
        st.subheader("Chat Summary")
        num_messages, word_count, media_count, link_count = helper.chat_statistics(selected_user, df)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Messages", num_messages)
            st.metric("Media Shared", media_count)
        with col2:
            st.metric("Total Words", word_count)
            st.metric("Links Shared", link_count)

        # ==========================
        # Monthly Activity
        # ==========================
        st.subheader("Monthly Activity")
        monthly_data = helper.monthly_timeline(selected_user, df)
        fig = px.line(monthly_data, x='time', y='message', markers=True, title="Messages Over Time",
                      line_shape='spline', color_discrete_sequence=['green'])
        st.plotly_chart(fig)

        # ==========================
        # Daily Activity
        # ==========================
        st.subheader("Daily Activity")
        daily_data = helper.daily_message_count(selected_user, df)
        fig = px.line(daily_data, x='date', y='message', markers=True, title="Messages Per Day",
                      line_shape='spline', color_discrete_sequence=['red'])
        st.plotly_chart(fig)

        # ==========================
        # Weekly Activity Heatmap
        # ==========================
        st.subheader("Weekly Activity Heatmap")
        heatmap_data = helper.weekly_activity(selected_user, df)
        fig = px.imshow(heatmap_data, color_continuous_scale='Blues', title="Messages Heatmap",
                        labels={'x': 'Hour of the Day', 'y': 'Day of the Week'}, text_auto=True)
        st.plotly_chart(fig)

        # ==========================
        # Word Cloud
        # ==========================
        st.subheader("Word Cloud")
        wordcloud = helper.generate_wordcloud(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

        # ==========================
        # Emoji Analysis
        # ==========================
        st.subheader("Emoji Analysis")
        col1, col2 = st.columns(2)
        with col1:
            emoji_data = helper.emoji_usage(selected_user, df)
            st.dataframe({"Emoji": emoji_data[0], "Count": emoji_data[1]})
        with col2:
            df_emoji = pd.DataFrame({"Emoji": emoji_data[0], "Count": emoji_data[1]})
            fig = px.pie(df_emoji, names="Emoji", values="Count", title="Most Used Emojis",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig)

        # ==========================
        # Active Users Analysis
        # ==========================
        if selected_user == 'Overall':
            st.subheader("Most Active Users")
            active_users = helper.most_active_user(df)
            df_active = pd.DataFrame(active_users)
            fig = px.bar(df_active, y='names', x='counts', orientation='h', title="Most Active Users",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig)

        # ==========================
        # Response Time Analysis
        # ==========================
        st.subheader("Response Time Analysis")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Average Response Time per User")
            avg_response_time = helper.average_response_time(df)
            st.dataframe(avg_response_time)

        with col2:
            st.subheader("Peak Response Time Hours")
            fig = px.histogram(df, x="hour", title="Peak Response Time Hours",
                               labels={"hour": "Hour of the Day"},
                               color_discrete_sequence=["blue"], nbins=24)
            st.plotly_chart(fig)

        # Response Time Distribution
        st.subheader("Response Time Distribution")
        response_time_data = helper.compute_response_time(df)
        fig = px.histogram(response_time_data, x='response_time', title="Response Time Distribution",
                           color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig)
