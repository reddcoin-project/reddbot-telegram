#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author: Oliver Webb
"""

import json
from datetime import datetime


class AppData:
    def __init__(self, last_processed_block):
        self.last_processed_block = last_processed_block


class MarketData:
    def __init__(self, rdd_price_usd, price_change_percentage_24h, rdd_market_cap_btc, rdd_market_cap_usd):
        self.rdd_price_usd = float(rdd_price_usd)
        self.price_change_percentage_24h = price_change_percentage_24h
        self.rdd_market_cap_btc = float(rdd_market_cap_btc)
        self.rdd_market_cap_usd = float(rdd_market_cap_usd)
        self.timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")


class BlockchainData:
    def __init__(self, last_block_height, rdd_being_staked, max_supply, posv_v2_multiplier):
        self.last_block_height = float(last_block_height)
        self.rdd_being_staked = float(rdd_being_staked)
        self.max_supply = float(max_supply)
        self.posv_v2_multiplier = float(posv_v2_multiplier)
        self.blockchain_data_timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")


class StakeData:
    def __init__(self, number_of_stakes, total_stake_amount):
        self.number_of_stakes = float(number_of_stakes)
        self.total_stake_amount = float(total_stake_amount)


class TelegramUser:
    def __init__(self, id, username, first_name, last_name, chat_id, chat_type, msg_text, msg_date):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.msg_text = msg_text
        self.msg_date = msg_date


class UserActivity:
    # JSON format: account_id = {'chat_id': telegram_chat_id, 'date': msg_date}
    def __init__(self, user_json):
        self.user_json = json.loads(user_json)


class StakeTx:
    def __init__(self, id, date, amount):
        self.id = id
        self.date = date
        self.amount = amount
