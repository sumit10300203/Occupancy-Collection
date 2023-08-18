import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import numpy as np
import requests as re
from bs4 import BeautifulSoup as bs
from datetime import datetime
from pytz import timezone
import json as js

st.set_page_config(
    page_title="Occupancy Collection",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

with open("authorization.json") as f:
    key = js.load(f)
    NOTION_TOKEN = key["NOTION_TOKEN"]
    DATABASE_ID = key["DATABASE_ID"]
    headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"}

def get_pages(filter_username = None, num_pages=None):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    if filter_username:
        payload = {"page_size": page_size, 'filter': {'property': 'name', 'rich_text': {'contains': filter_username}}}
    else:
        payload = {"page_size": page_size}
    response = re.post(url, json=payload, headers=headers)

    data = response.json()

    results = data["results"]
    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = re.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results

key = []
names = []
password = []
for page in get_pages():
    key.append(page['properties']['key']['title'][0]['text']['content'])
    names.append(page['properties']['name']['rich_text'][0]['text']['content'])
    password.append(page['properties']['password']['rich_text'][0]['text']['content'])

password = stauth.Hasher(password).generate()
credentials = {"usernames":{}}
        
for uname,name,pwd in zip(key,names,password):
    user_dict = {"name": name, "password": pwd}
    credentials["usernames"].update({uname: user_dict})

authenticator = stauth.Authenticate(credentials, "occupancy_collector_login", "login", cookie_expiry_days = 1)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status is None:
    st.warning("Please enter your username and password")

if authentication_status:
    @st.cache_data
    def convert_df(df, index = False):
        return df.to_csv(index = index).encode('utf-8')

    def submit():
        st.session_state.occupancy = st.session_state.widget
        st.session_state.widget = ''

    def update():
        tmp = st.session_state.editeddf['edited_rows']
        for i in tmp:
            for j in tmp[i]:
                edited_df.loc[i][j] = tmp[i][j]
            edited_df.loc[i]['Last Modified'] = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
            edited_df.loc[i]['Date'] = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")


    st.header(f":red[Welcome] {name}", anchor = False)
    authenticator.logout("Logout", "sidebar")
    
    tab1, tab2= st.tabs(["👨‍👩‍👧‍👦 Occupancy Collection", "🔗 Merged Occupancy with Sensor data"])
    
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame(columns = ['Time Entered', 'Last Modified', 'Occupancy'])
    
    if 'occupancy' not in st.session_state:
        st.session_state.occupancy = ''
    
    with tab1.container():
        col = st.columns(2)
        with col[0].container():
            col[0].text_input('Enter current occupancy', key='widget', placeholder = '', on_change=submit)
            if st.session_state.occupancy:
                st.session_state.df.loc[st.session_state.df.shape[0]] = [datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"), datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"), st.session_state.occupancy]
                st.session_state.occupancy = ''
            edited_df = col[0].data_editor(st.session_state.df, num_rows="fixed", key = 'editeddf', on_change = update, hide_index = True, use_container_width = True, disabled=['Last Modified'])
            st.session_state.df = edited_df
    
        st.caption('**:red[Note:] Only Time Entered and Occupancy can be modified.**')
    
        disabled = True
        if st.session_state.df.shape[0]:
            disabled = False
        st.download_button(label="Download data as CSV", data = convert_df(st.session_state.df), file_name=f'Occupancy_{datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d_%H:%M:%S")}.csv', mime='text/csv', disabled = disabled)
    
    with tab2.container():
        disabled = True
        merged_df = pd.DataFrame()
        col = st.columns(2)
        with col[0].container():
            sensor_file = st.file_uploader("**Choose Sensor CSV file**", type = "csv")
        with col[1].container():
            occupancy_file = st.file_uploader("**Choose Occupancy CSV file**", type = "csv")
        if sensor_file is not None and occupancy_file is not None:
            st.divider()
            option = st.radio("Choose Occupancy Collection Type", ('Direct', 'Cummulative'), horizontal = True)
            try:
                sensor_data = pd.read_csv(sensor_file, usecols = ['Date', 'Time', 'CO (ppm)', 'NO2 (ppm)', 'CO2 (ppm)', 'TVOC (ppb)', 
                                                                                      'PM1 (ug/m3)', 'PM2.5 (ug/m3)', 'PM10 (ug/m3)', 'Temperature (C)',
                                                                                      'Humidity (%)', 'Sound (dB)'], parse_dates=[['Date', 'Time']])
                occupancy_data = pd.read_csv(occupancy_file, usecols = ['Time Entered', 'Occupancy'])
                sensor_data.rename({"Date_Time": "Timestamp"}, axis = 1, inplace = True)
                sensor_data.set_index("Timestamp", drop = True, inplace = True)
                occupancy_data['Time Entered'] = pd.to_datetime(occupancy_data['Time Entered'])
                occupancy_data.set_index('Time Entered', drop = True, inplace = True)
                # occupancy_data = occupancy_data.asfreq(freq='S', method = 'ffill', fill_value = 0)
                if option == "Cummulative":
                    occupancy_data['Occupancy'] = occupancy_data['Occupancy'].cumsum()
                merged_df = sensor_data.join(occupancy_data, how = "outer")
                merged_df['Occupancy'].fillna(method="ffill", inplace = True)
                merged_df.dropna(how = 'any', inplace = True)
                disabled = False
            except:
                st.error('Error in CSV files, please check the columns name are identical to the requirement and re upload again', icon="🚨")
                disabled = True
    
        st.download_button(label = "Download Merged CSV file", data = convert_df(merged_df, index = True), file_name=f'Sensor_data_with_Occupancy_{datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d_%H:%M:%S")}.csv', mime='text/csv', disabled = disabled)
        st.caption('**:red[Note:] If timestamp range matches in both csv, then only it will be merged.**')
