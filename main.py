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

def get_user_input() -> str:
    user_input = input("What exercise did you do? ")
    return user_input

def connect_to_nutrix(user_input):

    # headers = {
    #     "x-app-id": APP_ID,
    #     "x-app-key": API_KEY,
    #     "Content-Type": "application/json"
    # }

    # body = {
    #     "query": user_input
    # }

    # response = requests.post(
    #     "https://trackapi.nutritionix.com/v2/natural/exercise",
    #     json=body,
    #     headers=headers
    # )

    # data = response.json()

    ########
    # can't connect now
    ########
    data = {
        "exercises": [
            {
            "tag_id": 317,
            "user_input": "I ran 30 minutes",
            "duration_min": 30,
            "met": 9.8,
            "intensity": "medium",
            "name": "running",
            "nf_calories": 290.5,
            "compendium_code": 12020,
            "description": "running",
            "benefits": "..."
            }
        ]
        }

    return data

def append_to_sheet(user_input, sheet):
    data = connect_to_nutrix(user_input)

    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")


    for exercise in data["exercises"]:
        row = [
            date,
            time,
            exercise["name"].title(),
            exercise["duration_min"],
            exercise["nf_calories"]
        ]

    sheet.append_row(row)
    print(f"Logged: {exercise['name']} - {exercise['duration_min']} min")


def main():
    sheet = connect_to_sheets()
    user_input = get_user_input()
    append_to_sheet(user_input, sheet)


if __name__ == "__main__":
    main()
