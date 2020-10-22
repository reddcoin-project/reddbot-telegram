#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 07.05.2019
@author: owebb
'''

from config import *
from util import *
from json_io import *
from db_io import *
from scheduled_tasks import *
import time
import random
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import ParseMode
from telegram.bot import Bot
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

def main():
    ## Connect to database
    connect_to_db()
    
    ## Main Scheduler setup for running tasks
    scheduler = BackgroundScheduler()
    if scheduler_active:
        scheduler.add_job(check_incoming_transactions, 'interval', seconds=30)
#        scheduler.add_job(check_stake_transactions, 'cron', day_of_week='mon-sun', hour=11, minute=52)
    scheduler.start()
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

    ## Telegram bot dispatcher and handlers
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=bot_token, use_context=True)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Add command handlers
    start_handler = CommandHandler("start", commands)
    dispatcher.add_handler(start_handler)

    transform_users_activity_list_handler = CommandHandler("transform_users_activity_list", transform_users_activity_list)
    dispatcher.add_handler(transform_users_activity_list_handler)
    
    #export_user_balances_to_db_handler = CommandHandler("export_user_balances_to_db", export_user_balances_to_db)
    #dispatcher.add_handler(export_user_balances_to_db_handler)

    xfer_handler = CommandHandler("xfer", xfer)
    dispatcher.add_handler(xfer_handler)

    broadcast_stake_handler = CommandHandler("broadcast_stake", broadcast_stake)
    dispatcher.add_handler(broadcast_stake_handler)

    get_stake_tx_from_addresses_handler = CommandHandler("get_stake_tx_from_addresses", get_stake_tx_from_addresses)
    dispatcher.add_handler(get_stake_tx_from_addresses_handler)

    commands_handler = CommandHandler("commands", commands)
    dispatcher.add_handler(commands_handler)

    moon_handler = CommandHandler("moon", moon)
    dispatcher.add_handler(moon_handler)

    statistics_handler = CommandHandler("statistics", statistics)
    dispatcher.add_handler(statistics_handler)

    posv_handler = CommandHandler("posv", posv)
    dispatcher.add_handler(posv_handler)

    hi_handler = CommandHandler("hi", hi)
    dispatcher.add_handler(hi_handler)

    donate_handler = CommandHandler("donate", donate)
    dispatcher.add_handler(donate_handler)

    withdraw_handler = CommandHandler("withdraw", withdraw)
    dispatcher.add_handler(withdraw_handler)

    marketcap_handler = CommandHandler("marketcap", marketcap)
    dispatcher.add_handler(marketcap_handler)

    deposit_handler = CommandHandler("deposit", deposit)
    dispatcher.add_handler(deposit_handler)

    price_handler = CommandHandler("price", price)
    dispatcher.add_handler(price_handler)

    tip_handler = CommandHandler("tip", tip)
    dispatcher.add_handler(tip_handler)

    rain_handler = CommandHandler("rain", rain)
    dispatcher.add_handler(rain_handler)

    rainbow_handler = CommandHandler("rainbow", rainbow)
    dispatcher.add_handler(rainbow_handler)

    snow_handler = CommandHandler("snow", snow)
    dispatcher.add_handler(snow_handler)

    sun_handler = CommandHandler("sun", sun)
    dispatcher.add_handler(sun_handler)

    sunshine_handler = CommandHandler("sunshine", sunshine)
    dispatcher.add_handler(sunshine_handler)

    reddpot_cashout_handler = CommandHandler("reddpot_cashout", reddpot_cashout)
    dispatcher.add_handler(reddpot_cashout_handler)

    mytips_handler = CommandHandler("mytips", mytips)
    dispatcher.add_handler(mytips_handler)

    mystakes_handler = CommandHandler("mystakes", mystakes)
    dispatcher.add_handler(mystakes_handler)

    balance_handler = CommandHandler("balance", balance)
    dispatcher.add_handler(balance_handler)

    help_handler = CommandHandler("help", help)
    dispatcher.add_handler(help_handler)

    about_handler = CommandHandler("about", about)
    dispatcher.add_handler(about_handler)
    
    changelog_handler = CommandHandler("changelog", changelog)
    dispatcher.add_handler(changelog_handler)
    
    newwebsite_handler = CommandHandler("newwebsite", newwebsite)
    dispatcher.add_handler(newwebsite_handler)
    
    newwallet_handler = CommandHandler("newwallet", newwallet)
    dispatcher.add_handler(newwallet_handler)

    newDonation_handler = CommandHandler("newDonation", newDonation)
    dispatcher.add_handler(newDonation_handler)

    removeDonor_handler = CommandHandler("removeDonor", removeDonor)
    dispatcher.add_handler(removeDonor_handler)

    hallOfFame_handler = CommandHandler("hallOfFame", hallOfFame)
    dispatcher.add_handler(hallOfFame_handler)

    #check_deposit_transactions_handler = CommandHandler("check_deposit_transactions", check_deposit_transactions)
    #dispatcher.add_handler(check_deposit_transactions_handler)

    #check_stake_transactions_handler = CommandHandler("check_stake_transactions", check_stake_transactions)
    #dispatcher.add_handler(check_stake_transactions_handler)
    
    text_msg_handler = MessageHandler(filters=Filters.all, callback=incoming_msg)
    dispatcher.add_handler(text_msg_handler)

    # Add error handler.
    dispatcher.add_error_handler(error)

    # Start the Bot.
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    # This is here to simulate application activity (which keeps the main thread alive).
#    try:
#        while scheduler_active:
#            time.sleep(1)
#    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
#        scheduler.shutdown()

def error(update, context):
    try:
        raise context.error
    except Unauthorized:
        logger.error('Unauthorized error: %s', update)
    except BadRequest:
        logger.error('BadRequest: %s', update)
    except TimedOut:
        logger.error('TimedOut: %s', update)
    except NetworkError:
        logger.error('NetworkError: %s', update)
    except ChatMigrated as e:
        logger.error('ChatMigrated: %s', e)
    except TelegramError:
        logger.error('TelegramError: %s', update)

#def error(update, context):
#    """Log Errors caused by Updates."""
#    logger.error('Update "%s" caused error "%s"', update, error)

##############################################################################################
### Telegram Reddbot functions and commands                                               ####
##############################################################################################

## Called by scheduler for checking incoming receive transactions from accounts wallet
def check_incoming_transactions():
    check_deposit_tx()

## Called by scheduler for checking new stake transactions from from stake wallet
def check_stake_transactions():
    # Telegram bot for broadcasting messages to all Reddcoin Channels
    # Init bot by using bot token
    bot = Bot(bot_token)
    check_stake_tx(bot)

def transform_users_activity_list(update, context):
    donors_list_json = read_donors_list()
    donors_list_json_transformed = {}
    for donor_username, donation_amount in donors_list_json.items():
        #logger.info("donor_username: %s", donor_username)
        #logger.info("donation_amount: %s", donation_amount)
        donor_user_username = donor_username.split(" ")[0]
        #logger.info("donor_user_username: %s", donor_user_username)
        donor_user_first_name = donor_username.replace(donor_user_username, "")[1:]
        #logger.info("donor_user_first_name: %s", donor_user_first_name)
        donors_list_json_transformed[donor_user_username[1:]] = [{'name': donor_user_first_name, 'amount': donation_amount}]
    #logger.info("donors_list_json_transformed: %s", donors_list_json_transformed)
    logger.info("transform_users_activity_list transformed: %s", len(donors_list_json_transformed))
    write_donors_list(donors_list_json_transformed)

## Called for all incoming messages except for /<command>
## Function: called by itself
def incoming_msg(update, context):
    user_username = get_username(update)
    user_language_code = get_language_code(update)
    chat_id = get_chat_id(update)
    msg_type = get_chat_type(update)
    msg_text = get_message_text(update)
    new_chat_members_list = get_new_chat_members(update)
    msg_date = int(datetime.utcnow().timestamp())
    users_activity_json = read_users_activity_list()

    logger.info("incoming_msg - user_username: %s", user_username)
    logger.info("incoming_msg - user_language_code: %s", user_language_code)
    logger.info("incoming_msg - chat_id: %s", chat_id)
    logger.info("incoming_msg - msg_type: %s", msg_type)
    logger.info("incoming_msg - message.text: %s", msg_text)
    logger.info("incoming_msg - message: %s", update.message)
    for user in new_chat_members_list:
        logger.info("incoming_msg - new_chat_members.username: %s", user.username)

    if user_username is not None and (msg_type == "group" or msg_type == "supergroup"):
        if user_username not in users_activity_json:
            add_new_user(user_username)
            users_activity_json[user_username] = [{'group_id': chat_id, 'date': msg_date}]
        else:
            found_existing_entry = False
            for users_group_activity in users_activity_json[user_username]:
                if users_group_activity['group_id'] == chat_id:
                    users_group_activity['date'] = msg_date
                    found_existing_entry = True
            if found_existing_entry == False:
                users_activity_json[user_username].append({'group_id': chat_id, 'date': msg_date})
    write_users_activity_list(users_activity_json)

## Respond to user with basic information how to use Reddbot commands
## Command: /help
def help(update, context):
    user_username = get_username(update)
    user_first_name = update.message.from_user.first_name
    if user_username is None:
        user_username = " " + user_first_name
    else:
        user_username = " @" + user_username
    help_msg = []
    help_msg.append("Hello{} 👋 Initiating commands /tip & /withdraw have a specific format. Use them like so:\n\n".format(user_username))
    help_msg.append("<b>Parameters:</b>\n")
    help_msg.append("<code>username</code> = target user to tip (starting with @)\n")
    help_msg.append("<code>amount</code> = amount of Ɍeddcoin to utilize\n")
    help_msg.append("<code>address</code> = Ɍeddcoin address to withdraw to\n\n")
    help_msg.append("<b>Tipping format:</b>\n")
    help_msg.append("<code>/tip @username amount</code>\n\n")
    help_msg.append("<b>Withdrawing format:</b>\n")
    help_msg.append("<code>/withdraw address amount</code>\n\n")
    help_msg.append("Need more help? -> View all /commands")
    send_text_msg(update, context, help_msg)

## Respond to user with all Reddbot commands and how to use them specifically
## Command: /commands
def commands(update, context):
    commands_msg = []
    commands_msg.append("<b>The following commands are at your disposal:</b>\n")
    commands_msg.append("/hi /commands /deposit /tip /rain /donate /hallOfFame /withdraw /balance /mytips /mystakes /price /marketcap /statistics /moon /about /changelog\n\n")
    commands_msg.append("<b>Examples:</b>\n")
    commands_msg.append("<code>/tip @TechAdept 100</code>\n")
    commands_msg.append("<code>/tip @CryptoGnasher 100</code>\n")
    commands_msg.append("➡️ send a tip of 100 Ɍeddcoins to our project lead Jay 'TechAdept' Laurence or to our lead dev John Nash\n")
    commands_msg.append("<code>/donate 100</code>\n")
    commands_msg.append("➡️ support Ɍeddcoin charity initiatives by donating 100 Ɍeddcoins\n")
    commands_msg.append("<code>/rain 100 24</code>\n")
    commands_msg.append("➡️ tip some ɌeddHeads with Telegram activity in the last 24 hours (amount divided by total active numbers in given timeframe)\n")
    commands_msg.append("<code>/withdraw {} 100</code>\n".format(dev_fund_address))
    commands_msg.append("➡️ send 100 Ɍeddcoins to a specific address (in this example: Charity initiatives address which is also used for /donate)\n")
    commands_msg.append("<code>/mytips</code>\n")
    commands_msg.append("➡️ Get a list of all recent sent and received tips\n")
    commands_msg.append("<code>/mystakes</code>\n")
    commands_msg.append("➡️ Get a list of all recent received stakes\n")
    send_text_msg(update, context, commands_msg)

## Respond to user with basic information about Reddbot
## Command: /about
def about(update, context):
    about_msg = []
    about_msg.append("{} was originally coded by @xGozzy (Ex-Developer) and was further developed by @cryptoBUZE.\n".format(bot_name))
    about_msg.append("The source code can be viewed at https://github.com/cryptoBUZE/reddbot-telegram.\n")
    about_msg.append("If you have any enquiries please contact @TechAdept or @cryptoBUZE\n")
    send_text_msg(update, context, about_msg)

## Respond to user with recent and older changes
## Command: /changelog
def changelog(update, context):
    changelog_msg = []
    changelog_msg.append("<b>Changelog for {} {}:</b>\n".format(name, version))
    changelog_msg.append("✔️ Smaller fixed and improvements\n")
    changelog_msg.append("<b>Older changes:</b>\n")
    changelog_msg.append("✔️ New command <code>/tip randomHead 100 8</code> -> Tipping a random ReddHead with recent group activity of 8 hours (default: last {} hours).\n".format(tip_randomhead_brokehead_default_activity_hours))
    changelog_msg.append("✔️ New command <code>/tip brokeHead 100 8</code> -> Tipping a random ReddHead with balance below {} Ɍeddcoin and recent group activity (last {} hours).\n".format(tip_brokehead_balance_threshold, tip_randomhead_brokehead_default_activity_hours))
    changelog_msg.append("✔️ Staking -> All ReddHeads who have more than 0 Ɍeddcoins in their Telegram Tip bot wallet will automatically get stake rewards!\n")
    changelog_msg.append("✔️ Tx fee for withdrawals -> Small transaction fee of Ɍ<code>{}</code> is added to ensure that everyones balances will always reflect 100% correct amount of stored Ɍeddcoins\n".format(tx_fee))
    changelog_msg.append("✔️ New command <code>/mystakes</code> -> Get a list of all recent stakes\n")
    changelog_msg.append("✔️ New command <code>/mytips</code> -> Get a list of all recent tips\n")
    changelog_msg.append("✔️ New command <code>/rain 100 8</code> -> Tip all ɌeddHeads with recent group activity of 8 hours (default: last {} hours).\n".format(rain_default_activity_hours))
    send_text_msg(update, context, changelog_msg)

## Respond to user with a simple hi message
## Command: /hi
def hi(update, context):
    user_username = get_username(update)
    user_first_name = update.message.from_user.first_name
    if user_username is None:
        user_username = " " + user_first_name
    else:
        user_username = " @" + user_username
    hi_msg = "Hello{}, how are you doing today?".format(user_username)
    send_text_msg(update, context, hi_msg)

## Respond to user with current price information
## Command: /price
def price(update, context):
    price_info = get_market_data_info_from_coingecko()
    price_btc = price_info[0]
    price_usd = price_info[1]
    price_change_percentage_24h = price_info[2]
    if price_change_percentage_24h < 0:
        change_symbol = "-"
        price_change_percentage_24h = -price_change_percentage_24h
    elif price_change_percentage_24h > 0:
        change_symbol = "+"
    else:
        change_symbol = ""
    price_change_percentage_24h = format_number(price_change_percentage_24h, False, 2) + "%"
    if change_symbol != "":
        price_msg = "1 Ɍeddcoin is valued at $<code>{}</code> Δ {}<code>{}</code> ≈ ₿<code>{}</code>".format(price_usd,change_symbol,price_change_percentage_24h,price_btc)
    else:
        price_msg = "1 Ɍeddcoin is valued at $<code>{}</code> ≈ ₿<code>{}</code>".format(price_usd,price_btc)
    send_text_msg(update, context, price_msg)

## Respond to user with current market capitalization information
## Command: /marketcap
def marketcap(update, context):
    price_info = get_market_data_info_from_coingecko()
    marketcap_btc = price_info[3]
    marketcap_usd = format_number(price_info[4], False, 0)
    marketcap_msg = "The current market cap of Ɍeddcoin is valued at $<code>{}</code> ≈ ₿<code>{}</code>".format(marketcap_usd, marketcap_btc)
    send_text_msg(update, context, marketcap_msg)

## Respond to user with a deposit address and qr code bound to his unique Telegram username
## Command: /deposit
def deposit(update, context):
    user_username = get_username(update)
    user_input_parameter_format_list = []
    get_user_input(update, context, user_input_parameter_format_list)

    if user_username is not None:
        fetch_deposit_address(update, context, user_username)

## Respond to user with current balance from his unique Telegram username
## Command: /balance
def balance(update, context):
    user_username = get_username(update)
    user_input_parameter_format_list = []
    get_user_input(update, context, user_input_parameter_format_list)
    price_info = get_market_data_info_from_coingecko()
    price_usd = float(price_info[1])

    if user_username is not None:
        user_balance = get_balance_from_user(user_username)
        if user_balance is not None:
            fiat_balance = get_decimal(OP_MUL, user_balance, price_usd)
            fiat_balance = format_number(fiat_balance, False, 4)
            user_balance = format_number(user_balance, False, 8)
            balance_msg = "@{} your current balance is: Ɍ<code>{}</code> ≈ $<code>{}</code>".format(user_username, user_balance, fiat_balance)
            send_text_msg(update, context, balance_msg)

## Send a tip to another Telegram user
## Command: /tip @<username> <amount>
## Command: /tip randomHead <amount> <hours of last activity>
## Command: /tip brokeHead <amount> <hours of last activity>
def tip(update, context, send_tip_msg = True):
    user_username = get_username(update)
    group_chat_id = update.message.chat_id
    user_input_parameter_format_list = [str, float, float]
    user_input_list = get_user_input(update, context, user_input_parameter_format_list)
    tippings_json = read_users_tips_list()
    users_activity_json = read_users_activity_list()
    last_active_users_list = []
    tip_msg = ""
    
    logger.info("tip - user_input_list: %s", user_input_list)
    
    if len(user_input_list) > 1 and is_not_on_exclude_list(user_username):
        target = user_input_list[0]
        amount = float(user_input_list[1])
        if len(user_input_list) == 3:
            tip_randomhead_brokehead_activity_hours = float(user_input_list[2])
        else:
            tip_randomhead_brokehead_activity_hours = tip_randomhead_brokehead_default_activity_hours
        if target == bot_name:
            tip_msg = "HODL."
            #tip_msg = tip_target_user(user_username, target[1:], amount, tippings_json, True)
        elif target.startswith("@"):
            tip_msg = tip_target_user(user_username, target[1:], amount, tippings_json)
        elif target.lower() == "randomhead" or target.lower() == "brokehead":
            for active_user_username in users_activity_json:
                for users_activity_entry_json in users_activity_json[active_user_username]:
                    group_id = users_activity_entry_json['group_id']
                    date = users_activity_entry_json['date']
                    if group_id == group_chat_id:
                        current_ts = int(datetime.utcnow().timestamp())
                        diff = current_ts - date
                        hours = diff / 60 / 60 
                        if hours <= tip_randomhead_brokehead_activity_hours and user_username != active_user_username:
                            last_active_users_list.append(active_user_username)
            
            logger.info("tip - last_active_users_list: %s", last_active_users_list)
            
            if target.lower() == "randomhead":
                if len(last_active_users_list) > 1:
                    active_user_username = random.choice(last_active_users_list)
                    tip_msg = tip_target_user(user_username, active_user_username, amount, tippings_json)
                else:
                    tip_msg = "Sorry @{}, but there are no randomHeads with recent activity since {} hours.".format(user_username, format_number(tip_randomhead_brokehead_activity_hours))
            if target.lower() == "brokehead":
                for active_user_username in last_active_users_list:
                    active_user_balance = get_balance_from_user(active_user_username)
                    if active_user_balance is not None:
                        if active_user_balance < tip_brokehead_balance_threshold:
                            tip_msg = tip_target_user(user_username, active_user_username, amount, tippings_json)
                            break
                    else:
                        tip_msg = tip_target_user(user_username, active_user_username, amount, tippings_json)
                        break
                if tip_msg == "":
                    tip_msg = "Sorry @{}, but there are no brokeHeads with recent activity since {} hours.".format(user_username, format_number(tip_randomhead_brokehead_activity_hours))
        else:
            tip_msg = "Error that user is not applicable. Need help? -> /help"
        if send_tip_msg:
            send_text_msg(update, context, tip_msg)

    write_users_tips_list(tippings_json)

def rain(update, context):
    type_of_weather = "rain"
    weather_tipping(update, context, type_of_weather)

def rainbow(update, context):
    type_of_weather = "rainbow"
    weather_tipping(update, context, type_of_weather)

def snow(update, context):
    type_of_weather = "snow"
    weather_tipping(update, context, type_of_weather)

def sun(update, context):
    type_of_weather = "sun"
    weather_tipping(update, context, type_of_weather)

def sunshine(update, context):
    type_of_weather = "sun"
    weather_tipping(update, context, type_of_weather)

## Send a tip to other active Telegram users which is split equality
## Command: /rain <amount> <hours of last activity>
def weather_tipping(update, context, type_of_weather):
    user_username = get_username(update)
    group_chat_id = update.message.chat_id
    user_input_parameter_format_list = [float, float]
    user_input_list = get_user_input(update, context, user_input_parameter_format_list)
    tippings_json = read_users_tips_list()
    users_activity_json = read_users_activity_list()
    last_active_users_list = []
    rain_msg = ""

    if len(user_input_list) > 0 and is_not_on_exclude_list(user_username):
        if len(user_input_list) == 1:
            amount = float(user_input_list[0])
            activity = rain_default_activity_hours
        else:
            amount = float(user_input_list[0])
            activity = float(user_input_list[1])

        user_balance = get_balance_from_user(user_username)
        if user_balance < amount:
            rain_msg = "@{} you have insufficient funds.".format(user_username)
        else:
            for active_user_username in users_activity_json:
                for users_activity_entry_json in users_activity_json[active_user_username]:
                    group_id = users_activity_entry_json['group_id']
                    date = users_activity_entry_json['date']
                    if group_id == group_chat_id:
                        current_ts = int(datetime.utcnow().timestamp())
                        diff = current_ts - date
                        hours = diff / 60 / 60
                        if hours <= activity and user_username != active_user_username:
                            last_active_users_list.append(active_user_username)

        if len(last_active_users_list) > 0:
            amount_per_reddhead = get_decimal(OP_DIV, amount, len(last_active_users_list))
            rain_tipping_list = []
            rain_msg = "@{} has tipped the following ɌeddHeads of Ɍ<code>{}</code>:\n".format(user_username, amount_per_reddhead)

            if type_of_weather == "rain":
                rain_tipping_list.append("💸 -> ")
            elif type_of_weather == "rainbow":
                rain_tipping_list.append("🌈 -> ")
            elif type_of_weather == "snow":
                rain_tipping_list.append("❄️ -> ")
            elif type_of_weather == "sun":
                rain_tipping_list.append("🌞 -> ")
            last_active_users_list_counter = 0
            user_balances_attribute_list = []

            last_active_users_list = sorted(last_active_users_list, key=str.casefold)
            for active_user_username in last_active_users_list:
                active_user_balance = get_balance_from_user(active_user_username)
                last_active_users_list_counter += 1
                active_user_new_balance = get_decimal(OP_ADD, active_user_balance, amount_per_reddhead)
                user_balances_attribute_list.append((active_user_new_balance, active_user_username))

                ts_iso8601 = datetime.utcnow().isoformat()
                if active_user_username not in tippings_json:
                    tippings_json[active_user_username] = [{'tipfrom': user_username, 'date': ts_iso8601, 'amount': amount_per_reddhead}]
                else:
                    if len(tippings_json[active_user_username]) >= 10:
                        del tippings_json[active_user_username][1]
                    tippings_json[active_user_username].append({'tipfrom': user_username, 'date': ts_iso8601, 'amount': amount_per_reddhead})

                if last_active_users_list_counter < 150:
                    rain_tipping_list.append("@{} ".format(active_user_username))
                elif last_active_users_list_counter == 150:
                    rain_tipping_list.append("... and some more ...")

            for entry in rain_tipping_list:
                rain_msg += entry
            ## update user balances in database
            user_new_balance = get_decimal(OP_SUB, user_balance, amount)
            user_balances_attribute_list.append((user_new_balance, user_username))
            bulk_update_balance_from_user(user_balances_attribute_list)
        elif len(rain_msg) == 0:
            rain_msg = "Sorry, no active users to tip for with last activity within {} hours.".format(str(activity))

        write_users_tips_list(tippings_json)
        send_text_msg(update, context, rain_msg)

def reddpot_cashout(update, context):
    bot = Bot(bot_token)
    user_username = get_username(update)
    user_input_parameter_format_list = []
    user_input_list = get_user_input(update, context, user_input_parameter_format_list)
    tippings_json = read_users_tips_list()
    if user_username in admin_list and len(user_input_list) > 0:
        reddpot_balance = get_balance_from_user(bot_name[1:])
        amount_per_reddhead = get_decimal(OP_DIV, reddpot_balance, len(user_input_list))
        reddpot_tipping_list = []
        reddpot_msg = "Congratulations to the following ReddPot winners - <code>{}</code> Reddcoins for each of you:\n".format(format_number(amount_per_reddhead, True, 8))
        reddpot_tipping_list.append("🎆 -> ")
        user_balances_attribute_list = []
        for reddpot_winner_user_username in user_input_list:
            reddpot_winner_user_balance = get_balance_from_user(reddpot_winner_user_username)
            reddpot_winner_new_balance = get_decimal(OP_ADD, reddpot_winner_user_balance, amount_per_reddhead)
            user_balances_attribute_list.append((reddpot_winner_new_balance, reddpot_winner_user_username))
            
            ts_iso8601 = datetime.utcnow().isoformat()
            if reddpot_winner_user_username not in tippings_json:
                tippings_json[reddpot_winner_user_username] = [{'tipfrom': bot_name[1:], 'date': ts_iso8601, 'amount': amount_per_reddhead}]
            else:
                tippings_json[reddpot_winner_user_username].append({'tipfrom': bot_name[1:], 'date': ts_iso8601, 'amount': amount_per_reddhead})
            
            reddpot_tipping_list.append("@{} ".format(reddpot_winner_user_username))
        for entry in reddpot_tipping_list:
            reddpot_msg += entry
        ## update user balances in database
        user_balances_attribute_list.append((0, bot_name[1:]))
        bulk_update_balance_from_user(user_balances_attribute_list)
        write_users_tips_list(tippings_json)
        #send_text_msg(update, context, reddpot_msg)
        bot.send_message(chat_id=reddcoin_chat_id_en, text=reddpot_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        #bot.send_message(chat_id=reddcoin_chat_id_v3test, text=reddpot_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

## Respond to user with a list of latest tips
## Command: /mytips
def mytips(update, context):
    user_username = get_username(update)
    user_input_parameter_format_list = []
    get_user_input(update, context, user_input_parameter_format_list)
    tippings_json = read_users_tips_list()
    tippings_list = []
    tippings_msg = ""
    
    if user_username is not None:
        if user_username in tippings_json:
            tippings_msg += "<b>Latest tips:</b>\n"
            for tipping_entry_json in tippings_json[user_username]:
                amount = format_number(tipping_entry_json['amount'], True, 8)
                date = datetime.strptime(tipping_entry_json['date'], '%Y-%m-%dT%H:%M:%S.%f').strftime("%Y-%m-%d %H:%M:%S")
                tipfrom = tipping_entry_json['tipfrom']
                tippings_list.append("💸 {} - ⬇️ <code>{}</code> ɌDD from @{}\n".format(date, amount, tipfrom))
            for user_entry in tippings_json:
                for tipping_entry_json in tippings_json[user_entry]:
                    amount = format_number(tipping_entry_json['amount'], True, 8)
                    date = datetime.strptime(tipping_entry_json['date'], '%Y-%m-%dT%H:%M:%S.%f').strftime("%Y-%m-%d %H:%M:%S")
                    tipfrom = tipping_entry_json['tipfrom']
                    if user_username == tipfrom:
                        tippings_list.append("💸 {} - ⬆️ <code>{}</code> ɌDD to @{}\n".format(date, amount, user_entry))
            if len(tippings_list) > 0:
                tippings_list.sort(reverse=True)
                entry_num = 0
                for entry in tippings_list:
                    entry_num += 1
                    tippings_msg += entry
                    if entry_num == tips_list_max_entries:
                        break
        else:
            tippings_msg = "Sorry @{}, but I could not find any tips.".format(user_username)
    send_text_msg(update, context, tippings_msg)

## Respond to user with a list of latest stake rewards
## Command: /mystakes
def mystakes(update, context):
    #send_text_msg(update, context, "currently disabled.")
    user_username = get_username(update)
    user_input_parameter_format_list = []
    get_user_input(update, context, user_input_parameter_format_list)
    staking_users_json = read_users_stake_rewards_list()
    stakings_list = []
    stakings_msg = ""

    if user_username is not None:
        if user_username in staking_users_json:
            stakings_msg += "<b>Latest stake rewards\n(Stake reward | Previous balance | New balance):</b>\n"
            for staking_entry_json in staking_users_json[user_username]:
                balance = get_decimal(OP_MUL, staking_entry_json['balance'], 1)
                date = ""
                if "T" in staking_entry_json['date']:
                    date = datetime.strptime(staking_entry_json['date'], '%Y-%m-%dT%H:%M:%S.%f').strftime("%Y-%m-%d %H:%M:%S")
                else:
                    date = staking_entry_json['date']
                stake = get_decimal(OP_MUL, staking_entry_json['stake'], 1)
                new_balance = balance + stake
                msg = "⛏ {}\nɌ<code>{}</code> | Ɍ<code>{}</code> | Ɍ<code>{}</code>\n".format(date, format_number(stake, True, 8), format_number(balance, True, 8), format_number(new_balance, True, 8))
                stakings_list.append(msg)
        if len(stakings_list) > 0:
            stakings_list.sort(reverse=True)
            entry_num = 0
            for entry in stakings_list:
                entry_num += 1
                stakings_msg += entry
                if entry_num == stakes_list_max_entries:
                    break
        else:
            stakings_msg = "Sorry @{}, but I could not find any stake rewards.".format(user_username)
    send_text_msg(update, context, stakings_msg)

## Transfer funds from one user to another (only for admins)
## Command: /xfer <amount> <from user> <to user>
def xfer(update, context):
    user_username = get_username(update)
    user_input_parameter_format_list = [float, str, str]
    user_input_list = get_user_input(update, context, user_input_parameter_format_list)
    if user_username in admin_list:
        amount = float(user_input_list[0])
        fromUser = user_input_list[1]
        toUser = user_input_list[2]
        
        fromUser_balance = get_balance_from_user(fromUser)
        toUser_balance = get_balance_from_user(toUser)
        
        if amount > 0.0 and fromUser_balance >= amount:
            if fromUser_balance is not None and toUser_balance is not None:
                user_balances_attribute_list = []
                user_balances_attribute_list.append((fromUser_balance - amount, fromUser))
                user_balances_attribute_list.append((toUser_balance + amount, toUser))
                bulk_update_balance_from_user(user_balances_attribute_list)
                logger.info("Transferred %s RDD from user %s to %s", amount, fromUser, toUser)
                xfer_msg = "Transferred {} RDD from user {} to {}".format(amount, fromUser, toUser)
                send_text_msg(update, context, xfer_msg)
    else:
        send_user_not_allowed_text_msg(update, context)

## Removes donor from hall of fame list (only for admins)
## CAUTION: Using legacy impl. of user input handling
## Command: /removeDonor @<username> <user first name> <user last name (optional)>
def removeDonor(update, context):
    user_username = get_username(update)
    if user_username in admin_list:
        json_obj = read_donors_list()
        user_input = update.message.text.partition(' ')[2]
        user_input_user_id = ''.join(user_input.partition(" ")).split(" ")[0]
        user_input_user_display_name = ''.join(user_input.partition(" ")).split(user_input_user_id)[1]
        user_key = user_input_user_id + " " + user_input_user_display_name.strip()
        if user_key in json_obj:
            del json_obj[user_key]
            remove_msg = "Donor '{}' was removed from hall of fame list.".format(user_key)
        else:
            remove_msg = "Sorry but donor '{}' was not found on hall of fame list 😐".format(user_key)
        write_donors_list(json_obj)
        send_text_msg(update, context, remove_msg)
    else:
        send_user_not_allowed_text_msg(update, context)

## Respond to user with a list of largest donations from all donors
## CAUTION: Using legacy impl. of user input handling
## Command: /hallOfFame
def hallOfFame(update, context):
    user_username = get_username(update)
    user_input = update.message.text[12:].strip().lower()
    json_obj = read_donors_list()
    counter = 0
    json_obj_size = str(len(json_obj))
    
    # Converting multidimensional to flat structure to use reverse sorted order
    json_obj_flat = {}
    for json_user_username, json_user_obj in json_obj.items():
        #logger.info("json_user_username: %s", json_user_username)
        #logger.info("json_user_obj: %s", json_user_obj)
        #logger.info("json_user_username: %s", json_user_username)
        #logger.info("json_user_obj['name']: %s", json_user_obj[0]['name'])
        #logger.info("json_user_obj['amount']: %s", json_user_obj[0]['amount'])
        user_username_and_name = json_user_username + " " + json_user_obj[0]['name']
        json_obj_flat[user_username_and_name] = json_user_obj[0]['amount']
    #logger.info("json_obj_flat: %s", json_obj_flat)
    
    if user_username is not None and user_input == "position":
        for key, value in sorted(json_obj_flat.items(), key=lambda item: item[1], reverse=True):
            counter += 1
            if user_username in key:
                hall_of_fame_msg = "Hey @{}, your current position in hall of fame donation list is: {} out of {}".format(user_username, counter, json_obj_size)
                break;
    else:
        rank = {1 : "🥇", 2 : "🥈", 3 : "🥉", 4 : "🎖", 5 : "🎖", 6 : "🎖", 7 : "🎖", 8 : "🎖", 9 : "🎖", 10 : "🎖"}
        hall_of_fame_msg = "<b>Top {} Ɍeddcoin donors</b> 🎉\n".format(hall_of_fame_max_entries)
        for key, value in sorted(json_obj_flat.items(), key=lambda item: item[1], reverse=True):
            counter += 1
            if counter > hall_of_fame_max_entries:
                break
            else:
                username = key.split(" ")[0]
                display_name = key.replace(username, "")
                username = "@" + username
                html_username_link = '<a href="#/im?p=%40' + username[1:] + '">' + username + '</a>' + display_name
                value = format_number(value, True, 8)
                hall_of_fame_msg += rank[counter] + " " + html_username_link + "\n-> Ɍ<code>" + value + "</code>\n"
        hall_of_fame_msg += "_____________________________\n"
        hall_of_fame_msg += "<b>We also want to thank the following anonymous donors:</b>\n"
        hall_of_fame_msg += "🥇 Anonymous 1 -> Ɍ<code>1,500,000</code>\n"
        hall_of_fame_msg += "🥈 Anonymous 2 -> Ɍ<code>1,000,000</code>\n"
        hall_of_fame_msg += "🥉 Anonymous 3 -> Ɍ<code>500,000</code>\n"
        hall_of_fame_msg += "_____________________________\n"
        hall_of_fame_msg += "‼ Use /donate 'amount of RDD' to support Ɍeddcoin charity initiatives and you might be on this list!"
    send_text_msg(update, context, hall_of_fame_msg)

## Sends a donation to Reddcoin funding address or responds with a qr code and funding address if no amount was provided
## Command: /donate <amount (optional)>
def donate(update, context):
    user_username = get_username(update)
    user_input_parameter_format_list = [float]
    verify_input = False
    user_input_list = get_user_input(update, context, user_input_parameter_format_list, verify_input)
    withdraw_successful = False
    if len(user_input_list) == 0:
        qrcode_png = create_qr_code(dev_fund_address)
        donate_qr_msg = dev_fund_address
        donate_text_msg = []
        donate_text_msg.append("Any donations are highly appreciated 👍\n")
        donate_text_msg.append("-> You can also use our tipbot 😎 Example: /donate 100\n")
        donate_text_msg.append("-> Hit /hallOfFame to get a list of top 10 contributers\n")
        send_photo_msg(update, context, qrcode_png, donate_qr_msg)
        send_text_msg(update, context, donate_text_msg)
    elif user_username is not None:
        amount = user_input_list[0]
        update.message.text = "/withdraw {} {}".format(dev_fund_address, amount)
        withdraw_successful = withdraw(update, context)
        if withdraw_successful:
            newDonation(update, context, True)

## Adds a new donation to donors list
## Command: /newDonation
def newDonation(update, context, initiated_by_user = False):
    user_username = get_username(update)
    user_input_parameter_format_list = [str, float]
    verify_input = False
    user_input_list = get_user_input(update, context, user_input_parameter_format_list, verify_input)
    if initiated_by_user:
        user_input_user_id = user_username
        user_input_user_first_name = update.message.from_user.first_name
        user_input_user_last_name = update.message.from_user.last_name
        if user_input_user_last_name == None:
            user_input_user_display_name = user_input_user_first_name
        else:
            user_input_user_display_name = user_input_user_first_name + " " + user_input_user_last_name
        user_input_user_amount = float(user_input_list[1])
        addDonation(update, context, user_input_user_id, user_input_user_display_name, user_input_user_amount)
    elif user_username in admin_list:
        user_input = update.message.text.partition(' ')[2]
        user_input_user_id = ''.join(user_input.partition(" ")).split(" ")[0]
        user_input_user_display_name_and_amount = ''.join(user_input.partition(" ")).split(user_input_user_id)[1]
        user_input_user_display_name = user_input_user_display_name_and_amount[:user_input_user_display_name_and_amount.rfind(' ')].strip()
        user_input_user_amount = user_input_user_display_name_and_amount[user_input_user_display_name_and_amount.rfind(' '):].strip()
        addDonation(update, context, user_input_user_id, user_input_user_display_name, user_input_user_amount)
    else:
        send_user_not_allowed_text_msg(update, context)

## Withdraw any amount to a specific Reddcoin address
## Command: /withdraw
def withdraw(update, context):
    user_username = get_username(update)
    user_input_parameter_format_list = [str, float]
    user_input_list = get_user_input(update, context, user_input_parameter_format_list)
    logger.info("withdraw - user_input_list: %s", user_input_list)
    withdraw_successful = False
    
    if len(user_input_list) > 1 and is_not_on_exclude_list(user_username):
        address = user_input_list[0]
        amount = float(user_input_list[1])
        if not valid_rdd_address(address):
            withdraw_msg = "Hey @{}, it looks like that <code>{}</code> is not a valid Ɍeddcoin address! Please try again.".format(user_username, address)
        else:
            balance = get_balance_from_user(user_username)
            if balance < amount:
                withdraw_msg = "Sorry @{}, but you have insufficient funds 😐 -> There is also a tx fee of Ɍ<code>{}</code>".format(user_username, tx_fee)
            elif amount > tx_fee:
                amount = get_decimal(OP_SUB, amount, tx_fee)
                #amount -= tx_fee
                tx_id = rpc_connect("sendtoaddress", [address, amount])['result']
                if len(tx_id) == 64:
                    user_balances_attribute_list = []
                    withdraw_successful = True
                    withdraw_msg = "@{} has successfully withdrawn Ɍ<code>{}</code> (tx fee of Ɍ<code>{}</code> was deducted) to address <code>{}</code> -> https://live.reddcoin.com/tx/{}".format(user_username, format_number(amount), tx_fee, address, tx_id)
                    amount = get_decimal(OP_ADD, amount, tx_fee)
                    #amount += tx_fee
                    user_balances_attribute_list.append((balance - amount, user_username))
                    bulk_update_balance_from_user(user_balances_attribute_list)
                else:
                    withdraw_msg = "Sorry @{}, but there was a problem with your request. Please contact an admin!".format(user_username)
                    logger.warning("Something went wrong: Response: %s - Issued by user %s with amount=%s and address=%s", tx_id, user_username, format_number(amount), address)
            else:
                withdraw_msg = "Sorry @{}, but the amount for withdrawals has to be more than Ɍ<code>{}</code>".format(user_username, tx_fee)
        send_text_msg(update, context, withdraw_msg)
    return withdraw_successful

## Respond to user with some current stats
## Command: /statistics
def statistics(update, context):
    # sum of staking from staking tx json file
    stakings_json = read_staking_tx_list()
    number_of_stakes = 0
    total_stake_amount = 0.0
    staking_multiplier_prefix = ""
    for tx, stake_amount in stakings_json.items():
        number_of_stakes += 1
        total_stake_amount += stake_amount
    #dev_fund_balance = str(requests.get(dev_fund_balance_api_url).content)
    #dev_fund_balance = dev_fund_balance.replace("'","").replace("b","")
    #dev_fund_balance = dev_fund_balance[:-8] + "." + dev_fund_balance[-8:]
    #dev_fund_balance = format_number(float(dev_fund_balance), True, 8)
    accounts_wallet_getinfo = json.loads(accounts_wallet_cli_call(["getinfo"]))
    accounts_wallet_getstakinginfo = json.loads(accounts_wallet_cli_call(["getstakinginfo"]))
    #accounts_wallet_listaccounts = json.loads(accounts_wallet_cli_call(["listaccounts"]))
    staking_wallet_getinfo = rpc_connect("getinfo", [])['result']

    block_height = accounts_wallet_getinfo["blocks"]
    money_supply = accounts_wallet_getinfo["moneysupply"]
    net_stake_weight = accounts_wallet_getstakinginfo["netstakeweight"]
    balance = staking_wallet_getinfo["balance"]
    stake = staking_wallet_getinfo["stake"]
    total_users = get_number_of_users()
    staking_quota = format_number(get_decimal(OP_DIV, net_stake_weight, money_supply) * 100, False, 2)
    staking_multiplier = get_posv_stats_from_logfile()
    #staking_multiplier = 100 / ((net_stake_weight / money_supply) * 100)
    #if staking_multiplier < 5:
    #    staking_multiplier_prefix = "~"
    #elif staking_multiplier > 5:
    #    staking_multiplier = 5

    # Formatting output
    block_height = format_number(block_height, False, 0)
    money_supply = format_number(money_supply, False, 0)
    net_stake_weight = format_number(net_stake_weight, False, 0)
    total_balance = format_number(balance + stake, True, 8)
    total_stake_amount = format_number(total_stake_amount, True, 8)
    #staking_multiplier = format_number(staking_multiplier, False, 3)

    block_height_msg = "✅ Block height: <code>{}</code>\n".format(block_height)
    netstake_weight_msg = "✅ There are currently <code>{} ({}%)</code> ɌDD being staked from a total of <code>{}</code>\n".format(net_stake_weight, staking_quota, money_supply)
    accounts_msg = "✅ {} is currently holding <code>{}</code> Ɍeddcoins from <code>{}</code> users".format(bot_name, total_balance, total_users)
    staking_stats_msg = " and has received a total of <code>{}</code> ɌDD from <code>{}</code> stake rewards 😎\n".format(total_stake_amount, number_of_stakes)
    #dev_fund_balance_msg = "✅ Balance of development fund: <code>{}</code> ɌDD\n".format(dev_fund_balance)
    supermajority_status_msq = "✅ PoSV v2 on Mainnet was activated on block height <a href=\"https://live.reddcoin.com/block/23ce6d230dc277af0abc3ecb2bad0c86b410d0588f345c2a04807183864dad53\">3382230</a> 🎉 - Please update your wallet to <a href=\"https://download.reddcoin.com/bin/\">latest v3</a> if you don't want to miss out on staking rewards (learn more about PoSV v2 <a href=\"https://medium.com/@techadept/rdd-posv-v2-with-enhanced-staking-a-simple-core-wallet-upgrade-and-a-quantum-leap-forward-for-58baf642fb1d\">here</a>)\n"
    staking_multiplier_msg = "✅ PoSV v2 staking multiplier: {}{}".format(staking_multiplier_prefix, staking_multiplier)
    #send_text_msg(update, context, block_height_msg + netstake_weight_msg + accounts_msg + staking_stats_msg + dev_fund_balance_msg + supermajority_status_msq)
    send_text_msg(update, context, block_height_msg + netstake_weight_msg + accounts_msg + staking_stats_msg + supermajority_status_msq + staking_multiplier_msg)

## Respond to user with current PoSV v2 status
## Command: /posv
def posv(update, context):
    # Get supermajority
    #supermajority_pos_num, supermajority_percentage = get_posv_from_debug_logfile()

    # Formatting output
    #supermajority_percentage = format_number(supermajority_percentage, True, 2)

    #supermajority_status_msq = '✅ PoSV v2 on Mainnet has reached {} out of 9000 blocks ({}%) from last 10000 generated blocks - Please update your wallet to latest v3 (learn more about PoSV v2 <a href="https://medium.com/@techadept/rdd-posv-v2-with-enhanced-staking-a-simple-core-wallet-upgrade-and-a-quantum-leap-forward-for-58baf642fb1d">here</a>)'.format(supermajority_pos_num, supermajority_percentage)
    supermajority_status_msq = "✅ PoSV v2 on Mainnet was activated on block height <a href=\"https://live.reddcoin.com/block/23ce6d230dc277af0abc3ecb2bad0c86b410d0588f345c2a04807183864dad53\">3382230</a> 🎉 - Please update your wallet to <a href=\"https://download.reddcoin.com/bin/\">latest v3</a> if you don't want to miss out on staking rewards (learn more about PoSV v2 <a href=\"https://medium.com/@techadept/rdd-posv-v2-with-enhanced-staking-a-simple-core-wallet-upgrade-and-a-quantum-leap-forward-for-58baf642fb1d\">here</a>)"
    send_text_msg(update, context, supermajority_status_msq)

def get_posv_stats_from_logfile():
    last_lines_tail_obj = os.popen("tail -5000 " + debug_log)
    staking_multiplier = 0
    for line in last_lines_tail_obj:
        if "fInflationAdjustment" in line:
            staking_multiplier_start_pos = line.find("fInflationAdjustment") + 21
            staking_multiplier_end_pos = line.find("fInflationAdjustment") + 26
            staking_multiplier = line[staking_multiplier_start_pos:staking_multiplier_end_pos]
    return staking_multiplier

def get_stake_tx_from_addresses(update, context):
    addresses = rpc_connect("listaddressgroupings", [])['result']
    address_list = []
    balance_sum = 0
    stake_sum = 0
    staking_tx_json = read_staking_tx_list()
    for address in addresses:
        for entry in address:
            entry_address = entry[0]
            entry_balance = entry[1]
            if entry_balance > 0:
                balance_sum += entry_balance
                logger.info("address:       " + entry_address)
                logger.info("balance:       " + str(entry_balance))
                address_list.append(entry_address)
    logger.info("sum of balances: " + str(balance_sum))

    for address in address_list:
        api_request_url = "http://live.reddcoin.com/api/txs/?address={}".format(address)
        txs_from_address = requests.get(api_request_url).json()
        if "txs" in txs_from_address:
            for entry in txs_from_address["txs"]:
                if "isCoinStake" in entry and entry['confirmations'] > 50:
                    txid = entry['txid']
                    stake_reward = -entry['fees']
                    if txid not in staking_tx_json:
                        stake_sum += stake_reward
                        logger.info("stake tx from address " + address + ": " + txid + " - " + str(stake_reward))
    logger.info("sum of missing stake rewards: " + str(stake_sum))

def broadcast_stake(update, context):
    staking_tx_json = read_staking_tx_list()
    staking_users_json = read_users_stake_rewards_list()
    stake_transactions_msg = []
    user_input_parameter_format_list = [str, float]
    user_input_list = get_user_input(update, context, user_input_parameter_format_list)
    tx_id = user_input_list[0]
    stake_reward = user_input_list[1]
    stake_transactions_msg.append("What a great day, ɌeddHeads! Our Tipping Bot just received a successful stake of Ɍ<code>{}</code> and if you have some Ɍeddcoins in your Telegram tip bot wallet you just got some free Ɍeddcoins 🤑\n\n".format(stake_reward))
    stake_transactions_msg.append("Check out how much you got by sending /mystakes as a private message to {} -> Otherwise bot will directly reply here with a list of your latest stake rewards including your balance.".format(bot_name))
    staking_tx_json[tx_id] = float(stake_reward)
    users_balance = 0.0
    
    result = get_all_user_balance_entries()
    logger.info("broadcast_stake - get_all_user_balance_entries: %s", result)
    
#    for user, user_balance in users_json.items():
#        users_balance += user_balance
#    for user, user_balance in users_json.items():
#        if user_balance > 0.0:
#            current_balance = user_balance
#            stake_proportion = get_decimal(OP_DIV, user_balance, users_balance) * float(stake_reward)
#            new_balance = current_balance + stake_proportion
#            users_json[user] = new_balance
#            ts_iso8601 = datetime.utcnow().isoformat()
#            if user not in staking_users_json:
#                staking_users_json[user] = [{'txid': tx_id, 'balance': current_balance, 'date': ts_iso8601, 'stake': stake_proportion}]
#            else:
#                staking_users_json[user].append({'txid': tx_id, 'balance': current_balance, 'date': ts_iso8601, 'stake': stake_proportion})
#    if len(stake_transactions_msg) > 0:
#        stake_transactions_msg = ''.join(stake_transactions_msg)
#        context.bot.send_message(chat_id=reddcoin_chat_id_en, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
#        context.bot.send_message(chat_id=reddcoin_chat_id_ko, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
#        context.bot.send_message(chat_id=reddcoin_chat_id_nl, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
#        context.bot.send_message(chat_id=reddcoin_chat_id_de, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
#        write_staking_tx_list(staking_tx_json)
#        write_users_stake_rewards_list(staking_users_json)

def moon(update, context):
    moon_msg = "Moon mission inbound!"
    send_animation_msg(update, context, reddcoin_rocket_ani, moon_msg)

def newwebsite(update, context):
    send_text_msg(update, context, "🎉🎉🎉 https://reddcoin.com 🎉🎉🎉")

def newwallet(update, context):
    send_text_msg(update, context, "🎉🎉🎉 https://github.com/reddcoin-project/reddcoin/releases 🎉🎉🎉")

if __name__ == '__main__':
    main()
