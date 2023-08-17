import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pytz import timezone

st.set_page_config(
    page_title="Occupancy Collection",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

st.header(":red[Welcome]", anchor = False)
st.divider()

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns = ['Time Entered', 'Last Modified', 'Occupancy'])

if 'occupancy' not in st.session_state:
    st.session_state.occupancy = ''

@st.cache_data
def convert_df(df):
    return df.to_csv(index = False).encode('utf-8')


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
