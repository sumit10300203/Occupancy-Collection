import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Occupancy Collection",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

st.header(":red[Welcome] Sumit", anchor = False)
st.divider()

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns = ['Date', 'Time Entered', 'Last Modified', 'Occupancy'])

if 'occupancy' not in st.session_state:
    st.session_state.occupancy = ''

@st.cache_data
def convert_df(df):
    return df.to_csv().encode('utf-8')


def submit():
    st.session_state.occupancy = st.session_state.widget
    st.session_state.widget = ''

def update():
    # print(st.session_state.editeddf)
    tmp = st.session_state.editeddf['edited_rows']
    for i in tmp:
        for j in tmp[i]:
            edited_df.loc[i][j] = tmp[i][j]
        edited_df.loc[i]['Date'] = datetime.now().date()
        edited_df.loc[i]['Last Modified'] = datetime.now().time().strftime("%H:%M:%S")

    tmp = st.session_state.editeddf['deleted_rows']
    for i in tmp:
        edited_df.drop(i, axis = 0, inplace = True)
    edited_df.reset_index(inplace = True, drop = True)

col = st.columns(2)
with col[0].container():
    col[0].text_input('Enter current occupancy', key='widget', placeholder = '', on_change=submit)
    if st.session_state.occupancy:
        st.session_state.df.loc[st.session_state.df.shape[0]] = [datetime.now().date(), datetime.now().time().strftime("%H:%M:%S"), datetime.now().time().strftime("%H:%M:%S"), st.session_state.occupancy]
        st.session_state.occupancy = ''
    edited_df = col[0].data_editor(st.session_state.df, num_rows="dynamic", key = 'editeddf', on_change = update, hide_index = True, use_container_width = True, disabled=['Date', 'Last Modified'])
    st.session_state.df = edited_df

st.caption('**:red[Note:] Only Time Entered and Occupancy can be modified.**')

disabled = True
if st.session_state.df.shape[0]:
    disabled = False
st.download_button(label="Download data as CSV", data = convert_df(st.session_state.df), file_name=f'Occupancy_{datetime.now().date()}_{datetime.now().time().strftime("%H:%M:%S")}.csv', mime='text/csv', disabled = disabled)