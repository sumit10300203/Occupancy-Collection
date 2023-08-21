import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import numpy as np
from datetime import datetime
from pytz import timezone
import json as js

st.set_page_config(
    page_title="Occupancy Collection",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)
if 'authorization_df' not in st.session_state:
    st.session_state.authorization_df = pd.read_csv("Authentication.csv")

credentials = {"usernames":{}}

for uname,name,pwd in zip(st.session_state.authorization_df['username'],st.session_state.authorization_df['Name'],st.session_state.authorization_df['key']):
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

    def submit_3():
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
    
    tab1, tab2, tab3 = st.tabs(["👨‍👩‍👧‍👦 Occupancy Collection", "🔗 Merge Occupancy with Sensor data", "👀 View CSV file"])
    
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame(columns = ['Time Entered', 'Last Modified', 'Position', 'Occupancy'])

    if 'view_df' not in st.session_state:
        st.session_state.view_df = pd.DataFrame()
    
    if 'occupancy' not in st.session_state:
        st.session_state.occupancy = ''

    if 'widget' not in st.session_state:
        st.session_state.widget = ''
    
    with tab1.container():
        col = st.columns(2)
        with col[0].container():
            col_inner = col[0].columns(2)
            with col_inner[0].container():
                position = col_inner[0].text_input('**Enter current Position**', placeholder = 'Enter Position')
            if position:
                with col_inner[0].container():
                    col_inner[0].text_input('**Enter current Occupancy**', key='widget', placeholder = 'Enter Occupancy', on_change=submit_3)
                if st.session_state.occupancy and position:
                    st.session_state.df.loc[st.session_state.df.shape[0]] = [datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"), datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"), st.session_state.occupancy, position.lower()]
                    st.session_state.occupancy = ''
            edited_df = col[0].data_editor(st.session_state.df, num_rows="fixed", key = 'editeddf', on_change = update, hide_index = True, use_container_width = True, disabled=['Last Modified'])
            st.session_state.df = edited_df
    
        st.caption('**:red[Note:] Only Time Entered and Occupancy can be modified.**')
    
        disabled = True
        if st.session_state.df.shape[0]:
            disabled = False
        st.download_button(label="**Download data as CSV**", data = convert_df(st.session_state.df), file_name=f'Occupancy_{datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d_%H:%M:%S")}.csv', mime='text/csv', disabled = disabled)
    
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
            option1 = st.radio("**Choose Occupancy Collection Type**", ('Direct', 'Cummulative'), horizontal = True)
            option2 = st.radio("**Keep Zeros ?**", ('No', 'Yes'), horizontal = True)
            try:
                sensor_data = pd.read_csv(sensor_file, usecols = ['Date', 'Time', 'CO (ppm)', 'NO2 (ppm)', 'CO2 (ppm)', 'TVOC (ppb)', 
                                                                                      'PM1 (ug/m3)', 'PM2.5 (ug/m3)', 'PM10 (ug/m3)', 'Temperature (C)',
                                                                                      'Humidity (%)', 'Sound (dB)'], parse_dates=[['Date', 'Time']])
                occupancy_data = pd.read_csv(occupancy_file, usecols = ['Time Entered', 'Occupancy', 'Position'])
                sensor_data.rename({"Date_Time": "Timestamp"}, axis = 1, inplace = True)
                sensor_data.set_index("Timestamp", drop = True, inplace = True)
                occupancy_data['Time Entered'] = pd.to_datetime(occupancy_data['Time Entered'])
                occupancy_data.rename({'Time Entered': 'Timestamp'}, axis = 1, inplace = True)
                occupancy_data.set_index('Timestamp', drop = True, inplace = True)
                # occupancy_data = occupancy_data.asfreq(freq='S', method = 'ffill', fill_value = 0)
                if option1 == "Cummulative":
                    occupancy_data['Occupancy'] = occupancy_data['Occupancy'].cumsum()
                merged_df = sensor_data.join(occupancy_data, how = "outer")
                merged_df.reset_index(inplace = True)
                merged_df['Occupancy'].fillna(method="ffill", inplace = True)
                merged_df['Position'].fillna(method="ffill", inplace = True)
                merged_df.dropna(how = 'any', inplace = True)
                if option2 == 'No':
                    merged_df['Occupancy'].replace(to_replace=0, method='ffill', inplace=True)
                    merged_df = merged_df[merged_df['Occupancy'] != 0].reset_index(drop = True)
                disabled = False
            except:
                st.error('Error in CSV files, please check the columns name are identical to the requirement and re upload again', icon="🚨")
                disabled = True

        st.download_button(label = "**Download Merged CSV file**", data = convert_df(merged_df, index = False), file_name=f'Sensor_data_with_Occupancy_{datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d_%H:%M:%S")}.csv', mime='text/csv', disabled = disabled)
        st.caption('**:red[Note:] If timestamp range matches in both csv, then only it will be merged.**')

    with tab3.container():
        view_csv_file = st.file_uploader("**Choose CSV file**", type = "csv")
        if view_csv_file:
            st.session_state.view_df = pd.read_csv(view_csv_file)
            st.dataframe(st.session_state.view_df, use_container_width = True)
        
    # if tab4:            
    #     with tab4.container():
    #         col = st.columns(2)
    #         with col[0].container():
    #             col[0].subheader("Add Users", anchor= False)
    #             add_remove_users = col[0].radio("Operation:", ('Add', 'Remove'), horizontal = True)
    #             if add_remove_users == 'Add':
    #                 user_add_1 = col[0].text_input("**Enter Username**", key = 'user_add_1', placeholder="Enter Username")
    #                 user_add_2 = col[0].text_input("**Enter Name**", placeholder="Enter Name")
    #                 user_add_3 = col[0].text_input("**Enter Password**", type = 'password', placeholder="Enter Password")
    #                 proceed1 = col[0].button(label = "Continue", key = 'proceed1')
    #                 if user_add_1 and user_add_2 and user_add_3 and proceed1:
    #                     tmp = st.session_state.authorization_df[st.session_state.authorization_df['username'] == user_add_1]
    #                     if tmp.shape[0]:
    #                         col[0].warning(f"**{user_add_1} is already an User**")
    #                     else:
    #                         st.session_state.authorization_df.loc[-1] = [user_add_2, user_add_1, stauth.Hasher([user_add_3]).generate()[0], 0]
    #                         st.session_state.authorization_df.reset_index(inplace = True, drop = True)
    #                         col[0].success(f"**{user_add_1} added as User**")
    #                 st.session_state.authorization_df.to_csv('Authentication.csv', index = False)
    #             else:
    #                 user_del_1 = col[0].text_input("**Enter Username**", key = 'user_del_1', placeholder="Enter Username")
    #                 proceed2 = col[0].button(label = "Continue", key = 'proceed2')
    #                 if user_del_1 and proceed2:
    #                     tmp = st.session_state.authorization_df[st.session_state.authorization_df['username'] == user_del_1]
    #                     if tmp.shape[0]:
    #                         st.session_state.authorization_df = st.session_state.authorization_df[st.session_state.authorization_df['username'] != user_del_1]
    #                         st.session_state.authorization_df.reset_index(drop = True, inplace = True)
    #                         col[0].success(f"**{user_del_1} deleted as User**")
    #                     else:
    #                         col[0].error(f"**{user_del_1} not a User**")
    #                 st.session_state.authorization_df.to_csv('Authentication.csv', index = False)

            # with col[1].container():
            #     col[1].subheader("Add/Remove Admins", anchor= False)
            #     col[1].text_input("**Enter Username who is authorized**", key = 'admin_add_remove', on_change = submit_3, placeholder="Enter Username")
            #     add_remove_admin_radio = col[1].radio("Operation:", ('Add', 'Remove'), horizontal = True)
            #     proceed2 = col[1].button(label = "Continue", key = 'proceed2')
            #     if add_remove_admin_radio == 'Add':
            #         if st.session_state.admin_add_remove and proceed2:
            #             tmp = st.session_state.authorization_df[st.session_state.authorization_df['username'] == st.session_state.admin_add_remove]
            #             if tmp.shape[1] and tmp['admin'].item():
            #                 col[1].warning(f"**{st.session_state.admin_add_remove} is already an Admin**")
            #             elif tmp.shape[1] and tmp['admin'].item() == 0:
            #                 st.session_state.authorization_df.loc[st.session_state.authorization_df['username'] == st.session_state.admin_add_remove, 'admin'] = 1
            #                 col[1].success(f"**{st.session_state.admin_add_remove} promoted to Admin**")
            #             else:
            #                 col[1].error(f"**{st.session_state.admin_add_remove} not Authorized**")
            #         st.session_state.authorization_df.to_csv('Authentication.csv', index = False)
            #     else:
            #         if st.session_state.admin_add_remove and proceed2:
            #             tmp = st.session_state.authorization_df[st.session_state.authorization_df['username'] == st.session_state.admin_add_remove]
            #             if tmp.shape[1] and tmp['admin'].item() == 0:
            #                 col[1].warning(f"**{st.session_state.admin_add_remove} is not an Admin**")
            #             elif tmp.shape[1] and tmp['admin'].item():
            #                 st.session_state.authorization_df.loc[st.session_state.authorization_df['username'] == st.session_state.admin_add_remove, 'admin'] = 0
            #                 col[1].success(f"**{st.session_state.admin_add_remove} demoted to User**")
            #             else:
            #                 col[1].error(f"**{st.session_state.admin_add_remove} not Authorized**")
            #         st.session_state.authorization_df.to_csv('Authentication.csv', index = False)
