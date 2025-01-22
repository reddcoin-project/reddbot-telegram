#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author: Oliver Webb
"""

import json
import uuid
import config
import util
import scheduled_tasks
from cached_data import TelegramUser
from db_redis import DbRedis
from db_mysql import DbMySQL
from users import User
from users_autowithdrawal import UserAutowithdrawal
from users_transactions import UserTransactions
import random
import tzlocal
from decimal import *
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import (Updater, CallbackContext, CommandHandler, MessageHandler, Filters)
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

# Telegram bot dispatcher and handlers
# Create the Updater and pass it your bot's token.
updater = Updater(token=config.bot_token, use_context=True)


def main():
    # Initial tasks
    scheduled_tasks.fetch_market_data()
    scheduled_tasks.fetch_blockchain_data()
    scheduled_tasks.check_autowithdrawal()
    #scheduled_tasks.check_stake_transactions(updater)

    # Main Scheduler setup for running tasks
    scheduler = BackgroundScheduler(timezone=str(tzlocal.get_localzone()))
    if config.scheduler_active:
        scheduler.add_job(check_receive_transactions, 'interval', seconds=30)
        scheduler.add_job(check_stake_transactions, 'cron', day_of_week='mon-sun', hour=22, minute=10, jitter=10)
        #scheduler.add_job(check_stake_transactions, 'interval', seconds=100, jitter=20)
        scheduler.add_job(check_market_data, 'interval', seconds=300)
        scheduler.add_job(check_blockchain_data, 'interval', seconds=20)
        scheduler.add_job(check_autowithdrawal, 'interval', seconds=120)
        scheduler.add_job(backup_redis_db_to_disk, 'interval', seconds=600)
    scheduler.start()
    util.logging.getLogger('apscheduler').setLevel(util.logging.DEBUG)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", commands))
    dispatcher.add_handler(CommandHandler("commands", commands))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("about", about))
    dispatcher.add_handler(CommandHandler("changelog", changelog))
    dispatcher.add_handler(CommandHandler("newwebsite", newwebsite))
    dispatcher.add_handler(CommandHandler("moon", moon))
    dispatcher.add_handler(CommandHandler("statistics", statistics))
    dispatcher.add_handler(CommandHandler("hi", hi))
    dispatcher.add_handler(CommandHandler("donate", donate))
    dispatcher.add_handler(CommandHandler("crowdfund", crowdfund))
    dispatcher.add_handler(CommandHandler("withdraw", withdraw))
    dispatcher.add_handler(CommandHandler("autowithdraw", autowithdraw))
    dispatcher.add_handler(CommandHandler("marketcap", marketcap))
    dispatcher.add_handler(CommandHandler("deposit", deposit))
    dispatcher.add_handler(CommandHandler("price", price))
    dispatcher.add_handler(CommandHandler("tip", tip))
    dispatcher.add_handler(CommandHandler("balance", balance))
    dispatcher.add_handler(CommandHandler("rain", rain))
    dispatcher.add_handler(CommandHandler("rainbow", rainbow))
    dispatcher.add_handler(CommandHandler("snow", snow))
    dispatcher.add_handler(CommandHandler("sun", sun))
    dispatcher.add_handler(CommandHandler("sunshine", sunshine))
    dispatcher.add_handler(CommandHandler("love", love))
    dispatcher.add_handler(CommandHandler("mytips", mytips))
    dispatcher.add_handler(CommandHandler("mystakes", mystakes))
    dispatcher.add_handler(CommandHandler("mydeposits", mydeposits))
    dispatcher.add_handler(CommandHandler("mydonations", mydonations))
    dispatcher.add_handler(CommandHandler("mywithdrawals", mywithdrawals))
    dispatcher.add_handler(CommandHandler("myautowithdrawals", myautowithdrawals))

    # Add handler for all non-command messages
    dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=incoming_msg))

    # Add error handler.
    dispatcher.add_error_handler(error)

    # Start the Bot.
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def error(update: Update, context: CallbackContext):
    try:
        raise context.error
    except Unauthorized:
        util.logger.error('Unauthorized error: %s', update)
    except BadRequest:
        util.logger.error('BadRequest: %s', update)
    except TimedOut:
        util.logger.error('TimedOut: %s', update)
    except NetworkError:
        util.logger.error('NetworkError: %s', update)
    except ChatMigrated as e:
        util.logger.error('ChatMigrated: %s', e)
    except TelegramError:
        util.logger.error('TelegramError: %s', update)


##############################################################################################
# Telegram Reddbot functions and commands                                                    #
##############################################################################################


# Called by scheduler for checking incoming receive transactions
def check_receive_transactions():
    scheduled_tasks.check_deposit_transactions()


# Called by scheduler for checking incoming stake transactions
def check_stake_transactions():
    scheduled_tasks.check_stake_transactions(updater)


# Called by scheduler for checking autowithdrawal
def check_autowithdrawal():
    scheduled_tasks.check_autowithdrawal()


# Called by scheduler for fetching current market data
def check_market_data():
    scheduled_tasks.fetch_market_data()


# Called by scheduler for fetching current blockchain data
def check_blockchain_data():
    scheduled_tasks.fetch_blockchain_data()


# Called by scheduler for saving current redis in memory db to local disk
def backup_redis_db_to_disk():
    DbRedis.backup_db_to_disk()


# Called for all incoming messages except for /<command>
def incoming_msg(update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    print(telegram_user)
    new_chat_members_list = util.get_new_chat_members(update)
    for user in new_chat_members_list:
        util.logger.info("incoming_msg - new_chat_members.username: %s", user.username)
    if telegram_user.username != 'GroupAnonymousBot' and (telegram_user.chat_type == "group" or telegram_user.chat_type == "supergroup"):
        create_new_user = DbRedis.update_user_activity(account_id=telegram_user.id, chat_id=telegram_user.chat_id, msg_date=telegram_user.msg_date)
        if create_new_user:
            check_user(telegram_user=telegram_user)


# Respond to user with basic information how to use Reddbot commands
# Command: /help
def help(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    if telegram_user.username is None:
        username_prefix = ""
    else:
        username_prefix = "@"
    help_msg = []
    help_msg.append("Hello {} 👋 Initiating commands /tip & /withdraw have a specific format. Use them like so:\n\n".format(username_prefix + telegram_user.username))
    help_msg.append("<b>Parameters:</b>\n")
    help_msg.append("<code>username</code> = target user to tip (starting with @)\n")
    help_msg.append("<code>amount</code> = amount of Reddcoin to utilize\n")
    help_msg.append("<code>address</code> = Reddcoin address to withdraw to\n\n")
    help_msg.append("<b>Tipping format:</b>\n")
    help_msg.append("<code>/tip @username amount</code>\n\n")
    help_msg.append("<b>Withdrawing format:</b>\n")
    help_msg.append("<code>/withdraw address amount</code>\n\n")
    help_msg.append("Need more help? -> View all /commands")
    util.send_text_msg(update, context, help_msg)


# Respond to user with all Reddbot commands and how to use them specifically
# Command: /commands
def commands(update: Update, context: CallbackContext):
    commands_msg = []
    commands_msg.append("<b>The following commands are at your disposal:</b>\n")
    commands_msg.append("/hi /commands /deposit /tip /rain /donate /withdraw /autowithdraw /balance /mytips /mystakes /mydeposits /mydonations /mywithdrawals /myautowithdrawals /price /marketcap /statistics /moon /about /changelog\n\n")
    commands_msg.append("<b>Examples:</b>\n")
    commands_msg.append("<code>/tip @cryptoBUZE 100</code>\n")
    commands_msg.append("➡️ send a tip of 100 Reddcoins to the tipbot maintainer 'cryptoBUZE'\n")
    commands_msg.append("<code>/donate 100</code>\n")
    commands_msg.append("➡️ support Reddcoin organization team by donating them 100 Reddcoins\n")
    commands_msg.append("<code>/rain 100 24</code>\n")
    commands_msg.append("➡️ tip some ɌeddHeads with Telegram activity in the last 24 hours (amount divided by total active numbers in given timeframe)\n")
    commands_msg.append("<code>/autowithdraw {} 1000</code>\n".format(config.posv_v2_dev_fund_address))
    commands_msg.append("➡️ set threshold limit to 1000 Reddcoins - If your balance reaches this value the full amount is send to a specific address (in this example: dev fund raising address which is also used for /donate)\n")
    commands_msg.append("<code>/withdraw {} 100</code>\n".format(config.posv_v2_dev_fund_address))
    commands_msg.append("➡️ send 100 Reddcoins to a specific address (in this example: dev fund raising address which is also used for /donate)\n")
    commands_msg.append("<code>/mytips</code>\n")
    commands_msg.append("➡️ Get a list of all recent sent and received tips\n")
    commands_msg.append("<code>/mystakes</code>\n")
    commands_msg.append("➡️ Get a list of all recent received stakes\n")
    util.send_text_msg(update, context, commands_msg)


# Respond to user with basic information about Reddbot
# Command: /about
def about(update: Update, context: CallbackContext):
    about_msg = []
    about_msg.append("{} was originally coded by @xGozzy (Ex-Developer) and was further developed by @cryptoBUZE\n".format(config.bot_name))
    about_msg.append("The source code can be viewed at https://github.com/reddcoin-project/reddbot-telegram\n")
    about_msg.append("If you have any enquiries please contact @TechAdept or @cryptoBUZE\n")
    util.send_text_msg(update, context, about_msg)


# Respond to user with recent and older changes
# Command: /changelog
def changelog(update: Update, context: CallbackContext):
    changelog_msg = []
    changelog_msg.append("<b>Changelog for {} {}:</b>\n".format(config.app_name, config.app_version))
    changelog_msg.append("✔️ New command /mydeposits that shows list of recent deposit transactions\n")
    changelog_msg.append("✔️ New command /mydonations that shows list of recent donation transactions\n")
    changelog_msg.append("✔️ New command /mywithdrawals that shows list of recent withdrawal transactions\n")
    changelog_msg.append("✔️ New command /autowithdraw for setting threshold value that withdraws balance at a certain amount\n")
    changelog_msg.append("✔️ New command /myautowithdrawals that shows list of recent withdrawal transactions when threshold value was set using /autowithdraw\n")
    changelog_msg.append("✔️ Command /deposit adds now separated message with Reddcoin address\n")
    changelog_msg.append("✔️ Commands with with more than one argument don't need to be strict positional any more\n")
    changelog_msg.append("✔️ Telegram user name can now be changed without loosing balance\n")
    changelog_msg.append("✔️ Feeless transactions for withdrawals\n")
    changelog_msg.append("✔️ Overall performance increase due to caching\n")
    util.send_text_msg(update, context, changelog_msg)


# Respond to user with a simple hi message
# Command: /hi
def hi(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    if telegram_user.username is None:
        username_prefix = ""
    else:
        username_prefix = "@"
    hi_msg = "Hello {} How are you doing today?".format(username_prefix + telegram_user.username)
    util.send_text_msg(update, context, hi_msg)


# Respond to user with current price information
# Command: /price
def price(update: Update, context: CallbackContext):
    market_data = DbRedis.get_market_data_info()
    price_usd = util.format_number(market_data.rdd_price_usd)
    price_change_percentage_24h = market_data.price_change_percentage_24h
    price_msg = "1 Ɍeddcoin is valued at $<code>{}</code> Δ <code>{}</code>".format(price_usd, price_change_percentage_24h)
    util.send_text_msg(update, context, price_msg)


# Respond to user with current market capitalization information
# Command: /marketcap
def marketcap(update: Update, context: CallbackContext):
    market_data = DbRedis.get_market_data_info()
    marketcap_btc = util.format_number(market_data.rdd_market_cap_btc)
    marketcap_usd = util.format_number(market_data.rdd_market_cap_usd)
    marketcap_msg = "The current market cap of Reddcoin is valued at $<code>{}</code> ≈ ₿<code>{}</code>".format(marketcap_usd, marketcap_btc)
    util.send_text_msg(update, context, marketcap_msg)


# Respond to user with a deposit address and qr code bound to unique Telegram id
# Command: /deposit
def deposit(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    check_user(telegram_user=telegram_user)
    user_account_address = util.fetch_deposit_address(telegram_user.id)
    qrcode_png = util.create_qr_code(user_account_address)
    deposit_msq_qr_code = "Use this qr code or copy the following deposit address:"
    util.send_photo_msg(update, context, qrcode_png, deposit_msq_qr_code)
    util.send_text_msg(update, context, user_account_address)


# Respond to user with current balance
# Command: /balance
def balance(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    user = check_user(telegram_user=telegram_user)
    if telegram_user.chat_type != "private":
        balance_msg = "Please send this command as a private message to {}".format(config.bot_name)
    else:
        market_data = DbRedis.get_market_data_info()
        fiat_balance = float(user.balance) * market_data.rdd_price_usd
        fiat_balance = util.format_number(fiat_balance, False, 4)
        user_balance = util.format_number(user.balance, False, 8)
        balance_msg = "Your current balance is: Ɍ<code>{}</code> ≈ $<code>{}</code>".format(user_balance, fiat_balance)
    util.send_text_msg(update, context, balance_msg)


# Respond to user with a list of recent stake rewards
# Command: /mystakes
def mystakes(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    user = check_user(telegram_user)
    staking_msg = []
    if telegram_user.chat_type != "private":
        staking_msg.append("To get a list of your recent stake rewards please send this command as a private message to {}".format(config.bot_name))
    else:
        task_name = DbMySQL.start_tx()
        try:
            user_tx_list = UserTransactions.get_stake_rewards_by_user(task_name=task_name, user_name=user.user_name)
        finally:
            DbMySQL.end_tx(task_name=task_name)
        if len(user_tx_list) > 0:
            staking_msg.append("<b>Recent stake rewards\n(Stake reward | New balance):</b>\n")
            for user_stake_tx in user_tx_list[:30]:
                msg = "⛏ {}\nɌ<code>{}</code> | Ɍ<code>{}</code>\n".format(user_stake_tx.create_date, user_stake_tx.amount, user_stake_tx.amount + user_stake_tx.balance)
                staking_msg.append(msg)
        else:
            staking_msg.append("Sorry but I could not find any recent stake rewards for your account.")
    util.send_text_msg(update, context, staking_msg)


# Respond to user with a list of all latest tip transactions
# Command: /mytips
def mytips(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    user = check_user(telegram_user)
    tips_msg = []
    if telegram_user.chat_type != "private":
        tips_msg.append("To get a list of your latest tips please send this command as a private message to {}".format(config.bot_name))
    else:
        task_name = DbMySQL.start_tx()
        try:
            user_tx_list = UserTransactions.get_tips_by_user(task_name=task_name, user_name=user.user_name)
            if len(user_tx_list) > 0:
                tips_msg.append("<b>Latest tips:</b>\n")
                for user_tip_tx in user_tx_list:
                    affected_user_tip_tx = User.get_user_by_user_name(task_name=task_name, user_name=user_tip_tx.affected_user_name)
                    if user_tip_tx.tx_type == "tip_send":
                        msg = "💸⬆️ {}\nɌ<code>{}</code> to @{}\n".format(user_tip_tx.create_date, user_tip_tx.amount, affected_user_tip_tx.user_name)
                        tips_msg.append(msg)
                    if user_tip_tx.tx_type == "tip_receive":
                        msg = "💸⬇️ {}\nɌ<code>{}</code> from @{}\n".format(user_tip_tx.create_date, user_tip_tx.amount, affected_user_tip_tx.user_name)
                        tips_msg.append(msg)
                    if user_tip_tx.tx_type == "rain_send":
                        msg = "🌦⬆️ {}\nɌ<code>{}</code> to @{}\n".format(user_tip_tx.create_date, user_tip_tx.amount, affected_user_tip_tx.user_name)
                        tips_msg.append(msg)
                    if user_tip_tx.tx_type == "rain_receive":
                        msg = "🌦⬇ {}\nɌ<code>{}</code> from @{}\n".format(user_tip_tx.create_date, user_tip_tx.amount, affected_user_tip_tx.user_name)
                        tips_msg.append(msg)
            else:
                tips_msg.append("Sorry but I could not find any recent tips for your account.")
        finally:
            DbMySQL.end_tx(task_name=task_name)
    util.send_text_msg(update, context, tips_msg)


# Respond to user with a list of all latest incoming transactions
# Command: /mydeposits
def mydeposits(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    user = check_user(telegram_user)
    receive_tx_msg = []
    if telegram_user.chat_type != "private":
        receive_tx_msg.append("To get a list of your latest deposits please send this command as a private message to {}".format(config.bot_name))
    else:
        task_name = DbMySQL.start_tx()
        try:
            user_tx_list = UserTransactions.get_deposits_by_user(task_name=task_name, user_name=user.user_name)
            if len(user_tx_list) > 0:
                receive_tx_msg.append("<b>Latest incoming transactions:</b>\n")
                for user_receive_tx in user_tx_list:
                    msg = "💸⬇️ {}\nɌ<code>{}</code> for address <code>{}</code> (<a href='https://live.reddcoin.com/tx/{}'>details</a>)\n".format(user_receive_tx.create_date, user_receive_tx.amount, user_receive_tx.address, user_receive_tx.tx_id)
                    receive_tx_msg.append(msg)
            else:
                receive_tx_msg.append("Sorry but I could not find any recent incoming transactions for your account.")
        finally:
            DbMySQL.end_tx(task_name=task_name)
    util.send_text_msg(update, context, receive_tx_msg)


# Respond to user with a list of all latest donations
# Command: /mydonations
def mydonations(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    user = check_user(telegram_user)
    donation_tx_msg = []
    if 1 != 1:
        donation_tx_msg.append("To get a list of your latest donations please send this command as a private message to {}".format(config.bot_name))
    else:
        task_name = DbMySQL.start_tx()
        try:
            user_tx_list = UserTransactions.get_donations_by_user(task_name=task_name, user_name=user.user_name)
            if len(user_tx_list) > 0:
                donation_tx_msg.append("<b>Latest outgoing transactions:</b>\n")
                for user_receive_tx in user_tx_list:
                    msg = "💸⬆️ {}\nɌ<code>{}</code> to address <code>{}</code> (<a href='https://live.reddcoin.com/tx/{}'>details</a>)\n".format(user_receive_tx.create_date, user_receive_tx.amount, user_receive_tx.address, user_receive_tx.tx_id)
                    donation_tx_msg.append(msg)
            else:
                donation_tx_msg.append("Sorry but I could not find any recent donations for your account.")
        finally:
            DbMySQL.end_tx(task_name=task_name)
    util.send_text_msg(update, context, donation_tx_msg)


# Respond to user with a list of all latest outgoing transactions
# Command: /mywithdrawals
def mywithdrawals(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    user = check_user(telegram_user)
    send_tx_msg = []
    if telegram_user.chat_type != "private":
        send_tx_msg.append("To get a list of your latest withdrawals please send this command as a private message to {}".format(config.bot_name))
    else:
        task_name = DbMySQL.start_tx()
        try:
            user_tx_list = UserTransactions.get_withdrawals_by_user(task_name=task_name, user_name=user.user_name)
            if len(user_tx_list) > 0:
                send_tx_msg.append("<b>Latest outgoing transactions:</b>\n")
                for user_receive_tx in user_tx_list:
                    msg = "💸⬆️ {}\nɌ<code>{}</code> to address <code>{}</code> (<a href='https://live.reddcoin.com/tx/{}'>details</a>)\n".format(user_receive_tx.create_date, user_receive_tx.amount, user_receive_tx.address, user_receive_tx.tx_id)
                    send_tx_msg.append(msg)
            else:
                send_tx_msg.append("Sorry but I could not find any recent outgoing transactions for your account.")
        finally:
            DbMySQL.end_tx(task_name=task_name)
    util.send_text_msg(update, context, send_tx_msg)


# Respond to user with a list of all latest outgoing transactions (auto withdrawals)
# Command: /myautowithdrawals
def myautowithdrawals(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    user = check_user(telegram_user)
    autowithdrawal_msg = []
    if telegram_user.chat_type != "private":
        autowithdrawal_msg.append("To get a list of your latest autowithdrawals please send this command as a private message to {}".format(config.bot_name))
    else:
        task_name = DbMySQL.start_tx()
        try:
            user_tx_list = UserTransactions.get_autowithdrawals_by_user(task_name=task_name, user_name=user.user_name)
            if len(user_tx_list) > 0:
                autowithdrawal_msg.append("<b>Latest auto withdrawal transactions:</b>\n")
                for user_autowithdrawal_tx in user_tx_list:
                    msg = "💸⬆️ {}\nɌ<code>{}</code> to address <code>{}</code> (<a href='https://live.reddcoin.com/tx/{}'>details</a>)\n".format(user_autowithdrawal_tx.create_date, user_autowithdrawal_tx.amount, user_autowithdrawal_tx.address, user_autowithdrawal_tx.tx_id)
                    autowithdrawal_msg.append(msg)
            else:
                autowithdrawal_msg.append("Sorry but I could not find any recent auto withdrawal transactions for your account.")
        finally:
            DbMySQL.end_tx(task_name=task_name)
    util.send_text_msg(update, context, autowithdrawal_msg)


# Sends a donation to Reddcoin funding address or responds with a qr code and funding address if no amount was provided
# Command: /donate <amount (optional)>
def donate(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    user = check_user(telegram_user)
    user_input_list = util.get_user_input(update, context, telegram_user)
    if len(user_input_list) == 0:
        qrcode_png = util.create_qr_code(config.donation_address)
        donate_qr_msg = config.donation_address
        donate_text_msg = []
        donate_text_msg.append("Any donations are highly appreciated 👍\n")
        donate_text_msg.append("-> You can also use our tipbot 😎 Example: /donate 100\n")
        util.send_photo_msg(update, context, qrcode_png, donate_qr_msg)
        util.send_text_msg(update, context, donate_text_msg)
    else:
        amount = user_input_list[0]
        update.message.text = "/withdraw {} {}".format(config.donation_address, amount)
        withdraw_successful = withdraw(update, context, donation=True)
        if withdraw_successful:
            donation_msg = "Added a new donation of Ɍ<code>{}</code> to dev fund 🎉".format(amount)
            util.send_text_msg(update, context, donation_msg)


# Sends Reddcoin to crowdfund address or responds with a qr code and crowdfund address if no amount was provided
# Command: /crowdfund <amount (optional)>
def crowdfund(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    user_input_list = util.get_user_input(update, context, telegram_user)
    if len(user_input_list) == 0:
        qrcode_png = util.create_qr_code(config.crowdfund_address)
        donate_qr_msg = config.crowdfund_address
        donate_text_msg = []
        donate_text_msg.append("If you want to see Reddcoin on more exchanges like BitMart you can support the core team by sending Reddcoins to the address above.\n")
        donate_text_msg.append("-> You can also use our tipbot 😎 Example: /crowdfund 100\n")
        util.send_photo_msg(update, context, qrcode_png, donate_qr_msg)
        util.send_text_msg(update, context, donate_text_msg)
    else:
        amount = user_input_list[0]
        update.message.text = "/withdraw {} {}".format(config.crowdfund_address, amount)
        withdraw_successful = withdraw(update, context, donation=True)
        if withdraw_successful:
            donation_msg = "Added a new donation of Ɍ<code>{}</code> to crowd fund 🎉".format(amount)
            util.send_text_msg(update, context, donation_msg)


# Withdraw any amount to a specific Reddcoin address
# Command: /withdraw
def withdraw(update: Update, context: CallbackContext, donation: bool = False) -> bool:
    telegram_user = util.get_telegram_user_data(update)
    check_user(telegram_user)
    user_input_list = util.get_user_input(update, context, telegram_user)
    withdraw_successful = False
    address = ""
    amount = 0
    if len(user_input_list) == 2 and not DbRedis.is_user_on_banned_list(telegram_user.id):
        if not util.is_numeric(user_input_list[0]):
            address = user_input_list[0]
        elif not util.is_numeric(user_input_list[1]):
            address = user_input_list[1]
        if util.is_numeric(user_input_list[0]):
            amount = Decimal(user_input_list[0])
        elif util.is_numeric(user_input_list[1]):
            amount = Decimal(user_input_list[1])
        if len(address) > 0 and amount >= 0:
            if not util.valid_rdd_address(address):
                withdraw_msg = "It looks like that <code>{}</code> is not a valid Reddcoin address! Please try again.".format(address)
            else:
                task_name = DbMySQL.start_tx()
                try:
                    user = User.get_user(task_name=task_name, account_id=telegram_user.id)
                    if user.balance < amount:
                        withdraw_msg = "Sorry but you have insufficient funds 😐"
                    else:
                        tx_id = util.reddcoin_wallet_cli_call(["sendtoaddress", address, amount])
                        if len(tx_id) == 64:
                            withdraw_successful = True
                            user.balance = user.balance - amount
                            User.update_user(task_name=task_name, user=user)
                            if donation:
                                UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=user.user_name, address=address, amount=amount, balance=user.balance + amount, tx_type="donation", tx_id=tx_id, affected_user_name="", create_date=datetime.utcnow()))
                            else:
                                UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=user.user_name, address=address, amount=amount, balance=user.balance + amount, tx_type="send", tx_id=tx_id, affected_user_name="", create_date=datetime.utcnow()))
                            withdraw_msg = "You have successfully withdrawn Ɍ<code>{}</code> to address <code>{}</code> (<a href='https://live.reddcoin.com/tx/{}'>details</a>)".format(amount, address, tx_id)
                        else:
                            withdraw_msg = "Sorry but there was a problem with your request. Please contact an admin!"
                            util.logger.warning("Something went wrong: Response: %s - Issued by user %s with amount=%s and address=%s", tx_id, telegram_user.username, amount, address)
                finally:
                    DbMySQL.end_tx(task_name)
        else:
            withdraw_msg = "There is something missing or wrong! See /help for an example."
    else:
        withdraw_msg = "There is something missing or wrong! See /help for an example."
    util.send_text_msg(update, context, withdraw_msg)
    return withdraw_successful


# Set Autowithdraw with amount to a specific Reddcoin address
# Command: /autowithdraw
def autowithdraw(update: Update, context: CallbackContext):
    telegram_user = util.get_telegram_user_data(update)
    check_user(telegram_user)
    user_input_list = util.get_user_input(update, context, telegram_user)
    address = ""
    threshold = -1
    task_name = DbMySQL.start_tx()
    try:
        if len(user_input_list) == 0:
            user = UserAutowithdrawal.get(task_name=task_name, account_id=telegram_user.id)
            if user.threshold == 0:
                autowithdrawal_msg = "There is currently no auto withdrawal threshold set."
            else:
                autowithdrawal_msg = "Auto withdrawal threshold is currently set to Ɍ<code>{}</code> for address <code>{}</code>".format(util.convert_decimal(user.threshold), user.address)
        elif len(user_input_list) == 2 and not DbRedis.is_user_on_banned_list(telegram_user.id):
            if not util.is_numeric(user_input_list[0]):
                address = user_input_list[0]
            elif not util.is_numeric(user_input_list[1]):
                address = user_input_list[1]
            if util.is_numeric(user_input_list[0]):
                threshold = user_input_list[0]
            elif util.is_numeric(user_input_list[1]):
                threshold = user_input_list[1]
            if len(address) > 0 and float(threshold) >= 0:
                if not util.valid_rdd_address(address):
                    autowithdrawal_msg = "It looks like that <code>{}</code> is not a valid Reddcoin address! Please try again.".format(address)
                else:
                    user = UserAutowithdrawal.get(task_name=task_name, account_id=telegram_user.id)
                    if user.address is None:
                        UserAutowithdrawal.insert(task_name=task_name, entry=UserAutowithdrawal(account_id=telegram_user.id, threshold=threshold, address=address))
                    else:
                        UserAutowithdrawal.update(task_name=task_name, entry=UserAutowithdrawal(account_id=telegram_user.id, threshold=threshold, address=address))
                    if float(threshold) == 0:
                        autowithdrawal_msg = "Auto withdrawal threshold was deactivated."
                    else:
                        autowithdrawal_msg = "Auto withdrawal threshold was set to Ɍ<code>{}</code> for address <code>{}</code>".format(threshold, address)
            else:
                autowithdrawal_msg = "There is something missing or wrong! See /help for an example."
        else:
            autowithdrawal_msg = "There is something missing or wrong! See /help for an example."
    finally:
        DbMySQL.end_tx(task_name)
    util.send_text_msg(update, context, autowithdrawal_msg)


# Respond to user with some current stats
# Command: /statistics
def statistics(update: Update, context: CallbackContext):
    task_name = DbMySQL.start_tx()
    try:
        #number_of_stakes = UserTransactions.get_number_of_stakes(task_name=task_name)
        #total_stake_amount = UserTransactions.get_total_stake_amount(task_name=task_name)
        total_balance = User.get_users_overall_balance(task_name=task_name)
        total_users = User.get_number_of_users(task_name=task_name)
    finally:
        DbMySQL.end_tx(task_name=task_name)
    stake_data = DbRedis.get_stake_data()
    number_of_stakes = stake_data.number_of_stakes
    total_stake_amount = stake_data.total_stake_amount
    blockchain_data = DbRedis.get_blockchain_data()
    block_height = blockchain_data.last_block_height
    money_supply = blockchain_data.max_supply
    rdd_being_staked = blockchain_data.rdd_being_staked
    staking_quota = (rdd_being_staked / money_supply) * 100
    staking_multiplier = blockchain_data.posv_v2_multiplier

    # Formatting output
    block_height = util.format_number(block_height, False, 0)
    money_supply = util.format_number(money_supply, False, 0)
    net_stake_weight = util.format_number(rdd_being_staked, False, 0)
    total_balance = util.format_number(total_balance, True, 8)
    total_users = util.format_number(total_users, False, 0)
    number_of_stakes = util.format_number(number_of_stakes, False, 0)
    total_stake_amount = util.format_number(total_stake_amount, True, 8)
    staking_quota = util.format_number(staking_quota, False, 2)

    title_msg = "<b>{} - {}</b>\n".format(config.app_name, config.app_version)
    block_height_msg = "✅ Block height: <code>{}</code>\n".format(block_height)
    netstake_weight_msg = "✅ There are currently <code>{} ({}%)</code> ɌDD being staked from a total of <code>{}</code>\n".format(net_stake_weight, staking_quota, money_supply)
    accounts_msg = "✅ {} is currently holding <code>{}</code> Reddcoins from <code>{}</code> users".format(config.bot_name, total_balance, total_users)
    staking_stats_msg = " and has received a total of <code>{}</code> ɌDD from <code>{}</code> stake rewards 😎\n".format(total_stake_amount, number_of_stakes)
    staking_multiplier_msg = "✅ PoSV v2 staking multiplier: {}\n".format(staking_multiplier)
    wallet_update_msq = "🚨 Are you running your own Reddcoin Core Wallet? Have you already updated to latest version? <a href=\"https://download.reddcoin.com/bin/reddcoin-core-4.22.8\">download</a>\n"
    util.send_text_msg(update, context, title_msg + block_height_msg + netstake_weight_msg + accounts_msg + staking_stats_msg + staking_multiplier_msg + wallet_update_msq)


def rain(update: Update, context: CallbackContext):
    type_of_weather = "rain"
    weather_tipping(update, context, type_of_weather)


def rainbow(update: Update, context: CallbackContext):
    type_of_weather = "rainbow"
    weather_tipping(update, context, type_of_weather)


def snow(update: Update, context: CallbackContext):
    type_of_weather = "snow"
    weather_tipping(update, context, type_of_weather)


def sun(update: Update, context: CallbackContext):
    type_of_weather = "sun"
    weather_tipping(update, context, type_of_weather)


def sunshine(update: Update, context: CallbackContext):
    type_of_weather = "sun"
    weather_tipping(update, context, type_of_weather)


def love(update: Update, context: CallbackContext):
    type_of_weather = "love"
    weather_tipping(update, context, type_of_weather)


def active_user_list(account_id, chat_id, msg_date, activity):
    users_activity_json = DbRedis.get_user_activity().user_json
    last_active_users_list = []
    for active_account_id in users_activity_json:
        for users_activity_entry_json in users_activity_json[active_account_id]:
            if users_activity_entry_json["chat_id"] == chat_id:
                if not isinstance(msg_date, str):
                    current_ts = msg_date.timestamp()
                else:
                    current_ts = float(msg_date)
                diff = current_ts - users_activity_entry_json["date"]
                hours = diff / 60 / 60
                if hours <= activity and str(account_id) != str(active_account_id):
                    last_active_users_list.append(active_account_id)
    return last_active_users_list


# Send a tip to other active Telegram users which is split equality
# Command: /rain <amount> <hours of last activity>
def weather_tipping(update, context, type_of_weather="rain"):
    telegram_user = util.get_telegram_user_data(update)
    check_user(telegram_user)
    user_input_list = util.get_user_input(update, context, telegram_user)
    amount = 0
    activity = 0
    rain_msg = ""
    last_active_users_list = []
    if len(user_input_list) > 0 and not DbRedis.is_user_on_banned_list(telegram_user.id):
        if len(user_input_list) == 1 and util.is_numeric(user_input_list[0]):
            amount = Decimal(user_input_list[0])
            activity = config.rain_default_activity_hours
        elif util.is_numeric(user_input_list[0]) and util.is_numeric(user_input_list[1]):
            amount = Decimal(user_input_list[0])
            activity = float(user_input_list[1])
        task_name = DbMySQL.start_tx()
        try:
            issuer_user = User.get_user(task_name=task_name, account_id=telegram_user.id)
            if issuer_user.balance < amount:
                rain_msg = "Sorry but you have insufficient funds."
            else:
                last_active_users_list = active_user_list(telegram_user.id, telegram_user.chat_id, telegram_user.msg_date, activity)
            if len(last_active_users_list) > 0:
                amount_per_reddhead = util.convert_decimal(amount / len(last_active_users_list))
                rain_tipping_list = []
                rain_msg = "@{} has tipped Ɍ<code>{}</code> to all ReddHeads that have been active in the last {} hour(s).".format(telegram_user.username, amount_per_reddhead, activity)
                if type_of_weather == "rain":
                    rain_tipping_list.append("💸 -> ")
                elif type_of_weather == "rainbow":
                    rain_tipping_list.append("🌈 -> ")
                elif type_of_weather == "snow":
                    rain_tipping_list.append("❄️ -> ")
                elif type_of_weather == "sun":
                    rain_tipping_list.append("🌞 -> ")
                elif type_of_weather == "love":
                    rain_tipping_list.append("❤️ -> ")
                for active_user_id in last_active_users_list:
                    active_user = User.get_user(task_name=task_name, account_id=active_user_id)
                    if active_user is None:
                        active_user = User.create_user(task_name=task_name, user=User(account_id=active_user_id, user_name=active_user_id, first_name="", last_name="", balance=0))
                    active_user.balance = active_user.balance + amount_per_reddhead
                    User.update_user(task_name=task_name, user=active_user)
                    UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=issuer_user.user_name, address="", amount=amount_per_reddhead, balance=issuer_user.balance, tx_type="rain_send", tx_id=uuid.uuid1(), affected_user_name=active_user.user_name, create_date=datetime.utcnow()))
                    UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=active_user.user_name, address="", amount=amount_per_reddhead, balance=active_user.balance - amount_per_reddhead, tx_type="rain_receive", tx_id=uuid.uuid1(), affected_user_name=issuer_user.user_name, create_date=datetime.utcnow()))
                # update user balances in database
                issuer_user.balance = issuer_user.balance - (amount_per_reddhead * len(last_active_users_list))
                User.update_user(task_name=task_name, user=issuer_user)
                # UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(account_id=issuer_user.account_id, address="", amount=amount, balance=issuer_user.balance + amount, tx_type="rain", tx_id=uuid.uuid1(), receiver_account_id="", create_date=datetime.utcnow()))
            elif len(rain_msg) == 0:
                rain_msg = "Sorry, no active users to tip for with last activity within {} hours.".format(str(activity))
        finally:
            DbMySQL.end_tx(task_name=task_name)
    util.send_text_msg(update, context, rain_msg)


# Send a tip to another Telegram user
# Command: /tip @<username> <amount>
# Command: /tip randomHead <amount> <hours of last activity>
# Command: /tip brokeHead <amount> <hours of last activity>
def tip(update, context, send_tip_msg=True):
    telegram_user = util.get_telegram_user_data(update)
    check_user(telegram_user)
    user_input_list = util.get_user_input(update, context, telegram_user)
    target = ""
    amount = 0
    tip_msg = ""
    if len(user_input_list) > 1 and not DbRedis.is_user_on_banned_list(telegram_user.id):
        if not util.is_numeric(user_input_list[0]):
            target = user_input_list[0]
        elif not util.is_numeric(user_input_list[1]):
            target = user_input_list[1]
        if util.is_numeric(user_input_list[0]):
            amount = Decimal(user_input_list[0])
        elif util.is_numeric(user_input_list[1]):
            amount = Decimal(user_input_list[1])
        if len(user_input_list) == 3 and util.is_numeric(user_input_list[2]):
            tip_randomhead_brokehead_activity_hours = float(user_input_list[2])
        else:
            tip_randomhead_brokehead_activity_hours = config.tip_randomhead_brokehead_default_activity_hours
        if target == config.bot_name:
            tip_msg = "HODL."
        elif target.startswith("@"):
            tip_msg = tip_target_user(telegram_user.id, target, amount)
        elif target.lower() == "randomhead" or target.lower() == "brokehead":
            last_active_users_list = active_user_list(telegram_user.id, telegram_user.chat_id, telegram_user.msg_date, tip_randomhead_brokehead_activity_hours)
            util.logger.info("tip - last_active_users_list: %s", last_active_users_list)
            if target.lower() == "randomhead":
                if len(last_active_users_list) > 1:
                    active_user_account_id = random.choice(last_active_users_list)
                    tip_msg = tip_target_user(telegram_user.id, active_user_account_id, amount)
                else:
                    tip_msg = "Sorry @{}, but there are no randomHeads with recent activity since {} hours.".format(telegram_user.username, util.format_number(tip_randomhead_brokehead_activity_hours))
            if target.lower() == "brokehead":
                random.shuffle(last_active_users_list)
                for active_user_account_id in last_active_users_list:
                    task_name = DbMySQL.start_tx()
                    try:
                        active_user = User.get_user(task_name=task_name, account_id=active_user_account_id)
                    finally:
                        DbMySQL.end_tx(task_name=task_name)
                    if active_user.balance < config.tip_brokehead_balance_threshold:
                        util.logger.info("source_user_id: " + str(telegram_user.id))
                        util.logger.info("target_user_id_or_username: " + str(active_user.account_id))
                        util.logger.info("amount: " + str(amount))
                        tip_msg = tip_target_user(telegram_user.id, active_user.account_id, amount)
                        break
                if tip_msg == "":
                    tip_msg = "Sorry @{}, but there are no brokeHeads with recent activity since {} hours.".format(telegram_user.username, util.format_number(tip_randomhead_brokehead_activity_hours))
        else:
            tip_msg = "Error that user is not applicable. Need help? -> /help"
        if send_tip_msg:
            util.send_text_msg(update, context, tip_msg)


def tip_target_user(source_user_id, target_user_id_or_username, amount):
    task_name = DbMySQL.start_tx()
    try:
        util.logger.info("source_user_id: " + str(source_user_id))
        util.logger.info("target_user_id_or_username: " + str(target_user_id_or_username))
        source_user = User.get_user(task_name=task_name, account_id=source_user_id)
        if str(target_user_id_or_username).startswith("@"):
            target_user = User.get_user_by_user_name(task_name=task_name, user_name=target_user_id_or_username[1:])
        else:
            target_user = User.get_user(task_name=task_name, account_id=target_user_id_or_username)
        if source_user.balance < amount:
            tip_msg = "Hey @{}, you have insufficient funds.".format(source_user.user_name)
        elif source_user_id == target_user.account_id:
            tip_msg = "You can't tip yourself silly."
        elif amount > 0:
            if target_user is not None:
                source_user.balance = source_user.balance - amount
                target_user.balance = target_user.balance + amount
                User.update_user(task_name=task_name, user=source_user)
                User.update_user(task_name=task_name, user=target_user)
                UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=source_user.user_name, address="", amount=amount, balance=source_user.balance + amount, tx_type="tip_send", tx_id=uuid.uuid1(), affected_user_name=target_user.user_name, create_date=datetime.utcnow()))
                UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=target_user.user_name, address="", amount=amount, balance=target_user.balance - amount, tx_type="tip_receive", tx_id=uuid.uuid1(), affected_user_name=source_user.user_name, create_date=datetime.utcnow()))
                tip_msg = "@{} tipped @{} of Ɍ<code>{}</code>".format(source_user.user_name, target_user.user_name, amount)
            else:
                tip_msg = "Sorry but I was not able to find user {} in Reddbot database 😔".format(target_user_id_or_username)
        else:
            tip_msg = "I see what you did there! 😏"
    finally:
        DbMySQL.end_tx(task_name=task_name)
    return tip_msg


def moon(update: Update, context: CallbackContext):
    moon_msg = "Moon mission inbound!"
    util.send_animation_msg(update, context, config.reddcoin_rocket_ani, moon_msg)


def newwebsite(update: Update, context: CallbackContext):
    util.send_text_msg(update, context, "🎉🎉🎉 https://reddcoin.com 🎉🎉🎉")


def newwallet(update: Update, context: CallbackContext):
    util.send_text_msg(update, context, "🎉🎉🎉 https://github.com/reddcoin-project/reddcoin/releases 🎉🎉🎉")


def check_user(telegram_user: TelegramUser):
    task_name = DbMySQL.start_tx()
    try:
        user_by_account_id = User.get_user(task_name=task_name, account_id=telegram_user.id)
        user_by_user_name = User.get_user_by_user_name(task_name=task_name, user_name=telegram_user.username)
        if user_by_account_id is None and user_by_user_name is None:
            user = User.create_user(task_name=task_name, user=User(account_id=telegram_user.id, user_name=telegram_user.username, first_name=telegram_user.first_name, last_name=telegram_user.last_name, balance=0))
        elif user_by_account_id is not None and user_by_user_name is None:
            user = User.update_user(task_name=task_name, user=User(account_id=telegram_user.id, user_name=telegram_user.username, first_name=telegram_user.first_name, last_name=telegram_user.last_name, balance=user_by_account_id.balance))
        else:
            user = User.update_user(task_name=task_name, user=User(account_id=telegram_user.id, user_name=telegram_user.username, first_name=telegram_user.first_name, last_name=telegram_user.last_name, balance=user_by_user_name.balance))
    finally:
        DbMySQL.end_tx(task_name=task_name)
    return user


if __name__ == '__main__':
    main()
