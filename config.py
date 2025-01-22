#!/usr/bin/python
# -*- coding: utf-8 -*-

encoding = "utf-8"
app_name = "Reddcoin Telegram Tipbot"
app_version = "v4.0"

bot_name = None
bot_token = None

db_mysql_host = "localhost"
db_mysql_port = 3306
db_mysql_name = "reddbotv4"
db_mysql_user = "root"
db_mysql_password = ""
db_sql_stdout_debug = False

db_redis_host = "localhost"
db_redis_port = 6379
db_redis_db = 0
db_redis_decode_responses = True

reddcoin_cli = "reddcoin-cli"
walletpassphrase = None

rain_default_activity_hours = 3
tip_randomhead_brokehead_default_activity_hours = 72
tip_brokehead_balance_threshold = 100

fetch_limit_deposits = 20
fetch_limit_withdrawals = 20
fetch_limit_autowithdrawals = 20
fetch_limit_stake_rewards = 20
fetch_limit_tips = 20

admin_list = ["TechAdept", "CryptoGnasher", "cryptoBUZE"]

market_data_origin = "https://api.coingecko.com/api/v3/coins/reddcoin?localization=false&tickers=false&community_data=false&developer_data=false"
xeggex_api_rdd_usdt_price = "https://api.xeggex.com/api/v2/market/getbysymbol/RDD_USDT"

qrcode_home = "qr/"
qrcode_logo_img = qrcode_home + "rdd_qrcode_logo.png"
qrcode_prefix = "reddcoin:"
animation_home = "animation/"
reddcoin_rocket_ani = animation_home + "reddcoin_rocket.mp4"
posv_v2_dev_fund_address = "Rmhzj2GptZxkKBMqbUL6VjFcX8npDneAXR"
donation_address = "Recrcq8moZjbEHVoJx6JiQ2mfZkQnktvnf"
crowdfund_address = "RqQ4qnJCAcqxPqsvMtyJx73eyVyWtpjN73"

user_activity_json = "user_activity"
datetime_format = "%Y%m%d-%H%M%S"

reddcoin_chat_id_en = "-1001128694035"
reddcoin_chat_id_nl = "-1001209536624"
reddcoin_chat_id_ko = "-1001354363757"
reddcoin_chat_id_de = "-1001394562204"
reddcoin_chat_id_tr = "-1001474224927"

scheduler_active = True
