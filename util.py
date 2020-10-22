#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 26.08.2019
@author: owebb
'''

from config import *
from json_io import *
from db_io import *
import os
import gc
import logging
import subprocess
import json
import requests
import pyqrcode
from datetime import datetime
from decimal import *
from PIL import Image
from string import Formatter
from telegram import ParseMode

LANG_EN = 'en'
LANG_DE = 'de'
LANG_NL = 'nl'
LANG_KO = 'ko'

OP_ADD = 'add'
OP_SUB = 'sub'
OP_MUL = 'mul'
OP_DIV = 'div'

## Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(name + "_" + version)

def tip_target_user(user_username, target_username, amount, tippings_json, reddpot_tip = False):
    user_balance = get_balance_from_user(user_username)
    target_user_balance = get_balance_from_user(target_username)
    user_balances_attribute_list = []
    if user_balance < amount:
        tip_msg = "Hey @{}, you have insufficient funds.".format(user_username)
    elif target_username == user_username:
        tip_msg = "You can't tip yourself silly."
    elif amount > 0.0:
        new_user_balance = get_decimal(OP_SUB, user_balance, amount)
        new_target_user_balance = get_decimal(OP_ADD, target_user_balance, amount)
        user_balances_attribute_list.append((new_user_balance, user_username))
        user_balances_attribute_list.append((new_target_user_balance, target_username))
        bulk_update_balance_from_user(user_balances_attribute_list)
        if reddpot_tip:
            tip_msg = "Hey @{}! Thanks for adding Ɍ<code>{}</code> to the Reddpot! Yep, that's not a typo 😉 There are currently <code>{}</code> Ɍeddcoins in the pot 🎉\nThe whole amount will be split up and tipped to a random list of active ɌeddHeads who have also added some ɌDD to the Ɍeddpot. Payout will be around Christmas and New Year's Eve 2019 🎆".format(user_username, amount, new_target_user_balance)
        else:
            tip_msg = "@{} tipped @{} of Ɍ<code>{}</code>".format(user_username, target_username, amount)
        ts_iso8601 = datetime.now().isoformat()
        if target_username not in tippings_json:
            tippings_json[target_username] = [{'tipfrom': user_username, 'date': ts_iso8601, 'amount': amount}]
        else:
            if len(tippings_json[target_username]) >= 10:
                del tippings_json[target_username][1]
            tippings_json[target_username].append({'tipfrom': user_username, 'date': ts_iso8601, 'amount': amount})
    else:
        tip_msg = "I see what you did there! 😏"
    return tip_msg

def addDonation(update, context, user_input_user_id, user_input_user_display_name, user_input_user_amount):
    logger.info("user_input_user_id: %s", user_input_user_id)
    logger.info("user_input_user_display_name: %s", user_input_user_display_name)
    logger.info("user_input_user_amount: %s", user_input_user_amount)
    # Get JSON data to store donation
    donors_list_json = read_donors_list()
    if user_input_user_id.startswith('@'):
        user_input_user_id = user_input_user_id[1:]
    if user_input_user_id not in donors_list_json:
        donors_list_json[user_input_user_id] = [{'name': user_input_user_display_name, 'amount': user_input_user_amount}]
        donation_msg = "Added a new donation of Ɍ<code>{}</code> from user @{} to hall of fame list 🎉".format(user_input_user_amount, user_input_user_id)
    else:
        donation_amount = donors_list_json[user_input_user_id][0]['amount']
        new_balance = get_decimal(OP_ADD, donation_amount, user_input_user_amount)
        donors_list_json[user_input_user_id][0]['name'] = user_input_user_display_name
        donors_list_json[user_input_user_id][0]['amount'] = new_balance
        donation_amount = format_number(donation_amount, True, 8)
        new_balance = format_number(new_balance, True, 8)
        donation_msg = "Donation from user @{} increased from Ɍ<code>{}</code> to Ɍ<code>{}</code> 🎉".format(user_input_user_id, donation_amount, new_balance)
    write_donors_list(donors_list_json)
    send_text_msg(update, context, donation_msg)

def fetch_deposit_address(update, context, user_username):
    logger.info("fetch_deposit_address - user_username: %s", user_username)
    user_accountaddress = accounts_wallet_cli_call(["getaccountaddress", user_username])
    logger.info("fetch_deposit_address - user_accountaddress: %s", user_accountaddress)
    qrcode_png = create_qr_code(user_accountaddress)
    logger.info("fetch_deposit_address - qrcode_png: %s", qrcode_png)
    deposit_msq = "Hey @{}, your depositing address is: {}".format(user_username, user_accountaddress)
    send_photo_msg(update, context, qrcode_png, deposit_msq) 

def is_not_on_exclude_list(user):
    user = user.lower()
    if "@" in user or "\n" in user or "ë" in user or "ê" in user or "ì" in user or user == "null" or user == "rjchrisjr" or user == "annako332":
        return False
    else:
        return True

def get_user_input(update, context, user_input_parameter_format_list, verify_input = True):
    user_username = get_username(update)
    user_first_name = update.message.from_user.first_name
    user_message_text = update.message.text
    user_input = ""
    user_input_list = []
    validated_user_input_list = []
    user_input_msg = ""

    logger.info("user_message_text: %s", user_message_text)

    # If username is not set respond with message
    if user_username is None and verify_input:
        user_input_msg = []
        user_input_msg.append("Hey {}, please set a Telegram username in your profile settings first.\n".format(user_first_name))
        user_input_msg.append("With your unique username you can access your <b>Telegram Ɍeddcoin wallet</b>.\n\n")
        user_input_msg.append("If you change your username you might loose access to your Ɍeddcoins! This wallet is separated from any other wallets and cannot be connected to other ones!")
    # If message from user contains one or more parameters proceed with verification
    elif user_message_text.find(" ") != -1:
        user_input = user_message_text[user_message_text.find(" "):].strip()
        user_input_list = user_input.split(" ")
        user_input_list = list(filter(None, user_input_list))
        logger.info("user_input_list: %s", user_input_list)
        logger.info("user_input_parameter_format_list: %s", user_input_parameter_format_list)
        
        pos = 0
        logger.info("user_input_list after split: %s", user_input_list)
        for entry in user_input_list:
            logger.info("for entry loop - entry: %s", entry)
            if is_number(entry):
                entry = float(entry)
                if entry <= tx_fee:
                    user_input_msg = "Hey @{}, please use values which are greater than {}".format(user_first_name, tx_fee)
                    user_input = ""
                    user_input_list = []
                    break
                else:
                    num_of_decimal_places = abs(Decimal(str(entry)).as_tuple().exponent)
                    logger.info("num_of_decimal_places: %s", num_of_decimal_places)
                    if num_of_decimal_places > 8:
                        num_of_decimal_places_to_remove = num_of_decimal_places - 8
                        new_value = str(entry)[:-num_of_decimal_places_to_remove]
                        validated_user_input_list.append(float(new_value))
                    else:
                        logger.info("num_of_decimal_places smaller than 8 - adding entry: %s", entry)
                        validated_user_input_list.append(entry)
            if len(user_input_list) <= len(user_input_parameter_format_list) and not isinstance(entry, user_input_parameter_format_list[pos]):
                logger.info("len(user_input_list): %s", len(user_input_list))
                logger.info("len(user_input_parameter_format_list): %s", len(user_input_parameter_format_list))
                logger.info("entry: %s", entry)
                logger.info("pos: %s", pos)
                logger.info("user_input_parameter_format_list[pos]: %s", user_input_parameter_format_list[pos])
                
                user_input_msg = "There is something missing or wrong! See /help for an example.".format(user_username)
                user_input = ""
                user_input_list = []
            elif not is_number(entry):
                validated_user_input_list.append(entry)

            pos += 1
    elif len(user_input_parameter_format_list) > 0 and verify_input:
        user_input_msg = "There is something missing or wrong! See /help for an example.".format(user_username)
    
    send_text_msg(update, context, user_input_msg)
    return validated_user_input_list

def get_market_data_info_from_coingecko():
    response = requests.get(market_data_origin)
    coingecko_api_response = response.json()
    response = requests.get(bittrex_api_btc_usd_price)
    bittrex_api_btc_usd_price_response = response.json()
    response = requests.get(bittrex_api_rdd_btc_price)
    bittrex_api_rdd_btc_price_response = response.json()
    response = requests.get(bittrex_api_rdd_btc_perc_change)
    bittrex_api_rdd_btc_perc_change_response = response.json()
    price_usd = bittrex_api_btc_usd_price_response['bidRate']
    price_btc = bittrex_api_rdd_btc_price_response['bidRate']
    price_usd = get_decimal(OP_MUL, price_btc, price_usd)
    price_change_percentage_24h = get_decimal(OP_MUL, bittrex_api_rdd_btc_perc_change_response['percentChange'])
    market_cap_btc = coingecko_api_response['market_data']['market_cap']['btc']
    market_cap_usd = coingecko_api_response['market_data']['market_cap']['usd']
    return[price_btc, price_usd, price_change_percentage_24h, market_cap_btc, market_cap_usd]

def send_user_not_allowed_text_msg(update, context):
    telegram_admin_user_list = ""
    for admin_user in admin_list:
        telegram_admin_user_list += " @" + admin_user
    admin_msg = "This function is restricted to following admins:{}".format(telegram_admin_user_list)
    send_text_msg(update, context, admin_msg)

def get_username(update):
    try:
        username = update.message.from_user.username
        logger.info("get_username input: %s", username)
    except AttributeError:
        username = None
    if username == "null":
        username = None
    logger.info("get_username output: %s", username)
    return username

def get_language_code(update):
    try:
        language_code = update.message.from_user.language_code
        if language_code[:2] == LANG_EN:
            language_code = LANG_EN
        if language_code[:2] == LANG_DE:
            language_code = LANG_DE
        if language_code[:2] == LANG_NL:
            language_code = LANG_NL
        if language_code[:2] == LANG_KO:
            language_code = LANG_KO
    except AttributeError:
        language_code = LANG_EN
    except TypeError:
        language_code = LANG_EN
    return language_code

def get_chat_id(update):
    try:
        chat_id = update.message.chat_id
    except AttributeError:
        chat_id = None
    return chat_id

def get_chat_type(update):
    try:
        msg_type = update.message.chat['type']
    except AttributeError:
        msg_type = None
    return msg_type

def get_message_text(update):
    try:
        msg_text = update.message.text
    except AttributeError:
        msg_text = None
    return msg_text

def get_new_chat_members(update):
    try:
        new_chat_members_list = update.message.new_chat_members
    except AttributeError:
        new_chat_members_list = []
    return new_chat_members_list

def send_text_msg(update, context, msg):
    if isinstance(msg, list):
        msg = "".join(msg)
    if msg != "":
        logger.info("send_text_msg: %s", msg)
        context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

def send_photo_msg(update, context, photo, caption):
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open(photo, "rb"), caption=caption, parse_mode=ParseMode.HTML)

def send_animation_msg(update, context, animation, caption):
    context.bot.sendAnimation(chat_id=update.message.chat_id, animation=open(animation, "rb"), caption=caption, parse_mode=ParseMode.HTML)

def get_files_from_dir(directory):
    (_, _, filenames) = next(os.walk("directory"))
    for file in filenames:
        os.path.getmtime(directory + "/" + file)

def valid_rdd_address(address):
    validation_result = accounts_wallet_cli_call(["validateaddress", address])
    validation_json = json.loads(validation_result)
    return validation_json["isvalid"]

def accounts_wallet_cli_call(command_list):
    logger.info("accounts_wallet_cli_call - command_list: %s", command_list)
    result = ""
    if isinstance(command_list, list) and len(command_list) > 0:
        logger.info("accounts_wallet_cli_call - start garbage collector")
        gc.collect()
        logger.info("accounts_wallet_cli_call - end of garbage collector")
        if walletpassphrase != "":
            subprocess.run([accounts_wallet, "walletpassphrase", walletpassphrase, "1" , "false"],stdout=subprocess.PIPE)
        if len(command_list) == 1:
            result = subprocess.run([accounts_wallet, command_list[0]], stdout=subprocess.PIPE)
        if len(command_list) == 2:
            result = subprocess.run([accounts_wallet, command_list[0], command_list[1]], stdout=subprocess.PIPE)
        if len(command_list) == 3:
            result = subprocess.run([accounts_wallet, command_list[0], command_list[1], command_list[2]], stdout=subprocess.PIPE)
        if len(command_list) == 4:
            result = subprocess.run([accounts_wallet, command_list[0], command_list[1], command_list[2], command_list[3]], stdout=subprocess.PIPE)            
    if result != "":
        result = result.stdout.strip().decode(encoding)
    else:
        logger.warning("accounts_wallet_cli_call: Result empty, please check command list")
    return result

def is_number(input):
    try:
        float(input)
        return True
    except ValueError:
        return False

def get_decimal(op = OP_MUL, fig1 = 1, fig2 = 1):
    fig1 = str(fig1)
    fig2 = str(fig2)
    getcontext().rounding = ROUND_DOWN
    if op == OP_ADD:
        result = Decimal(fig1) + Decimal(fig2)
    if op == OP_SUB:
        result = Decimal(fig1) - Decimal(fig2)
    if op == OP_MUL:
        result = Decimal(fig1) * Decimal(fig2)
    if op == OP_DIV:
        result = Decimal(fig1) / Decimal(fig2)
    result = result.quantize(Decimal(".00000000"))
    return float(result)

def format_number(fig, remove_trailing_zeros = True, decimal_point = 8):
    formatting = "{0:,." + str(decimal_point) + "f}"
    formatted_number = formatting.format(float(fig))
    if remove_trailing_zeros:
        formatted_number = formatted_number.rstrip("0").rstrip(".")
    return formatted_number

def create_qr_code(value):
    # Generate the qr code and save as png
    qrcode_png = value + ".png"
    qrobj = pyqrcode.QRCode(qrcode_prefix + value, error = "H")
    qrobj.png(qrcode_png, scale=10, quiet_zone=1)
    # Now open that png image to put the logo
    img = Image.open(qrcode_png)
    img = img.convert("RGBA")
    width, height = img.size
    # Open the logo image and  define how big the logo we want to put in the qr code png
    logo = Image.open(qrcode_logo_img)
    logo_size = 80
    # Calculate logo size and position
    xmin = ymin = int((width / 2) - (logo_size / 2))
    xmax = ymax = int((width / 2) + (logo_size / 2))
    logo = logo.resize((xmax - xmin, ymax - ymin))
    # put the logo in the qr code and save image
    img.paste(logo, (xmin, ymin, xmax, ymax))
    img.save(image_home + qrcode_png)
    return image_home + qrcode_png

def strfdelta(tdelta, fmt="{D:02}d {H:02}h {M:02}m {S:02}s", inputtype="timedelta"):
    """Convert a datetime.timedelta object or a regular number to a custom-
    formatted string, just like the stftime() method does for datetime.datetime
    objects.

    The fmt argument allows custom formatting to be specified.  Fields can 
    include seconds, minutes, hours, days, and weeks.  Each field is optional.

    Some examples:
        '{D:02}d {H:02}h {M:02}m {S:02}s' --> '05d 08h 04m 02s' (default)
        '{W}w {D}d {H}:{M:02}:{S:02}'     --> '4w 5d 8:04:02'
        '{D:2}d {H:2}:{M:02}:{S:02}'      --> ' 5d  8:04:02'
        '{H}h {S}s'                       --> '72h 800s'

    The inputtype argument allows tdelta to be a regular number instead of the  
    default, which is a datetime.timedelta object.  Valid inputtype strings: 
        's', 'seconds', 
        'm', 'minutes', 
        'h', 'hours', 
        'd', 'days', 
        'w', 'weeks'
    """

    # Convert tdelta to integer seconds.
    if inputtype == "timedelta":
        remainder = int(tdelta.total_seconds())
    elif inputtype in ["s", "seconds"]:
        remainder = int(tdelta)
    elif inputtype in ["m", "minutes"]:
        remainder = int(tdelta)*60
    elif inputtype in ["h", "hours"]:
        remainder = int(tdelta)*3600
    elif inputtype in ["d", "days"]:
        remainder = int(tdelta)*86400
    elif inputtype in ["w", "weeks"]:
        remainder = int(tdelta)*604800

    f = Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ("W", "D", "H", "M", "S")
    constants = {"W": 604800, "D": 86400, "H": 3600, "M": 60, "S": 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)
