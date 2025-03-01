import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import helper
import zipfile
import io
import base64

def set_bg_from_local(image_path):
    """Encodes local image and sets it as Streamlit background"""
    with open(image_path, "rb") as img_file:
        encoded_img = base64.b64encode(img_file.read()).decode()

    # Apply background image with CSS
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_img}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        /* Overlay container for all content */
        .overlay {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);  /* Dark semi-transparent overlay */
        padding: 30px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        }}

        /* Ensure all text is white */
        h1, h2, h3, h4, h5, h6, p, label, .stTextInput, .stDataFrame, .stTable {{
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


set_bg_from_local("backgroundImage.jpg")

st.markdown('<div class="overlay">', unsafe_allow_html=True)

st.title("WhatsApp Chat Analyzer")

# File Upload Section
with st.expander("Upload WhatsApp Chat File"):
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

    # Preprocess Data
    df = helper.preprocess(data)
    st.write(df.head())

    # User Selection
    user_analysis = st.toggle("Analyze Specific User", value=False)
    selected_user = "Overall"

    if user_analysis:
        user_list = sorted(set(df['user']) - {"group_notification"})
        user_list.insert(0, "Overall")
        selected_user = st.selectbox("Select a user", user_list)

    if st.button("Show Analysis"):
        # Top Statistics
        num_messages, length, media_len, len_links = helper.calculate_stats(selected_user, df)
        st.subheader("Chat Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Messages", num_messages)
            st.metric("Media Shared", media_len)
        with col2:
            st.metric("Total Words", length)
            st.metric("Links Shared", len_links)

        # Monthly Activity
        st.subheader("Monthly Activity")
        temp = helper.monthly_timeline(selected_user, df)
        fig = px.line(temp, x='time', y='message', markers=True, title="Messages Over Time",
                      line_shape='spline', color_discrete_sequence=['green'])
        st.plotly_chart(fig)

        # Daily Activity
        st.subheader("Daily Activity")
        daily_temp = helper.daily_activity(selected_user, df)
        fig = px.line(daily_temp, x='date', y='message', markers=True, title="Messages Per Day",
                      line_shape='spline', color_discrete_sequence=['red'])
        st.plotly_chart(fig)

        # Weekly Activity Heatmap
        st.subheader("Weekly Activity Heatmap")
        heatmap = helper.weekly_activity_heatmap(selected_user, df)
        fig = px.imshow(heatmap, color_continuous_scale='Blues', title="Messages Heatmap",
                        labels={'x': 'Hour of the Day', 'y': 'Day of the Week'})
        st.plotly_chart(fig)

        # Wordcloud
        st.subheader("Wordcloud")
        wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)


        # Emoji Analysis
        st.subheader("Emoji Analysis")
        col1, col2 = st.columns(2)
        with col1:
            emojis = helper.emoji_counter(selected_user, df)
            st.dataframe({"Emoji": emojis[0], "Count": emojis[1]})
        with col2:
            df_emoji = pd.DataFrame({"Emoji": emojis[0], "Count": emojis[1]})
            fig = px.pie(df_emoji, names="Emoji", values="Count", title="Most Used Emojis",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="black")
            st.plotly_chart(fig)

st.markdown('</div>', unsafe_allow_html=True)