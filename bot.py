import logging
import gspread
import os
import json
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import re

load_dotenv()

# Configuración desde variables de entorno
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
CREDENTIALS_FILE = r"C:\Users\Valentin\Desktop\bot_gastos\bot-gastos-500912-c63e2e205fc0.json"

# Categorías automáticas
CATEGORIAS = {
    "comida": ["almuerzo", "cena", "desayuno", "café", "restaurant", "pizza", "empanada", "super", "supermercado"],
    "transporte": ["nafta", "uber", "remis", "colectivo", "taxi", "peaje"],
    "salud": ["farmacia", "médico", "doctor", "medicamento"],
    "ocio": ["bar", "cine", "teatro", "cerveza", "trago"],
    "servicios": ["luz", "agua", "gas", "internet", "celular"],
}

def detectar_categoria(descripcion):
    descripcion_lower = descripcion.lower()
    for categoria, palabras in CATEGORIAS.items():
        for palabra in palabras:
            if palabra in descripcion_lower:
                return categoria.upper()
    return "OTROS"

def conectar_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola! Soy tu bot de gastos 💰\n\n"
        "Para registrar un gasto escribí:\n"
        "*Descripción monto*\n\n"
        "Ejemplo: _Almuerzo 850_\n\n"
        "Comandos:\n"
        "/resumen - Ver gastos del mes\n"
        "/total - Ver total gastado",
        parse_mode="Markdown"
    )

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sheet = conectar_sheets()
        registros = sheet.get_all_records()
        mes_actual = datetime.now().strftime("%m/%Y")

        gastos_mes = [r for r in registros if datetime.strptime(r["FECHA"], "%d/%m/%Y").strftime("%m/%Y") == mes_actual]

        if not gastos_mes:
            await update.message.reply_text("No hay gastos registrados este mes.")
            return

        resumen_cat = {}
        for gasto in gastos_mes:
            cat = gasto["CATEGORIA"]
            resumen_cat[cat] = resumen_cat.get(cat, 0) + float(gasto["MONTO"])

        mensaje = f"📊 *Resumen de {mes_actual}*\n\n"
        for cat, monto in sorted(resumen_cat.items(), key=lambda x: x[1], reverse=True):
            mensaje += f"• {cat}: ${monto:,.0f}\n"

        total = sum(resumen_cat.values())
        mensaje += f"\n💰 *Total: ${total:,.0f}*"

        await update.message.reply_text(mensaje, parse_mode="Markdown")
    except Exception as e:
        print(f"Error resumen: {type(e).__name__}: {e}")
        await update.message.reply_text("Error al obtener el resumen.")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sheet = conectar_sheets()
        registros = sheet.get_all_records()
        mes_actual = datetime.now().strftime("%m/%Y")

        gastos_mes = [r for r in registros if datetime.strptime(r["FECHA"], "%d/%m/%Y").strftime("%m/%Y") == mes_actual]
        total_mes = sum(float(r["MONTO"]) for r in gastos_mes)

        await update.message.reply_text(f"💰 Total gastado este mes: *${total_mes:,.0f}*", parse_mode="Markdown")
    except Exception as e:
        print(f"Error total: {type(e).__name__}: {e}")
        await update.message.reply_text("Error al obtener el total.")

async def registrar_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()

    match = re.search(r'^(.+?)\s+(\d+(?:[.,]\d+)?)$', texto)

    if not match:
        await update.message.reply_text(
            "No entendí el gasto 🤔\n"
            "Escribí así: *Descripción monto*\n"
            "Ejemplo: _Almuerzo 850_",
            parse_mode="Markdown"
        )
        return

    descripcion = match.group(1).strip()
    monto = float(match.group(2).replace(",", "."))
    fecha = datetime.now().strftime("%d/%m/%Y")
    categoria = detectar_categoria(descripcion)

    try:
        sheet = conectar_sheets()
        sheet.append_row([fecha, descripcion, monto, categoria])

        await update.message.reply_text(
            f"✅ Gasto registrado!\n\n"
            f"📅 {fecha}\n"
            f"📝 {descripcion}\n"
            f"💰 ${monto:,.0f}\n"
            f"🏷️ {categoria}"
        )
    except Exception as e:
        print(f"Error guardar: {type(e).__name__}: {e}")
        await update.message.reply_text("Error al guardar el gasto.")

logging.basicConfig(level=logging.INFO)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("resumen", resumen))
app.add_handler(CommandHandler("total", total))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_gasto))

print("Bot corriendo...")
app.run_polling()