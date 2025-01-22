#!/usr/bin/python
# -*- coding: utf-8 -*-

from db_mysql import DbMySQL


class UserAutowithdrawal:
    def __init__(self, account_id, threshold, address):
        self.account_id = account_id
        self.threshold = threshold
        self.address = address

    @staticmethod
    def get(task_name, account_id):
        select_stmt = "SELECT * FROM users_autowithdrawals WHERE account_id = '{}'".format(account_id)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        if len(result) > 0:
            return UserAutowithdrawal(account_id=result[0][1], threshold=result[0][2], address=result[0][3])
        else:
            return UserAutowithdrawal(account_id=account_id, threshold=0, address=None)

    @staticmethod
    def get_list(task_name):
        select_stmt = "SELECT * FROM users_autowithdrawals"
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        result_list = []
        for entry in result:
            result_list.append(UserAutowithdrawal(account_id=entry[1], threshold=entry[2], address=entry[3]))
        return result_list

    @staticmethod
    def update(task_name, entry):
        update_stmt = "UPDATE users_autowithdrawals SET threshold = '{}', address = '{}' WHERE account_id = '{}'".format(entry.threshold, entry.address, entry.account_id)
        return DbMySQL.execute(query=update_stmt, task_name=task_name)

    @staticmethod
    def insert(task_name, entry):
        insert_stmt = "INSERT INTO users_autowithdrawals (account_id, threshold, address) VALUES ('{}', '{}', '{}')".format(entry.account_id, entry.threshold, entry.address)
        return DbMySQL.execute(query=insert_stmt, task_name=task_name)
