#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author: Oliver Webb
"""

import config
from db_mysql import DbMySQL


class UserTransactions:
    def __init__(self, user_name, address, amount, balance, tx_type, tx_id, affected_user_name, create_date):
        self.user_name = user_name
        self.address = address
        self.amount = amount
        self.balance = balance
        self.tx_type = tx_type
        self.tx_id = tx_id
        self.affected_user_name = affected_user_name
        self.create_date = create_date

    @staticmethod
    def get_tx_id_list(task_name, tx_type):
        select_stmt = "SELECT DISTINCT tx_id FROM users_transactions WHERE tx_type = '{}'".format(tx_type)
        return DbMySQL.execute(query=select_stmt, task_name=task_name)

    @staticmethod
    def get_tx_list_by_type(task_name, *tx_types):
        where_condition = "WHERE "
        operator = ""
        if len(tx_types) > 1:
            where_condition += "("
            operator = " OR "
        for tx_type in tx_types:
            where_condition += "tx_type = '{}'{}".format(tx_type, operator)
        if operator == " OR ":
            where_condition = where_condition[:-4]
            where_condition += ") "
        else:
            where_condition += " "
        order_by = "ORDER BY create_date DESC"
        select_stmt = "SELECT * FROM users_transactions {}{}".format(where_condition, order_by)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        result_list = []
        for entry in result:
            result_list.append(UserTransactions(user_name=entry[1], address=entry[2], amount=entry[3], balance=entry[4], tx_type=entry[5], tx_id=entry[6], affected_user_name=entry[7], create_date=entry[8]))
        return result_list

    @staticmethod
    def get_tx_id_list_by_type(task_name, *tx_types):
        where_condition = "WHERE "
        operator = ""
        if len(tx_types) > 1:
            where_condition += "("
            operator = " OR "
        for tx_type in tx_types:
            where_condition += "tx_type = '{}'{}".format(tx_type, operator)
        if operator == " OR ":
            where_condition = where_condition[:-4]
            where_condition += ") "
        else:
            where_condition += " "
        order_by = "ORDER BY create_date DESC"
        select_stmt = "SELECT tx_id FROM users_transactions {}{}".format(where_condition, order_by)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        return result

    @staticmethod
    def get_number_of_stakes(task_name):
        tx_type = "stake"
        select_stmt = "SELECT COUNT(DISTINCT tx_id) FROM users_transactions WHERE tx_type = '{}'".format(tx_type)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        if len(result) == 1:
            return result[0]
        else:
            return result

    @staticmethod
    def get_total_stake_amount(task_name):
        tx_type = "stake"
        select_stmt = "SELECT SUM(DISTINCT amount) FROM users_transactions WHERE tx_type = '{}'".format(tx_type)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        if result[0] is not None:
            return result[0]
        else:
            return 0

    @staticmethod
    def get_stake_rewards_by_user(task_name, user_name):
        tx_type = "stake"
        fetch_limit = config.fetch_limit_stake_rewards
        select_stmt = "SELECT * FROM users_transactions WHERE user_name = '{}' AND tx_type = '{}' ORDER BY create_date DESC LIMIT {}".format(user_name, tx_type, fetch_limit)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        result_list = []
        for entry in result:
            result_list.append(UserTransactions(user_name=entry[1], address=entry[2], amount=entry[3], balance=entry[4], tx_type=entry[5], tx_id=entry[6], affected_user_name=entry[7], create_date=entry[8]))
        return result_list

    @staticmethod
    def get_tips_by_user(task_name, user_name):
        tx_type_1 = "tip_send"
        tx_type_2 = "tip_receive"
        tx_type_3 = "rain_send"
        tx_type_4 = "rain_receive"
        fetch_limit = config.fetch_limit_tips
        select_stmt = "SELECT * FROM users_transactions WHERE user_name = '{}' AND (tx_type = '{}' or tx_type = '{}' or tx_type = '{}' or tx_type = '{}') ORDER BY create_date DESC LIMIT {}".format(user_name, tx_type_1, tx_type_2, tx_type_3, tx_type_4, fetch_limit)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        result_list = []
        for entry in result:
            result_list.append(UserTransactions(user_name=entry[1], address=entry[2], amount=entry[3], balance=entry[4], tx_type=entry[5], tx_id=entry[6], affected_user_name=entry[7], create_date=entry[8]))
        return result_list

    @staticmethod
    def get_deposits_by_user(task_name, user_name):
        tx_type = "receive"
        fetch_limit = config.fetch_limit_deposits
        select_stmt = "SELECT * FROM users_transactions WHERE user_name = '{}' AND tx_type = '{}' ORDER BY create_date DESC LIMIT {}".format(user_name, tx_type, fetch_limit)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        result_list = []
        for entry in result:
            result_list.append(UserTransactions(user_name=entry[1], address=entry[2], amount=entry[3], balance=entry[4], tx_type=entry[5], tx_id=entry[6], affected_user_name=entry[7], create_date=entry[8]))
        return result_list

    @staticmethod
    def get_withdrawals_by_user(task_name, user_name):
        tx_type = "send"
        fetch_limit = config.fetch_limit_withdrawals
        select_stmt = "SELECT * FROM users_transactions WHERE user_name = '{}' AND tx_type = '{}' ORDER BY create_date DESC LIMIT {}".format(user_name, tx_type, fetch_limit)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        result_list = []
        for entry in result:
            result_list.append(UserTransactions(user_name=entry[1], address=entry[2], amount=entry[3], balance=entry[4], tx_type=entry[5], tx_id=entry[6], affected_user_name=entry[7], create_date=entry[8]))
        return result_list

    @staticmethod
    def get_donations_by_user(task_name, user_name):
        tx_type = "donation"
        fetch_limit = config.fetch_limit_withdrawals
        select_stmt = "SELECT * FROM users_transactions WHERE user_name = '{}' AND tx_type = '{}' ORDER BY create_date DESC LIMIT {}".format(user_name, tx_type, fetch_limit)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        result_list = []
        for entry in result:
            result_list.append(UserTransactions(user_name=entry[1], address=entry[2], amount=entry[3], balance=entry[4], tx_type=entry[5], tx_id=entry[6], affected_user_name=entry[7], create_date=entry[8]))
        return result_list

    @staticmethod
    def get_autowithdrawals_by_user(task_name, user_name):
        tx_type = "autowithdrawal"
        fetch_limit = config.fetch_limit_autowithdrawals
        select_stmt = "SELECT * FROM users_transactions WHERE user_name = '{}' AND tx_type = '{}' ORDER BY create_date DESC LIMIT {}".format(user_name, tx_type, fetch_limit)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        result_list = []
        for entry in result:
            result_list.append(UserTransactions(user_name=entry[1], address=entry[2], amount=entry[3], balance=entry[4], tx_type=entry[5], tx_id=entry[6], affected_user_name=entry[7], create_date=entry[8]))
        return result_list

    @staticmethod
    def insert_tx(task_name, tx):
        insert_stmt = "INSERT INTO users_transactions (user_name, address, amount, balance, tx_type, tx_id, affected_user_name, create_date) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(tx.user_name, tx.address, tx.amount, tx.balance, tx.tx_type, tx.tx_id, tx.affected_user_name, tx.create_date)
        return DbMySQL.execute(query=insert_stmt, task_name=task_name)
