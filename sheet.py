import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime



def connect_to_sheets():
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    sheet = client.open("app_tracker").sheet1

    return sheet

def append_to_sheet(job_data_from_llm):
    sheet = connect_to_sheets()

    # now = datetime.now()
    # date = now.strftime("%d/%m/%Y")

    # for data in job_data_from_llm:
    dt = job_data_from_llm[0]
    user_input_from_from = job_data_from_llm[1]
    url = user_input_from_from[0]
    resume = user_input_from_from[1]
    summary = job_data_from_llm[2]
    row = [
        dt,
        url,
        summary,
        resume
    ]

    sheet.append_row(row)
    print(f"Logged: {summary[:25]}")

    #add later:
                # data["title"],
                            # data["company"],


