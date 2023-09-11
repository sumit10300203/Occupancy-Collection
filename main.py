import streamlit as st
import streamlit_authenticator as stauth
from streamlit_extras.grid import grid
from streamlit_extras.no_default_selectbox import selectbox
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
    st.session_state['authorization_df'] = pd.read_csv("Authentication.csv")

credentials = {"usernames":{}}

for uname,name,pwd in zip(st.session_state.authorization_df['username'],st.session_state.authorization_df['Name'],st.session_state.authorization_df['key']):
    user_dict = {"name": name, "password": pwd}
    credentials["usernames"].update({uname: user_dict})

authenticator = stauth.Authenticate(credentials, "occupancy_collector_login", "login", cookie_expiry_days = 1)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("**🚨 Username/password is incorrect**")

if authentication_status is None:
    st.warning("**⚠️ Please enter your username and password**")

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

    my_grid = grid([15, 1], vertical_align="top")
    with my_grid.container():
        st.header(f":red[Welcome] {name}", anchor = False)
    with my_grid.container():
        authenticator.logout("Logout", "main")

    st.markdown('''
        **🡥 Redirect to 📋[Pandas DataFrame Viewer](https://pandas-dataframe-viewer-plotter.streamlit.app/) to visualize data with AI**
                ''')
    
    # tab1, tab2, tab3, tab4 = st.tabs(["👨‍👩‍👧‍👦 Occupancy Collection", "🔗 Merge Occupancy with Sensor data", "👀 View / Edit CSV file", "🔗 Concat multiple CSVs"])
    
    tab1, tab2, tab3 = st.tabs(["👨‍👩‍👧‍👦 Occupancy Collection", "🔗 Merge Occupancy with Sensor data", "📩 Send file using Mail"])

    if 'df' not in st.session_state:
        st.session_state['df'] = pd.DataFrame(columns = ['Time Entered', 'Last Modified', 'Occupancy', 'Position'])

    if 'view_edit_df' not in st.session_state:
        st.session_state['view_edit_df'] = pd.DataFrame()
    
    if 'occupancy' not in st.session_state:
        st.session_state['occupancy'] = ''

    if 'widget' not in st.session_state:
        st.session_state['widget'] = ''
    
    with tab1.container():
        my_grid = grid([3, 2], vertical_align="bottom")
        position = my_grid.text_input('**Enter current Position**', placeholder = 'Enter Position')
        my_grid.text_input('**Enter current Occupancy**', key='widget', placeholder = 'Enter Occupancy', on_change=submit)
        if st.session_state.occupancy and position:
            st.session_state.df.loc[st.session_state.df.shape[0]] = [datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"), datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"), st.session_state.occupancy, position.lower()]
            st.session_state.occupancy = ''
        edited_df = st.data_editor(st.session_state.df, num_rows="fixed", key = 'editeddf', on_change = update, hide_index = True, use_container_width = True, disabled=['Last Modified'])
        st.session_state.df = edited_df
        # col_inner = col[0].columns(2)
        # with col_inner[0].container():
        #     position = col_inner[0].text_input('**Enter current Position**', placeholder = 'Enter Position')
        # if position:
        #     with col_inner[0].container():
        #         col_inner[0].text_input('**Enter current Occupancy**', key='widget', placeholder = 'Enter Occupancy', on_change=submit_3)
        #     if st.session_state.occupancy and position:
        #         st.session_state.df.loc[st.session_state.df.shape[0]] = [datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"), datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"), st.session_state.occupancy, position.lower()]
        #         st.session_state.occupancy = ''
        # edited_df = col[0].data_editor(st.session_state.df, num_rows="fixed", key = 'editeddf', on_change = update, hide_index = True, use_container_width = True, disabled=['Last Modified'])
        # st.session_state.df = edited_df
    
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
                sensor_data = pd.read_csv(sensor_file, parse_dates=[['Date', 'Time']]).dropna(how='all', axis='columns')
                occupancy_data = pd.read_csv(occupancy_file, usecols = ['Time Entered', 'Occupancy', 'Position']).dropna(how='all', axis='columns')
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
                st.error('**Error in CSV files, please check the columns name are identical to the requirement and re upload again**', icon="🚨")
                disabled = True

        st.download_button(label = "**Download Merged CSV file**", data = convert_df(merged_df, index = False), file_name=f'Sensor_data_with_Occupancy_{datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d_%H:%M:%S")}.csv', mime='text/csv', disabled = disabled)
        st.caption('**:red[Note:] If timestamp range matches in both csv, then only it will be merged.**')

    with tab3.container():
        def local_css(file_name):
            with open(file_name) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        
        tab3_col = st.columns(2)
        with tab3_col[0]:
            if st.checkbox("**Send to other mail id**"):
                mail_id = st.text_input("**Enter mail id**", placeholder = "Enter the Mail ID", label_visibility = "collapsed")
            else:
                mail_id = selectbox("**Select the mail id from the below Authorised users**", options = st.session_state['authorization_df']['username'].to_list(), no_selection_label = None)
            if mail_id:
                contact_form = f"""
                    <form method="POST" action="https://formsubmit.co/{mail_id}" enctype="multipart/form-data">
                    <input type="hidden" name="_captcha" value="false">
                    <textarea name="message" placeholder="Any Comments"></textarea>
                    <input type="file" name="attachment" multiple = "multiple">
                    <button type="submit">Send</button>
                    </form>
                    """
                st.markdown(contact_form, unsafe_allow_html = True)
                local_css("style/style.css")

    # with tab3.container():
    #     def reset():
    #         st.session_state.view_edit_df = pd.DataFrame()
        
    #     view_csv_file = st.file_uploader("**Choose CSV file**", type = "csv", on_change = reset)
    #     if view_csv_file:
    #         if st.button("**Import / Re-Import CSV / Reset Filters, Slicers**"):
    #             st.session_state.view_edit_df = pd.read_csv(view_csv_file).dropna(how='all', axis='columns')
    #         tab3_3 = st.tabs(['**View**', '**Edit**'])
    #         with tab3_3[0].container():
    #             filtered_df = dataframe_explorer(st.session_state.view_edit_df, case=False).reset_index(drop = True)
    #             st.caption(f"**:red[Note:] Filters have no effect on slicers**")
    #             if st.button('Refresh Data'):
    #                 pass
    #             st.dataframe(filtered_df, use_container_width=True)
    #             st.caption(f"**:red[Current Row range -] [{0 if filtered_df.shape[0] else -1} : {filtered_df.shape[0] - 1}], :red[Current Column range -] [{0 if filtered_df.shape[1] else -1} : {filtered_df.shape[1] - 1}]**")
    #             store_col = {}
    #             for col in range(0, filtered_df.shape[1]):
    #                 store_col[filtered_df.columns[col]] = col
    #             st.json({"Column index info": store_col}, expanded = False)
    #             edited_file_name = st.columns(2)[0].text_input("**Enter edited csv file name**", key = 'tab3_3_0', placeholder = 'Enter file name')
    #             if edited_file_name:
    #                 st.download_button(label = "**Download Edited CSV file**", data = convert_df(filtered_df, index = False), file_name = f'{edited_file_name}.csv', mime='text/csv')
    #         with tab3_3[1].container():
    #             my_grid = grid([2, 2, 1.5, 1.5, 1], vertical_align="bottom")
    #             try:
    #                 option2 = my_grid.selectbox(label = "**Slicing Type**", options = ('Row Slicing', 'Column Slicing'), index = 0, label_visibility = 'visible')
    #                 option3 = my_grid.selectbox(label = "**Operation**", options = ('Keep', 'Remove'), label_visibility = 'visible')
    #                 slicing_input = st.columns(6)
    #                 start = my_grid.text_input("**Enter starting index**")
    #                 end = my_grid.text_input("**Enter ending index**")
    #                 proceed_3 = my_grid.button("**Continue**", use_container_width = 1)
    #                 if option2 == 'Row Slicing':
    #                     if start and end and proceed_3:
    #                         start = int(start)
    #                         end = int(end) + 1
    #                         if 0 <= start <= end <= st.session_state.view_edit_df.shape[0]:
    #                             if option3 == 'Keep':
    #                                 st.session_state.view_edit_df = st.session_state.view_edit_df.iloc[start: end].reset_index(drop = True)
    #                             else:
    #                                 st.session_state.view_edit_df = st.session_state.view_edit_df.drop(st.session_state.view_edit_df.iloc[start: end].index).reset_index(drop = True)
    #                         else:
    #                             if st.session_state.view_edit_df.shape[0] == 0:
    #                                 st.warning(f"**⚠️ Rows are empty**")
    #                             else:
    #                                 st.warning(f"**⚠️ Row's range slicing going out of bounds. Please select between [{0} : {st.session_state.view_edit_df.shape[0] - 1}]**")
    #                 else:
    #                     if start and end and proceed_3:
    #                         start = int(start)
    #                         end = int(end) + 1
    #                         if 0 <= start <= end <= st.session_state.view_edit_df.shape[1]:
    #                             if option3 == 'Keep':
    #                                 st.session_state.view_edit_df = st.session_state.view_edit_df[st.session_state.view_edit_df.columns[start: end]]
    #                             else:
    #                                 st.session_state.view_edit_df = st.session_state.view_edit_df.drop(st.session_state.view_edit_df.columns[start: end], axis = 1)
    #                         else:
    #                             if st.session_state.view_edit_df.shape[0] == 0:
    #                                 st.warning(f"**⚠️ Columns are empty**")
    #                             else:
    #                                 st.warning(f"**⚠️ Column's range slicing going out of bounds. Please select between [{0 if st.session_state.view_edit_df.shape[1] else -1} : {st.session_state.view_edit_df.shape[1] - 1}]**")                    
    #                 st.data_editor(st.session_state.view_edit_df, use_container_width = True, num_rows="fixed", hide_index = False, key=None, on_change=None)
    #             except Exception as e:
    #                 print(e)
    #                 st.error('**Error, please check the slicing values**', icon="🚨")
    #             st.caption("**:red[Note:] Make sure the slicing values are in range of the CSV file. Index Column cannot be removed**")
    #             st.caption(f"**:red[Current Row range -] [{0 if st.session_state.view_edit_df.shape[0] else -1} : {st.session_state.view_edit_df.shape[0] - 1}], :red[Current Column range -] [{0 if st.session_state.view_edit_df.shape[1] else -1} : {st.session_state.view_edit_df.shape[1] - 1}]**")
    #             store_col = {}
    #             for col in range(0, st.session_state.view_edit_df.shape[1]):
    #                 store_col[st.session_state.view_edit_df.columns[col]] = col
    #             st.json({"Column index info": store_col}, expanded = False)
    #             edited_file_name = st.columns(2)[0].text_input("**Enter edited csv file name**", key = 'tab3_3_1', placeholder = 'Enter file name')
    #             if edited_file_name:
    #                 st.download_button(label = "**Download Edited CSV file**", data = convert_df(st.session_state.view_edit_df, index = False), file_name = f'{edited_file_name}.csv', mime='text/csv')
    #     else:
    #         st.warning("**⚠️ Select a CSV**")

    # with tab4.container():
    #     concat_csvs = st.file_uploader("**Choose CSV files**", type = "csv", accept_multiple_files = True)
    #     st.caption('**:red[Note:] In the view above, lowest csv file data will be at top in merged csv file.**')
    #     if len(concat_csvs) < 2:
    #         st.warning("**⚠️ Select at least 2 CSV's. Make sure the CSV's have similar column name at similar positions, or null values will be inplaced**")
    #     else:
    #         for i in range(0, len(concat_csvs)):
    #             concat_csvs[i] = pd.read_csv(concat_csvs[i])
    #         merged_file_name = st.columns(2)[0].text_input("**Enter merged csv file name**", placeholder = 'Enter file name')
    #         if merged_file_name:
    #             st.download_button(label="**Download Merged CSV file**", data = convert_df(pd.concat(concat_csvs, ignore_index = True)), file_name=f'{merged_file_name}.csv', mime='text/csv')
        
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
