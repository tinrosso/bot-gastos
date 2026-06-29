import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(r'C:\Users\Valentin\Desktop\bot_gastos\bot-gastos-500912-c63e2e205fc0.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key('1MA9JJrnpOpOBpVZ9q8tDOO0RpglbBLIgCU4oKRVUGqo')
print('Conectado OK')
print(sheet.sheet1.title)