#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 26.08.2019
@author: owebb
'''

from config import *
from util import *
import logging
import requests
import json
from lock_file import lock_file

## Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(name + "_" + version)

def rpc_connect(method, params):
    url = "http://" + staking_wallet_rpc_ip +":" + staking_wallet_rpc_port + "/"
    payload = json.dumps({"method": method, "params": params})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    try:
        response = requests.request("POST", url, data=payload, headers=headers, auth=(staking_wallet_rpc_user, staking_wallet_rpc_pw))
        #logger.info("rpc_connect - response: %s", response)
        if response.text.startswith("{"):
            return json.loads(response.text)
        else:
            return response.text
    except:
        logger.error("No response from server. Check if Reddcoin core (staking) wallet is running on " + staking_wallet_rpc_ip)

def read_staking_tx_list():
    return read_json_file(staking_tx_json_file)

def read_receive_tx_list():
    return read_json_file(receive_tx_json_file)

def write_staking_tx_list(json_obj):
    return write_json_file(staking_tx_json_file, json_obj)

def write_receive_tx_list(json_obj):
    return write_json_file(receive_tx_json_file, json_obj)

def read_users_stake_rewards_list():
    return read_json_file(users_stake_rewards_json_file)

def write_users_stake_rewards_list(json_obj):
    return write_json_file(users_stake_rewards_json_file, json_obj)

def read_users_tips_list():
    return read_json_file(users_tips_json_file)

def write_users_tips_list(json_obj):
    return write_json_file(users_tips_json_file, json_obj)

#def read_users_balances_list_():
#    return read_json_file(users_balances_json_file)

#def write_users_balances_list_(json_obj):
#    return write_json_file(users_balances_json_file, json_obj)

def read_users_activity_list():
    return read_json_file(users_activity_json_file)

def write_users_activity_list(json_obj):
    return write_json_file(users_activity_json_file, json_obj)

def read_donors_list():
    return read_json_file(donors_json_file)

def write_donors_list(json_obj):
    return write_json_file(donors_json_file, json_obj)

def read_json_file(filename):
    with lock_file(filename, "r") as file:
        json_obj = json.load(file)
        return json_obj

def write_json_file(filename, json_obj):
    try:
        with lock_file(filename, "w", timeout = 10) as file:
            json.dump(json_obj, file, indent = 4)
    except Exception:
        logger.error("Could not write json file");
