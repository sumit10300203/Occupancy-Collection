import pandas as pd
import streamlit_authenticator as stauth

names = ["Sumit Dhar", "Saptarshi Ghosh", "Abhik Mandal"]
usernames = ["sumit10300203@gmail.com", "g2saptarshi@gmail.com", "mandalabhik75@gmail.com"]
passwords = ["12000120073", "12000120068", "12000120096"]

hashed_passwords = stauth.Hasher(passwords).generate()

pd.DataFrame({'Name': names, 'username': usernames, 'key':hashed_passwords, 'admin': 0}).to_csv('Authentication.csv', index = False)