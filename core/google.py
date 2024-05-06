import gspread
from oauth2client.service_account import ServiceAccountCredentials

from django.conf import settings


def get_sheet(name=None, key=None, sheet=None):
    if not sheet:
        raise ValueError("sheet is required")

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(settings.BASE_DIR / "easy-deutsch.json", scope)
    gc = gspread.authorize(credentials)

    if name:
        sheet = gc.open(name).worksheet(sheet)
    elif key:
        sheet = gc.open_by_key(key).worksheet(sheet)

    return sheet
