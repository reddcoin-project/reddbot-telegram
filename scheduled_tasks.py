#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author: Oliver Webb
"""

import config
import util
import requests
import uuid
from telegram.ext import Updater
from decimal import Decimal
from datetime import datetime
from db_redis import DbRedis
from db_mysql import DbMySQL
from cached_data import MarketData
from cached_data import BlockchainData
from cached_data import StakeData
from cached_data import AppData
from cached_data import StakeTx
from users_transactions import UserTransactions
from users_autowithdrawal import UserAutowithdrawal
from users import User


def fetch_market_data():
    util.logger.info("scheduled_tasks - fetch_market_data: try to connect to coingecko and xeggex api")
    coingecko_api_response = requests.get(config.market_data_origin).json()
    xeggex_api_price_response = requests.get(config.xeggex_api_rdd_usdt_price).json()
    price_usd = xeggex_api_price_response['lastPrice']
    price_change_percentage_24h = xeggex_api_price_response['changePercent'] + "%"
    rdd_market_cap_btc = coingecko_api_response['market_data']['market_cap']['btc']
    rdd_market_cap_usd = coingecko_api_response['market_data']['market_cap']['usd']
    DbRedis.update_market_data(MarketData(price_usd, price_change_percentage_24h, rdd_market_cap_btc, rdd_market_cap_usd))


def fetch_blockchain_data():
    util.logger.info("scheduled_tasks - fetch_blockchain_data...")
    last_block_height = util.reddcoin_wallet_cli_call(["getblockcount"])
    rdd_being_staked = util.reddcoin_wallet_cli_call(["getstakinginfo"])["netstakeweight"]
    max_supply = util.reddcoin_wallet_cli_call(["gettxoutsetinfo", "none"])["total_amount"]
    posv_v2_multiplier = util.get_posv_v2_multiplier()
    DbRedis.update_blockchain_data(BlockchainData(last_block_height, rdd_being_staked, max_supply, posv_v2_multiplier))
    if DbRedis.get_app_data().last_processed_block is None:
        DbRedis.update_app_data(AppData(last_processed_block=last_block_height))


# Incoming transactions from users need to be tracked by moving transferred Reddcoins from users account to main account for staking support
def check_deposit_transactions():
    start = int(float(DbRedis.get_app_data().last_processed_block))
    end = int(DbRedis.get_blockchain_data().last_block_height)
    listtransactions_output = util.reddcoin_wallet_cli_call(["listtransactions", "*", 100])

    task_name = DbMySQL.start_tx()
    try:
        tx_id_list_from_db = UserTransactions.get_tx_id_list_by_type(task_name, "receive")
        for tx in listtransactions_output:
            # noinspection PyTypeChecker
            tx_category = tx['category']
            if tx_category == 'receive':
                util.logger.info("--------tx category: receive")
                # noinspection PyTypeChecker
                tx_confirmations = tx['confirmations']
                # noinspection PyTypeChecker
                tx_txid = tx['txid']
                # noinspection PyTypeChecker
                if tx_confirmations > 0 and tx_txid not in tx_id_list_from_db:
                    # noinspection PyTypeChecker
                    tx_account = tx['label']
                    # noinspection PyTypeChecker
                    tx_address = tx['address']
                    # noinspection PyTypeChecker
                    tx_amount = tx['amount']
                    # noinspection PyTypeChecker
                    tx_time = datetime.utcfromtimestamp(tx['time'])
                    util.logger.info("tx_account: %s", tx_account)
                    util.logger.info("tx_address: %s", tx_address)
                    util.logger.info("tx_amount: %s", tx_amount)
                    if util.is_numeric(tx_account):
                        user = User.get_user(task_name=task_name, account_id=tx_account)
                    else:
                        user = User.get_user_by_user_name(task_name=task_name, user_name=tx_account)
                    if user is not None:
                        UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=user.user_name, address=tx_address, amount=tx_amount, balance=user.balance, tx_type=tx_category, tx_id=tx_txid, affected_user_name="", create_date=tx_time))
                        user.balance = user.balance + Decimal(tx_amount)
                        User.update_user(task_name=task_name, user=user)
                    else:
                        util.logger.warning("Deposit from the following Reddcoin Core Wallet account could not be mapped to Reddbot database: %s", tx_account)
    finally:
        DbMySQL.end_tx(task_name)


# For a successful stake from any stake wallet address Reddcoins are distributed to all receiving addresses according to their balance
def check_stake_transactions(updater: Updater):
    new_stake_rewards_list = get_list_of_new_stake_rewards()
    total_stake_amount = 0

    task_name = DbMySQL.start_tx()
    try:
        for stake_tx in new_stake_rewards_list:
            util.logger.info("Wallet stake tx: %s", stake_tx.id)
            util.logger.info("Wallet stake date: %s", str(stake_tx.date))
            util.logger.info("Wallet stake amount: %s", str(stake_tx.amount))
            total_stake_amount += stake_tx.amount
            UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=config.bot_name.strip("@"), address="", amount=stake_tx.amount, balance=0, tx_type="stake", tx_id=stake_tx.id, affected_user_name="", create_date=stake_tx.date))

        non_zero_list = User.get_users_with_non_zero_balance(task_name)
        total_balances = User.get_users_overall_balance(task_name)
        stake_tx = uuid.uuid1()
        for user in non_zero_list:
            stake_proportion = util.convert_decimal(user.balance / total_balances * total_stake_amount)
            if stake_proportion >= 0.00000001:
                UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=user.user_name, address="", amount=stake_proportion, balance=user.balance, tx_type="stake", tx_id=stake_tx, affected_user_name="", create_date=datetime.utcnow()))
                user.balance = user.balance + stake_proportion
                User.update_user(task_name=task_name, user=user)
    finally:
        DbMySQL.end_tx(task_name)

    if total_stake_amount > 0:
        stake_transactions_msg = []
        stake_transactions_msg.append("What a great day, ɌeddHeads! Our Tipbot has received some stake rewards with a total of Ɍ<code>{}</code> and if you have some ɌDD in your Telegram wallet you just got some Ɍeddcoins credited 🤑\n\n".format(util.convert_decimal(total_stake_amount)))
        stake_transactions_msg.append("Check out how much you got by sending /mystakes as a private message to {}".format(config.bot_name))
        stake_transactions_msg = ''.join(stake_transactions_msg)
        util.send_text_msg(update=updater, context=config.reddcoin_chat_id_en, msg=stake_transactions_msg)
        util.send_text_msg(update=updater, context=config.reddcoin_chat_id_nl, msg=stake_transactions_msg)
        util.send_text_msg(update=updater, context=config.reddcoin_chat_id_ko, msg=stake_transactions_msg)
        util.send_text_msg(update=updater, context=config.reddcoin_chat_id_de, msg=stake_transactions_msg)
        util.send_text_msg(update=updater, context=config.reddcoin_chat_id_tr, msg=stake_transactions_msg)

        task_name = DbMySQL.start_tx()
        try:
            number_of_stakes = UserTransactions.get_number_of_stakes(task_name=task_name)
            total_stake_amount = UserTransactions.get_total_stake_amount(task_name=task_name)
            DbRedis.update_stake_data(StakeData(number_of_stakes, total_stake_amount))
        finally:
            DbMySQL.end_tx(task_name)

    DbRedis.update_app_data(AppData(last_processed_block=DbRedis.get_blockchain_data().last_block_height))


# Check balance of users with active autowithdrawal
def check_autowithdrawal():
    task_name = DbMySQL.start_tx()
    try:
        autowithdrawal_list = UserAutowithdrawal.get_list(task_name=task_name)
        for entry in autowithdrawal_list:
            user = User.get_user(task_name=task_name, account_id=entry.account_id)
            if user.balance >= entry.threshold > 0:
                tx_id = util.reddcoin_wallet_cli_call(["sendtoaddress", entry.address, user.balance])
                if len(tx_id) == 64:
                    UserTransactions.insert_tx(task_name=task_name, tx=UserTransactions(user_name=user.user_name, address=entry.address, amount=user.balance, balance=user.balance, tx_type="autowithdrawal", tx_id=tx_id, affected_user_name="", create_date=datetime.utcnow()))
                    user.balance = 0
                    User.update_user(task_name=task_name, user=user)
    finally:
        DbMySQL.end_tx(task_name)


def get_list_of_new_stake_rewards():
    task_name = DbMySQL.start_tx()
    try:
        tx_id_list_from_db = UserTransactions.get_tx_id_list(task_name, "stake")
    finally:
        DbMySQL.end_tx(task_name)
    stake_rewards_dict = {}
    stake_rewards_list = []
    start = int(float(DbRedis.get_app_data().last_processed_block))
    end = int(DbRedis.get_blockchain_data().last_block_height)
    util.logger.info("---- start: %s", str(start))
    util.logger.info("---- end: %s", str(end))
    #listtransactions_output = util.reddcoin_wallet_cli_call(["listtransactions", "*", 1000 + (end - start) * 10])
    listtransactions_output = util.reddcoin_wallet_cli_call(["listtransactions", "*", 500])

    for entry in listtransactions_output:
        if entry['category'] == 'stake':
            util.logger.info("Processing tx id: %s", entry['txid'])
            if entry['txid'] not in tx_id_list_from_db:
                if entry['amount'] > 0 or entry['address'] == config.posv_v2_dev_fund_address:
                    stake_rewards_dict[entry['txid']] = util.convert_decimal(entry['amount'])
                    tx_id_list_from_db.append(entry['txid'])
            elif entry['txid'] in stake_rewards_dict:
                if entry['amount'] > 0 or entry['address'] == config.posv_v2_dev_fund_address:
                    amount_without_posv_v2_proportion = stake_rewards_dict[entry['txid']] + util.convert_decimal(entry['amount'])
                    stake_rewards_dict[entry['txid']] = amount_without_posv_v2_proportion
                    stake_rewards_list.append(StakeTx(id=entry['txid'], date=datetime.utcfromtimestamp(entry['time']), amount=amount_without_posv_v2_proportion))
    return stake_rewards_list
