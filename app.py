import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import helper
import zipfile
import io
import base64
from datetime import datetime
from io import BytesIO

# Set up caching for performance
@st.cache_data
def preprocess_data(file_data):
    return helper.preprocess(file_data)

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

st.sidebar.title("Settings & Filters")

dark_mode = st.sidebar.toggle("Dark Mode")
if dark_mode:
    st.markdown(
        """<style>
        body { background-color: #1e1e1e; color: white; }
        """, unsafe_allow_html=True
    )

st.title("WhatsApp Chat Analyzer")

uploaded_file = st.sidebar.file_uploader("Upload WhatsApp Chat File (.txt or .zip)")

date_range = st.sidebar.date_input("Select Date Range", [])

user_analysis = st.sidebar.toggle("Analyze Specific User", value=False)
selected_user = "Overall"

if uploaded_file is not None:
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

    df = preprocess_data(data)

    if user_analysis:
        user_list = sorted(set(df['user']) - {"group_notification", "Meta AI"})
        user_list.insert(0, "Overall")
        selected_user = st.sidebar.selectbox("Select a user", user_list)

    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]

    st.sidebar.subheader("Export Data")
    if st.sidebar.button("Download CSV"):
        csv = df.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("Download CSV", csv, "chat_analysis.csv", "text/csv")

    if st.sidebar.button("Download Image (Charts)"):
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        st.sidebar.download_button("Download Image", img_buffer, "chat_analysis.png", "image/png")

    st.subheader("Chat Summary")
    num_messages, length, media_len, len_links = helper.calculate_stats(selected_user, df)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Messages", num_messages)
        st.metric("Media Shared", media_len)
    with col2:
        st.metric("Total Words", length)
        st.metric("Links Shared", len_links)

    # Monthly Activity
    st.subheader("Monthly Activity Overview")
    st.caption("Hover over the chart to see detailed information.")
    temp = helper.monthly_timeline(selected_user, df)
    fig = px.line(temp, x='time', y='message', markers=True, title="Messages Over Time",
                  line_shape='spline', color_discrete_sequence=['green'])
    fig.update_layout(

        hoverlabel=dict(
            font_size=14,
            font_family="Arial",
            font_color="blue",  # Tooltip text color
            bgcolor="black"  # Tooltip background color
        )
    )

    fig.update_traces(
        textfont=dict(color="black"),
    )
    st.plotly_chart(fig)

    # Daily Activity
    st.subheader("Daily Message Trends")
    st.caption("Hover over the chart to see detailed information.")
    daily_temp = helper.daily_activity(selected_user, df)
    fig = px.line(daily_temp, x='date', y='message', markers=True, title="Messages Per Day",
                  line_shape='spline', color_discrete_sequence=['red'])
    fig.update_layout(

        hoverlabel=dict(
            font_size=14,
            font_family="Arial",
            font_color="blue",  # Tooltip text color
            bgcolor="black"  # Tooltip background color
        )
    )

    fig.update_traces(
        textfont=dict(color="black"),
    )
    st.plotly_chart(fig)

    # Weekly Activity Heatmap
    st.subheader("Weekly Activity Heatmap")
    st.caption("The darker the area, the higher the message frequency at the corresponding day and time. Hover to see details")
    heatmap = helper.weekly_activity_heatmap(selected_user, df)
    fig = px.imshow(heatmap,color_continuous_scale='Blues', title="Messages Heatmap",
                    labels={'x': 'Hour of the Day', 'y': 'Day of the Week'}, text_auto=True)
    fig.update_layout(

        hoverlabel=dict(
            font_size=14,
            font_family="Arial",
            font_color="blue",  # Tooltip text color
            bgcolor="black"  # Tooltip background color
        )
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(24)),  # Assuming 24-hour format
        ticktext=[f"{i}" for i in range(24)]  # Custom labels
    )

    fig.update_traces(
        textfont=dict(color="black"),
        hovertemplate="Hour: %{x}<br>Day: %{y}<extra></extra>"
    )
    st.plotly_chart(fig)

    # Wordcloud
    st.subheader("Most Frequently Used Words")
    st.caption("The larger the word, the more frequently it appears in the conversation.")
    wc = helper.create_wordcloud(selected_user, df)
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)


    # Emoji Analysis
    st.subheader("Emoji Usage Analysis")
    col1, col2 = st.columns(2)
    with col1:
        emojis = helper.emoji_counter(selected_user, df)
        if emojis is None or emojis.empty:
            st.write('No emojis found')
        else:
            st.dataframe({"Emoji": emojis[0], "Count": emojis[1]},hide_index=True, use_container_width=True)
    with col2:
        emojis = helper.emoji_counter(selected_user, df)

        if emojis is None or emojis.empty:
            pass
        else:
            df_emoji = pd.DataFrame({"Emoji": emojis[0], "Count": emojis[1]})
            fig = px.pie(df_emoji, names="Emoji", values="Count", title="Most Used Emojis",
                         color_discrete_sequence=px.colors.qualitative.Pastel)

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",  # Fully transparent background
                plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot area
                hoverlabel=dict(
                    font_size=14,
                    font_family="Arial",
                    font_color="blue",  # Tooltip text color
                    bgcolor="black"  # Tooltip background color
                )
            )

            fig.update_traces(
                textfont=dict(color="black"),
            )

            st.plotly_chart(fig)

    st.subheader('LLinks Shared in the Chat')
    links_df=helper.find_links(df,selected_user)
    if links_df is None or links_df.empty:
        st.write('No links found in the chat')
    else:
        st.dataframe(links_df, use_container_width=True,hide_index=True)


    if selected_user=='Overall':
        dic=helper.most_active_user(df)
        dataframe=pd.DataFrame(dic)
        st.subheader("Most Active Participants")
        fig=px.bar( data_frame=dataframe,y='names',x='counts', orientation='h', title='Most active user',
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    labels={'names': 'Name', 'counts': 'Count of messages'})

        fig.update_layout(

            hoverlabel=dict(
                font_size=14,
                font_family="Arial",
                font_color="blue",  # Tooltip text color
                bgcolor="black"  # Tooltip background color
            )
        )

        fig.update_traces(
            textfont=dict(color="black")
        )
        st.plotly_chart(fig)

        st.subheader("Response Time Analysis")
        st.caption("Analyzing how quickly users respond to messages.")
        # response time
        response_time_df= helper.calculate_response_time(df)
        fig = px.histogram(response_time_df['Response time (minutes)'], title='Overall response time',
                     color_discrete_sequence=px.colors.qualitative.Pastel, log_y=True,
                           labels={'value': 'Response time (minutes)', 'count': 'Number of messages'}
                     )

        fig.update_layout(
            showlegend=False,
            hoverlabel=dict(
                font_size=14,
                font_family="Arial",
                font_color="blue",  # Tooltip text color
                bgcolor="black"  # Tooltip background color
            )
        )

        fig.update_traces(
            textfont=dict(color="black")
        )
        st.plotly_chart(fig)

        col1,col2=st.columns(2)
        with col1:
            st.markdown('Average response time per user')
            avg_response_time = helper.average_response_time_user(df)
            st.dataframe(avg_response_time,hide_index=True,use_container_width=True)
        with col2:
            st.markdown('Average response time over days')
            day_response=helper.day_wise_response_time(df)
            st.dataframe(day_response,hide_index=True, use_container_width=True)

