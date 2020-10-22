#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 01.07.2019
@author: owebb
'''

from config import *
from util import *
from json_io import *
from telegram import ParseMode
from datetime import datetime

## Incoming transactions from users need to be tracked by moving transferred Reddcoins from users account to main account for staking support + adding to balance in json users file
def check_deposit_tx():
    account_list = accounts_wallet_cli_call(["listaccounts"])
    accounts_json = json.loads(account_list)
    db_user_balances_attribute_list = []
    #logger.info("check_deposit_transactions: accounts_json: %s", accounts_json)

    for deposit_wallet_account_user_username, deposit_wallet_account_user_balance in accounts_json.items():
        if len(deposit_wallet_account_user_username) > 0 and is_not_on_exclude_list(deposit_wallet_account_user_username) and deposit_wallet_account_user_balance > 0.0:
            db_user_balance = get_balance_from_user(deposit_wallet_account_user_username)
            new_balance = deposit_wallet_account_user_balance + db_user_balance
            logger.info("check_deposit_transactions: User: %s with balance: %s", deposit_wallet_account_user_username, deposit_wallet_account_user_balance)
            #user_balance -= tx_fee
            #logger.info("check_deposit_transactions: Deducting %s from balance: %s", tx_fee, user_balance)
            tx_id = accounts_wallet_cli_call(["sendfrom", deposit_wallet_account_user_username, staking_wallet_address, str(deposit_wallet_account_user_balance)])
            if len(tx_id) == 64:
                db_user_balances_attribute_list.append((new_balance, deposit_wallet_account_user_username))
                logger.info("check_deposit_transactions: User id: %s - User balance: %s - Tx msg: %s", deposit_wallet_account_user_username, deposit_wallet_account_user_balance, tx_id)
                deposit_wallet_account_user_balance_leftovers = accounts_wallet_cli_call(["getbalance", deposit_wallet_account_user_username])
                if float(deposit_wallet_account_user_balance_leftovers) > 0.0:
                    accounts_wallet_cli_call(["move", deposit_wallet_account_user_username, "", deposit_wallet_account_user_balance_leftovers])
            else:
                logger.error("Something went wrong! User id: %s - User balance: %s - Tx msg: %s", deposit_wallet_account_user_username, deposit_wallet_account_user_balance, tx_id)
    if len(db_user_balances_attribute_list) > 0:
        bulk_update_balance_from_user(db_user_balances_attribute_list)

## For a successful stake from main account Reddcoins are distributed to all other accounts according to their balance
def check_stake_tx(bot):
    tx_ids_from_staking_wallet = rpc_connect("listtransactions", ["*", 99999])
    staking_tx_json = read_staking_tx_list()
    staking_users_json = read_users_stake_rewards_list()
    stake_transactions_msg = []
    total_stake_amount = 0
    tx_list = []
    #logger.info("check_stake_transactions: listtransactions: %s", tx_ids_from_staking_wallet)
    for tx in tx_ids_from_staking_wallet['result']:
        if tx['category'] == 'stake' and tx['txid'] not in staking_tx_json:
            tx_list.append(tx['txid'])
            total_stake_amount += tx['amount']
            staking_tx_json[tx['txid']] = tx['amount']
            logger.info("check_stake_transactions - txid and amount: %s %s", tx['txid'], tx['amount'])
    if total_stake_amount > 0:
        users_balance = 0.0
        all_user_balances = get_all_user_balance_entries()
        user_balances_attribute_list = []
        #logger.info("check_stake_transactions - get_all_user_balance_entries: %s", result)
        for entry in all_user_balances:
            users_balance += entry[1]
        for entry in all_user_balances:
            user_username = entry[0]
            user_balance = entry[1]
            if user_balance > 0.0:
                current_balance = user_balance
                stake_proportion = get_decimal(OP_MUL, (user_balance / users_balance) * total_stake_amount)
                new_balance = current_balance + stake_proportion
                user_balances_attribute_list.append((new_balance, user_username))
                datetime_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                if user_username not in staking_users_json:
                    staking_users_json[user_username] = [{'txid': ' '.join(tx_list), 'balance': current_balance, 'date': datetime_utc, 'stake': stake_proportion}]
                else:
                    if len(staking_users_json[user_username]) >= 10:
                        del staking_users_json[user_username][1]
                    staking_users_json[user_username].append({'txid': ' '.join(tx_list), 'balance': current_balance, 'date': datetime_utc, 'stake': stake_proportion})
        #logger.info("check_stake_transactions - user_balances_attribute_list: %s", user_balances_attribute_list)
        bulk_update_balance_from_user(user_balances_attribute_list)

        stake_transactions_msg.append("What a great day, ɌeddHeads! Today our Tipbot has received {} stake rewards with a total of Ɍ<code>{}</code> and if you have some ɌDD in your Telegram wallet you just got some Ɍeddcoins credited 🤑\n\n".format(len(tx_list), total_stake_amount))
        stake_transactions_msg.append("Check out how much you got by sending /mystakes as a private message to {} -> Otherwise bot will directly reply here with a list of your latest stake rewards including your balance.".format(bot_name))
        stake_transactions_msg = ''.join(stake_transactions_msg)
        bot.send_message(chat_id=reddcoin_chat_id_en, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        bot.send_message(chat_id=reddcoin_chat_id_ko, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        bot.send_message(chat_id=reddcoin_chat_id_nl, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        bot.send_message(chat_id=reddcoin_chat_id_de, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        bot.send_message(chat_id=reddcoin_chat_id_tr, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        #bot.send_message(chat_id=reddcoin_chat_id_v3test, text=stake_transactions_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        write_staking_tx_list(staking_tx_json)
        write_users_stake_rewards_list(staking_users_json)
