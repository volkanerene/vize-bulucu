import logging
import requests
import asyncio
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(filename='visa_checker.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

BOT_TOKEN = 'telegrambottoken'
CHAT_ID = 'telegramchatid'

# API URL
API_URL = 'https://api.schengenvisaappointments.com/api/visa-list/' 

# Previous message file
PREVIOUS_MESSAGE_FILE = 'previous_message.txt'

def fetch_visa_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status() 
        data = response.json()
        logging.info("Fetched data successfully")
        return data
    except requests.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return []

def filter_data(data):
    filtered_data = [
        item for item in data
        if item['source_country'] == 'Turkiye'
        and item['appointment_date']
        and item['mission_country'] in ['Austria', 'istedikleriniz']
        and item['visa_subcategory'] is not None 
        and any(keyword in item['visa_subcategory'].lower() for keyword in ['turizm', 'tourism', 'touristic', 'tourist', 'short term standard'])
    ]
    logging.info(f"Filtered data: {filtered_data}")
    return sorted(filtered_data, key=lambda x: x['mission_country'])

async def send_message(bot, message):
    try:
        logging.info(f"Sending message: {message}")
        await bot.send_message(chat_id=CHAT_ID, text=message)
        logging.info("Message sent successfully")
    except TelegramError as e:
        logging.error(f"Error sending message: {e}. Retrying in 10 seconds.")
        await asyncio.sleep(10)
        await send_message(bot, message) 

def read_previous_message():
    try:
        with open(PREVIOUS_MESSAGE_FILE, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return ''

def write_previous_message(message):
    with open(PREVIOUS_MESSAGE_FILE, 'w') as file:
        file.write(message)

async def main():
    bot = Bot(token=BOT_TOKEN)

    while True:
        data = fetch_visa_data()
        turkey_data = filter_data(data)

        if turkey_data:
            message = ''
            for item in turkey_data:
                message += f"{item['mission_country']}, Bu Tarihde: {item['appointment_date']} {item['center_name']} Turistik Randevu Açtı\n"

            previous_message = read_previous_message()

            logging.info(f"Previous message: {previous_message}")
            logging.info(f"Current message: {message}")

            if message != previous_message:
                await send_message(bot, message)
                write_previous_message(message)

        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main())
