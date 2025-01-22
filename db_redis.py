#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author: Oliver Webb
"""

import json
import config
import redis
import util
from datetime import datetime
from cached_data import AppData
from cached_data import MarketData
from cached_data import BlockchainData
from cached_data import StakeData
from cached_data import UserActivity


class DbRedis:
    # global application scope
    redis_conn = redis.StrictRedis(host=config.db_redis_host, port=config.db_redis_port, db=config.db_redis_db, decode_responses=config.db_redis_decode_responses)

    @classmethod
    def get_app_data(cls) -> AppData:
        last_processed_block = cls.redis_conn.get("last_processed_block")
        return AppData(last_processed_block)

    @classmethod
    def update_app_data(cls, app_data: AppData):
        util.logger.info("app_data.last_processed_block: %s", str(app_data.last_processed_block))
        cls.redis_conn.set("last_processed_block", app_data.last_processed_block)

    @classmethod
    def get_market_data_info(cls) -> MarketData:
        rdd_price_usd = cls.redis_conn.get("rdd_price_usd")
        price_change_percentage_24h = cls.redis_conn.get("price_change_percentage_24h")
        rdd_market_cap_btc = cls.redis_conn.get("rdd_market_cap_btc")
        rdd_market_cap_usd = cls.redis_conn.get("rdd_market_cap_usd")
        return MarketData(rdd_price_usd, price_change_percentage_24h, rdd_market_cap_btc, rdd_market_cap_usd)

    @classmethod
    def update_market_data(cls, market_data: MarketData):
        cls.redis_conn.set("status", "ok")
        cls.redis_conn.set("rdd_price_usd", market_data.rdd_price_usd)
        cls.redis_conn.set("price_change_percentage_24h", market_data.price_change_percentage_24h)
        cls.redis_conn.set("rdd_market_cap_btc", market_data.rdd_market_cap_btc)
        cls.redis_conn.set("rdd_market_cap_usd", market_data.rdd_market_cap_usd)
        cls.redis_conn.set("market_data_timestamp", datetime.utcnow().strftime("%Y%m%d-%H%M%S"))

    @classmethod
    def get_blockchain_data(cls) -> BlockchainData:
        last_block_height = cls.redis_conn.get("last_block_height")
        rdd_being_staked = cls.redis_conn.get("rdd_being_staked")
        max_supply = cls.redis_conn.get("max_supply")
        posv_v2_multiplier = cls.redis_conn.get("posv_v2_multiplier")
        return BlockchainData(last_block_height, rdd_being_staked, max_supply, posv_v2_multiplier)

    @classmethod
    def update_blockchain_data(cls, blockchain_data: BlockchainData):
        cls.redis_conn.set("last_block_height", blockchain_data.last_block_height)
        cls.redis_conn.set("rdd_being_staked", blockchain_data.rdd_being_staked)
        cls.redis_conn.set("max_supply", blockchain_data.max_supply)
        cls.redis_conn.set("posv_v2_multiplier", blockchain_data.posv_v2_multiplier)
        cls.redis_conn.set("blockchain_data_timestamp", datetime.utcnow().strftime(config.datetime_format))

    @classmethod
    def get_stake_data(cls) -> StakeData:
        number_of_stakes = cls.redis_conn.get("number_of_stakes")
        total_stake_amount = cls.redis_conn.get("total_stake_amount")
        return StakeData(number_of_stakes, total_stake_amount)

    @classmethod
    def update_stake_data(cls, stake_data: StakeData):
        cls.redis_conn.set("number_of_stakes", stake_data.number_of_stakes)
        cls.redis_conn.set("total_stake_amount", stake_data.total_stake_amount)

    @classmethod
    def get_user_activity(cls) -> UserActivity:
        user_json = cls.redis_conn.get(config.user_activity_json)
        return UserActivity(user_json)

    @classmethod
    def update_user_activity(cls, account_id, chat_id, msg_date):
        msg_date = msg_date.timestamp()
        #if msg_date is not None and not isinstance(msg_date, str):
        #    msg_date = msg_date.timestamp()
        #else:
        #    msg_date = datetime.utcnow().timestamp()
        if not cls.redis_conn.exists(config.user_activity_json):
            users_activity_json = json.loads("{}")
        else:
            users_activity_json = json.loads(cls.redis_conn.get(config.user_activity_json))
        if account_id not in users_activity_json:
            users_activity_json[account_id] = [{'chat_id': chat_id, 'date': msg_date}]
            cls.redis_conn.set(config.user_activity_json, json.dumps(users_activity_json))
            return True
        else:
            found_existing_entry = False
            for users_group_activity in users_activity_json[account_id]:
                if users_group_activity['chat_id'] == chat_id:
                    users_group_activity['date'] = msg_date
                    found_existing_entry = True
            if not found_existing_entry:
                users_activity_json[account_id].append({'chat_id': chat_id, 'date': msg_date})
            cls.redis_conn.set(config.user_activity_json, json.dumps(users_activity_json))
            return False

    @classmethod
    def add_user_to_banned_list(cls, account_id):
        return cls.redis_conn.sadd("banned_user_list", account_id)

    @classmethod
    def remove_user_from_banned_list(cls, account_id):
        return cls.redis_conn.srem("banned_user_list", account_id)

    @classmethod
    def is_user_on_banned_list(cls, account_id):
        return cls.redis_conn.sismember("banned_user_list", account_id)

    @classmethod
    def add_address_to_known_list(cls, address):
        return cls.redis_conn.sadd("known_address_list", address)

    @classmethod
    def remove_address_from_known_list(cls, address):
        return cls.redis_conn.srem("known_address_list", address)

    @classmethod
    def get_all_addresses_of_known_list(cls):
        return cls.redis_conn.smembers("known_address_list")

    @classmethod
    def backup_db_to_disk(cls):
        cls.redis_conn.save()
