#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author: Oliver Webb
"""

from db_mysql import DbMySQL


class User:
    def __init__(self, account_id, user_name, first_name, last_name, balance):
        self.account_id = account_id
        self.user_name = user_name
        self.first_name = first_name
        self.last_name = last_name
        self.balance = balance

    @staticmethod
    def get_user(task_name, account_id):
        select_stmt = "SELECT * FROM users WHERE account_id = '{}'".format(account_id)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        if len(result) == 1:
            return User(account_id=result[0][0], user_name=result[0][1], first_name=result[0][2], last_name=result[0][3], balance=result[0][4])
        else:
            return None

    @staticmethod
    def get_user_by_user_name(task_name, user_name):
#        if user_name is None:
#           user_name = ""
        select_stmt = "SELECT * FROM users WHERE user_name = '{}'".format(user_name)
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        if len(result) == 1:
            return User(account_id=result[0][0], user_name=result[0][1], first_name=result[0][2], last_name=result[0][3], balance=result[0][4])
        else:
            return None

    @staticmethod
    def get_number_of_users(task_name):
        select_stmt = "SELECT COUNT(*) FROM users WHERE balance > 0"
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        if result[0] is not None:
            return result[0]
        else:
            return 0

    @staticmethod
    def get_users_with_non_zero_balance(task_name):
        select_stmt = "SELECT * FROM users WHERE balance > 0"
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        users_list = []
        for entry in result:
            users_list.append(User(account_id=entry[0], user_name=entry[1], first_name=entry[2], last_name=entry[3], balance=entry[4]))
        return users_list

    @staticmethod
    def get_users_overall_balance(task_name):
        select_stmt = "SELECT SUM(balance) FROM users"
        result = DbMySQL.execute(query=select_stmt, task_name=task_name)
        if result[0] is not None:
            return result[0]
        else:
            return 0

    @staticmethod
    def create_user(task_name, user):
        insert_stmt = "INSERT INTO users (account_id, user_name, first_name, last_name, balance) VALUES ('{}', '{}', '{}', '{}', '{}')".format(user.account_id, user.user_name, user.first_name, user.last_name, user.balance)
        DbMySQL.execute(query=insert_stmt, task_name=task_name)
        return User(account_id=user.account_id, user_name=user.user_name, first_name=user.first_name, last_name=user.last_name, balance=user.balance)

    @staticmethod
    def update_user(task_name, user):
        # print("update_user user obj: " + str(user.__dict__))
        user_from_db = User.get_user(task_name=task_name, account_id=user.account_id)
        if user_from_db is not None:
            update_stmt = "UPDATE users SET user_name = '{}', first_name = '{}', last_name = '{}', balance = '{}' WHERE account_id = '{}'".format(user.user_name, user.first_name, user.last_name, user.balance, user.account_id)
        else:
            update_stmt = "UPDATE users SET account_id = '{}', first_name = '{}', last_name = '{}', balance = '{}' WHERE user_name = '{}'".format(user.account_id, user.first_name, user.last_name, user.balance, user.user_name)
        DbMySQL.execute(query=update_stmt, task_name=task_name)
        return User(account_id=user.account_id, user_name=user.user_name, first_name=user.first_name, last_name=user.last_name, balance=user.balance)
