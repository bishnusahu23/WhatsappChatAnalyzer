import streamlit as st
import re
import pandas as pd
from urlextract import URLExtract
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

# preprocessing
def preprocess(chat):
    pattern='\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}'
    date=re.findall(pattern,chat)
    date=[x.replace(" - ","") for x in date]
    text=re.split(pattern,chat)[1:]
    text=[x.replace(" - ","") for x in text]

    df=pd.DataFrame({'date':date,'text':text})
    df['date']=pd.to_datetime(df['date'],format='%m/%d/%y, %H:%M')

    name=[]
    message=[]
    for i in df['text']:
        pattern='([\w\W]+?):\s'
        if re.findall(pattern,i):
            name.append(re.split(pattern,i)[1])
            message.append(re.split(pattern,i)[2])
            
        else:
            name.append('group_notification')
            message.append(i)
    df['user']=name
    df['message']=message

    df.drop(columns=['text'],inplace=True)
    df['year']=df['date'].dt.year
    df['month']=df['date'].dt.month_name()
    df['day']=df['date'].dt.day
    df['hour']=df['date'].dt.hour
    df['minute']=df['date'].dt.minute
    return df

# calculate the stats
def cal_stats(user,df):
 if user!='Overall':
  df=df[df['user']==user]
 # shared media
 media_len=df[df['message']=='<Media omitted>\n'].shape[0]
 # total messages
 num_messages=df.shape[0]
 # total words
 words=[]
 links=[]
 for i in df['message']:
  words.extend(i.split())
  
  # extracting urls
  extractor=URLExtract()
  urls=extractor.find_urls(i)
  links.extend(urls)
 
 return num_messages, len(words),media_len, len(links)


def group_analysis(user,df):
 most_active_users=df['user'].value_counts().head().reset_index().rename(columns={'index':'user','user':'messages'})
 per_active=round(df['user'].value_counts()/df.shape[0]*100,2).reset_index().rename(columns={'index':'User','user':'Percentage'})
 return most_active_users,per_active

def create_wordcloud(user,df):
 if user!='Overall':
  df=df[df['user']==user]
 wc=WordCloud(width=500,height=500,min_font_size=10, background_color='white').generate(df['message'].str.cat(sep=" "))
 return wc

# STREAMLIT PAGE
st.sidebar.title("Whatsapp Chat Analyzer")
uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
 bytes_data = uploaded_file.getvalue()
 data=bytes_data.decode("utf-8")
 df=preprocess(data)
 st.dataframe(df)
 user_list=df['user'].unique().tolist()
 user_list.remove('group_notification')
 user_list.sort()
 user_list.insert(0,"Overall")
 selected_user=st.sidebar.selectbox("Select a user",user_list)

 
 if st.sidebar.button("Show analysis"):

  num_messages,length,media_len, len_links= cal_stats(selected_user,df)
  col1,col2,col3,col4=st.columns(4)

  with col1:
   st.header("Total messages:")
   st.title(num_messages)
  with col2:
   st.header("Total words:")
   st.title(length)
  with col3:
   st.header("Total media shared:")
   st.title(media_len)
  with col4:
   st.header("Total links shared:")
   st.title(len_links)


  # active users analysis
  st.title("Most active users")
  fig, ax=plt.subplots()
  active_users, active_per=group_analysis(selected_user,df)
 
  col1, col2=st.columns(2)
  with col1:
   ax.bar(active_users.user,active_users.messages,color='grey')
   plt.xticks(rotation=30)
   st.pyplot(fig)
   
  with col2:
   st.dataframe(active_per)

 # wordcloud
  st.title("Wordcloud")
  wc=create_wordcloud(selected_user,df)
  fig, ax=plt.subplots()
  ax.imshow(wc)
  st.pyplot(fig)
































