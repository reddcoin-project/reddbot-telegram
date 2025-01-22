#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author: Oliver Webb
"""

import config
import logging
import os
import subprocess
import json
import pyqrcode
from typing import Union
from datetime import datetime, timedelta
from PIL import Image
from decimal import *
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, Updater
from cached_data import TelegramUser


# Telegram user language codes
LANG_EN = 'en'
LANG_DE = 'de'
LANG_NL = 'nl'
LANG_KO = 'ko'

# Enable logging
logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO)
logger = logging.getLogger(config.app_name + "_" + config.app_version)


def remove_file(path: str):
    try:
        os.remove(path)
    except FileNotFoundError:
        logger.warning("Could not remove file: %s", path)


def format_number(number: Decimal, remove_trailing_zeros: bool = True, decimal_point: int = 8) -> str:
    if not is_numeric(number):
        number = 0
    formatting = "{0:,." + str(decimal_point) + "f}"
    formatted_number = formatting.format(number)
    if remove_trailing_zeros:
        formatted_number = formatted_number.rstrip("0").rstrip(".")
    return formatted_number


def is_numeric(number) -> bool:
    try:
        float(number)
        return True
    except ValueError:
        return False


def convert_decimal(number: Union[int, float, str, Decimal]) -> Decimal:
    getcontext().rounding = ROUND_DOWN
    number = Decimal(str(number))
    result = number.quantize(Decimal('.00000000'))
    return result


def valid_rdd_address(address: str) -> bool:
    if len(address) == 34 and address.startswith("R"):
        first_check = True
    else:
        first_check = False
    wallet_validation_result = reddcoin_wallet_cli_call(["validateaddress", address])["isvalid"]
    if first_check and wallet_validation_result:
        return True
    else:
        return False


def reddcoin_wallet_cli_call(command_list: list) -> Union[str, dict, list]:
    logger.info("reddcoin_wallet_cli_call - command_list: %s", command_list)
    result = ""
    if isinstance(command_list, list) and len(command_list) > 0:
        if "sendtoaddress" in command_list:
            tx_fee = subprocess.run([config.reddcoin_cli, "estimatesmartfee", "3"], stdout=subprocess.PIPE)
            tx_fee = tx_fee.stdout.strip().decode(config.encoding)
            subprocess.run([config.reddcoin_cli, "settxfee", tx_fee], stdout=subprocess.PIPE)
        if config.walletpassphrase is not None:
            subprocess.run([config.reddcoin_cli, "walletpassphrase", config.walletpassphrase, "1", "false"], stdout=subprocess.PIPE)
        if len(command_list) == 1:
            result = subprocess.run([config.reddcoin_cli, str(command_list[0])], stdout=subprocess.PIPE)
        if len(command_list) == 2:
            result = subprocess.run([config.reddcoin_cli, str(command_list[0]), str(command_list[1])], stdout=subprocess.PIPE)
        if len(command_list) == 3:
            result = subprocess.run([config.reddcoin_cli, str(command_list[0]), str(command_list[1]), str(command_list[2])], stdout=subprocess.PIPE)
        if len(command_list) == 4:
            result = subprocess.run([config.reddcoin_cli, str(command_list[0]), str(command_list[1]), str(command_list[2]), str(command_list[3])], stdout=subprocess.PIPE)
    if result != "":
        result = result.stdout.strip().decode(config.encoding)
    else:
        logger.warning("accounts_wallet_cli_call: Result empty, please check command list")
    if result.startswith("[") or result.startswith("{"):
        result = json.loads(result)
    return result


def send_user_not_allowed_text_msg(update: Update, context: CallbackContext):
    telegram_admin_user_list = ""
    for admin_user in config.admin_list:
        telegram_admin_user_list += " @" + admin_user
    admin_msg = "This function is restricted to following admins:{}".format(telegram_admin_user_list)
    send_text_msg(update, context, admin_msg)


def get_telegram_user_data(update: Update) -> TelegramUser:
    telegram_user = TelegramUser(id=get_user_id(update), username=get_username(update), first_name=get_first_name(update), last_name=get_last_name(update), chat_id=get_chat_id(update), chat_type=get_chat_type(update), msg_text=get_message_text(update), msg_date=update.message.date)
    if telegram_user.username is None:
        telegram_user.username = telegram_user.id
    return telegram_user


def get_user_id(update: Update) -> int:
    try:
        user_id = update.message.from_user.id
    except AttributeError:
        user_id = None
    logger.info("get_user_id: %s", user_id)
    return user_id


def get_username(update: Update) -> str:
    try:
        username = update.message.from_user.username
    except AttributeError:
        username = None
    if username == "null":
        username = None
    logger.info("get_username: %s", username)
    return username


def get_first_name(update: Update) -> str:
    try:
        first_name = update.message.from_user.first_name
        logger.info("get_first_name: %s", first_name)
    except AttributeError:
        first_name = None
    return first_name


def get_last_name(update: Update) -> str:
    try:
        last_name = update.message.from_user.last_name
        logger.info("get_last_name: %s", last_name)
    except AttributeError:
        last_name = None
    return last_name


def get_chat_id(update: Update) -> int:
    try:
        chat_id = update.message.chat_id
    except AttributeError:
        chat_id = None
    return chat_id


def get_chat_type(update: Update) -> Union[str, None]:
    try:
        msg_type = update.message.chat['type']
    except AttributeError:
        msg_type = None
    return msg_type


def get_message_text(update: Update) -> Union[str, None]:
    try:
        msg_text = update.message.text
    except AttributeError:
        msg_text = None
    return msg_text


def get_message_date(update: Update) -> Union[str, None]:
    try:
        msg_date = update.message.date
    except AttributeError:
        msg_date = datetime.utcnow().timestamp()
    return msg_date


def get_new_chat_members(update: Update) -> list:
    try:
        new_chat_members_list = update.message.new_chat_members
    except AttributeError:
        new_chat_members_list = []
    return new_chat_members_list


def get_user_input(update: Update, context: CallbackContext, telegram_user: TelegramUser) -> list:
    validated_user_input_list = []
    user_input_msg = ""
    if telegram_user.msg_text.find(" ") != -1:
        user_input = telegram_user.msg_text[telegram_user.msg_text.find(" "):].strip()
        user_input_list = user_input.split(" ")
        user_input_list = list(filter(None, user_input_list))
        for entry in user_input_list:
            if is_numeric(entry):
                if Decimal(entry) < 1:
                    user_input_msg = "Please use values that or 1 or greater."
                    validated_user_input_list = []
                    break
                num_of_decimal_places = abs(Decimal(str(entry)).as_tuple().exponent)
                if num_of_decimal_places > 8:
                    num_of_decimal_places_to_remove = num_of_decimal_places - 8
                    new_value = str(entry)[:-num_of_decimal_places_to_remove]
                    validated_user_input_list.append(new_value)
                else:
                    validated_user_input_list.append(entry)
            else:
                validated_user_input_list.append(entry)
    send_text_msg(update, context, user_input_msg)
    return validated_user_input_list


def get_recent_days(num_days: int) -> list:
    day_list = []
    today = datetime.today()
    for day_to_extract in range(num_days):
        day_list.append((today - timedelta(days=day_to_extract)).strftime("%Y-%m-%d"))
    return day_list


def send_text_msg(update: Union[Update, Updater], context: Union[CallbackContext, str], msg: Union[list, str]):
    if isinstance(msg, list):
        msg = "".join(msg)
    if msg != "":
        logger.info("send_text_msg: %s", msg)
        if isinstance(update, Update) and isinstance(context, CallbackContext):
            context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_to_message_id=resolve_reply_to_id(update))
        elif isinstance(update, Updater) and isinstance(context, str):
            update.bot.send_message(chat_id=context, text=msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            logger.error("Message was not send. Please check update and context parameters!")


def send_photo_msg(update: Update, context: CallbackContext, photo: str, caption: str):
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open(photo, "rb"), caption=caption, parse_mode=ParseMode.HTML, reply_to_message_id=resolve_reply_to_id(update))


def send_animation_msg(update: Update, context: CallbackContext, animation: str, caption: str):
    context.bot.sendAnimation(chat_id=update.message.chat_id, animation=open(animation, "rb"), caption=caption, parse_mode=ParseMode.HTML, reply_to_message_id=resolve_reply_to_id(update))


def resolve_reply_to_id(update: Update) -> Union[int, None]:
    if update.message.chat_id < 0:
        # We are in a group message, reply to the original message
        return update.message.message_id
    # We are in a private chat, don't reply
    return None


def fetch_deposit_address(user_id: Union[int, str]) -> str:
    logger.info("fetch_deposit_address - user_id: %s", user_id)
    user_account_address = reddcoin_wallet_cli_call(["getnewaddress", user_id])
    logger.info("fetch_deposit_address - user_accountaddress: %s", user_account_address)
    return user_account_address


def create_qr_code(user_account_address: str) -> str:
    # Generate the qr code and save as png
    qrcode_png = config.qrcode_home + user_account_address + ".png"
    qrobj = pyqrcode.QRCode(config.qrcode_prefix + user_account_address, error="H")
    qrobj.png(qrcode_png, scale=10, quiet_zone=1)
    # Now open that png image to put the logo
    qrcode = Image.open(qrcode_png).convert("RGB")
    bg_w, bg_h = qrcode.size
    # Open the logo image and put it into the qr code png
    logo = Image.open(config.qrcode_logo_img).convert("RGBA")
    fg_w, fg_h = logo.size
    # Set centered position for logo
    offset = ((bg_w - fg_w) // 2, (bg_h - fg_h) // 2)
    # put the logo in the qr code and save image
    qrcode.paste(logo, offset, logo)
    qrcode.save(qrcode_png)
    return qrcode_png


def get_posv_v2_multiplier() -> str:
    fileHandle = open("/home/staker/.reddcoin/debug.log", "r")
    lineList = fileHandle.readlines()
    fileHandle.close()
    posv_v2_multiplier = 0
    for x in range(60):
        line = lineList[-x]
        if "fInflationAdjustment" in line:
            posv_v2_multiplier_start = line.find("fInflationAdjustment") + 21
            posv_v2_multiplier = line[posv_v2_multiplier_start:posv_v2_multiplier_start + 7].strip()
            break
    return posv_v2_multiplier