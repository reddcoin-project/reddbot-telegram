#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 26.08.2019
@author: owebb
'''

from config import *
from json_io import *
import util
#import logging
import mysql.connector

DB_CONN = ""
DB_USERS_BALANCES = "users_balances"
DB_USERS_BALANCES_TBL_USER_ID = "user_id"
DB_USERS_BALANCES_TBL_USER_BALANCE = "balance"
BALANCE_ADD = "add"
BALANCE_REMOVE = "remove"

## Enable logging
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#logger = logging.getLogger(name + "_" + version)

def connect_to_db():
    global DB_CONN
    try:
        logger.info("db_io - connect to db")
        DB_CONN = mysql.connector.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        if DB_CONN.is_connected():
            logger.info("db_io - connected to db")
    except Exception as error:
        logger.error("db_io - db connection failed!: %s", error)
    
def select_from_db(tbl_field_list, tbl_name, tbl_where_dict):
    if not DB_CONN.is_connected():
        connect_to_db()
    try:
        logger.info("select_from_db_ - tbl_field_list: %s", tbl_field_list)
        logger.info("select_from_db_ - tbl_name: %s", tbl_name)
        logger.info("select_from_db_ - tbl_where_dict: %s", tbl_where_dict)
        tbl_field_list = ", ".join(tbl_field_list)
        cursor = DB_CONN.cursor()
        if tbl_where_dict == None:
            select_statement = "SELECT {} FROM {}".format(tbl_field_list, tbl_name)
        else:
            where_clause_key = list(tbl_where_dict.keys())[0]
            where_clause_value = list(tbl_where_dict.values())[0]
            select_statement = "SELECT {} FROM {} WHERE {} = '{}'".format(tbl_field_list, tbl_name, where_clause_key, where_clause_value)
        logger.info("select_from_db_ - select_statement: %s", select_statement)
        cursor.execute(select_statement)
        result = cursor.fetchall()
        #logger.info("select_from_db_ - cursor.fetchall(): %s", result)
        logger.info("select_from_db_ - cursor.rowcount: %s", cursor.rowcount)
        #if cursor.rowcount != 1:
        #    result = None
    except Exception as error:
        raise error
    finally:
        cursor.close()
    return result

def insert_into_db(tbl_field_list, tbl_name, tbl_value_list):
    if not DB_CONN.is_connected():
        connect_to_db()
    try:
        logger.info("insert_into_db - tbl_field_list: %s", tbl_field_list)
        logger.info("insert_into_db - tbl_name: %s", tbl_name)
        logger.info("insert_into_db - tbl_value_list: %s", tbl_value_list)
        tbl_field_list = ", ".join(tbl_field_list)
        tbl_value_list_formatted = ""
        for value in tbl_value_list:
            tbl_value_list_formatted += "'" + str(value) + "', "
        tbl_value_list_formatted = tbl_value_list_formatted[:-2]
        cursor = DB_CONN.cursor()
        insert_statement = "INSERT INTO {}({}) VALUES ({})".format(tbl_name, tbl_field_list, tbl_value_list_formatted)
        logger.info("insert_into_db - insert_statement: %s", insert_statement)
        cursor.execute(insert_statement)
        DB_CONN.commit()
    except Exception as error:
        raise error
    finally:
        cursor.close()

def update_db(tbl_name, tbl_value_dict, tbl_where_dict):
    if not DB_CONN.is_connected():
        connect_to_db()
    try:
        logger.info("update_db - tbl_name: %s", tbl_name)
        logger.info("update_db - tbl_value_dict: %s", tbl_value_dict)
        logger.info("update_db - tbl_where_dict: %s", tbl_where_dict)
        update_key = list(tbl_value_dict.keys())[0]
        update_value = list(tbl_value_dict.values())[0]
        where_clause_key = list(tbl_where_dict.keys())[0]
        where_clause_value = list(tbl_where_dict.values())[0]
        cursor = DB_CONN.cursor()
        update_statement = "UPDATE {} SET {} = '{}' WHERE {} = '{}'".format(tbl_name, update_key, update_value, where_clause_key, where_clause_value)
        logger.info("update_db - update_statement: %s", update_statement)
        cursor.execute(update_statement)
        DB_CONN.commit()
    except Exception as error:
        raise error
    finally:
        cursor.close()

def bulk_update_db(table_name, table_update_column, table_where_column, records_to_update):    
    if not DB_CONN.is_connected():
        connect_to_db()
    try:
        logger.info("bulk_update_db - records_to_update: %s", records_to_update)
        cursor = DB_CONN.cursor()
        update_statement = "UPDATE {} SET {} = %s WHERE {} = %s".format(table_name, table_update_column, table_where_column)
        cursor.executemany(update_statement, records_to_update)
        DB_CONN.commit()
    except Exception as error:
        raise error
    finally:
        cursor.close()

def get_all_user_balance_entries():
    result = select_from_db([DB_USERS_BALANCES_TBL_USER_ID, DB_USERS_BALANCES_TBL_USER_BALANCE], DB_USERS_BALANCES, None)
    #logger.info("get_all_user_balance_entries - result: %s", result)
    return result

def get_number_of_users():
    result = select_from_db(["COUNT(" + DB_USERS_BALANCES_TBL_USER_ID + ")"], DB_USERS_BALANCES, None)
    return result[0][0]

def get_balance_from_user(user_username):
    result = select_from_db([DB_USERS_BALANCES_TBL_USER_BALANCE], DB_USERS_BALANCES, {DB_USERS_BALANCES_TBL_USER_ID: user_username})
    if result is None or len(result) == 0:
        add_new_user(user_username)
        result = 0
    else:
        result = result[0][0]
    return result

#def update_balance_from_user_(user_username, user_balance, update_type):
#    result = select_from_db([DB_USERS_BALANCES_TBL_USER_BALANCE], DB_USERS_BALANCES, {DB_USERS_BALANCES_TBL_USER_ID: user_username})
#    if result == None or len(result) == 0:
#        old_balance = 0
#        insert_into_db([DB_USERS_BALANCES_TBL_USER_ID, DB_USERS_BALANCES_TBL_USER_BALANCE], DB_USERS_BALANCES, [user_username, user_balance])
#    else:
#        old_balance = result[0][0]
#        if update_type == BALANCE_ADD:
#            new_balance = old_balance + user_balance
#        elif update_type == BALANCE_REMOVE:
#            new_balance = old_balance - user_balance
#        update_db(DB_USERS_BALANCES, {DB_USERS_BALANCES_TBL_USER_BALANCE: new_balance}, {DB_USERS_BALANCES_TBL_USER_ID: user_username})

def bulk_update_balance_from_user(bulk_update_list):
    #bulk_update_list = []
    #for user_attribute_list_entry in attribute_list:
        #user_user_id = user_attribute_list_entry[0]
        #user_balance = user_attribute_list_entry[1]
        #bulk_update_list.append((DB_USERS_BALANCES, DB_USERS_BALANCES_TBL_USER_BALANCE, user_balance, DB_USERS_BALANCES_TBL_USER_ID, user_user_id))
        #bulk_update_list.append((user_balance, user_user_id))
    bulk_update_db(DB_USERS_BALANCES, DB_USERS_BALANCES_TBL_USER_BALANCE, DB_USERS_BALANCES_TBL_USER_ID, bulk_update_list)

def add_new_user(user_username):
    result = select_from_db([DB_USERS_BALANCES_TBL_USER_BALANCE], DB_USERS_BALANCES, {DB_USERS_BALANCES_TBL_USER_ID: user_username})
    if result is None or len(result) == 0:
        insert_into_db([DB_USERS_BALANCES_TBL_USER_ID, DB_USERS_BALANCES_TBL_USER_BALANCE], DB_USERS_BALANCES, [user_username, 0])

#def export_user_balances_to_db(update, context):
#    users_json = read_users_balances_list_()
#    if not DB_CONN.is_connected():
#        connect_to_db()
#    else:
#        cursor = DB_CONN.cursor()
#        logger.info("export_user_balances_to_db - importing users_balances json flat file data into db")
#        for user_id, user_balance in users_json.items():
#            if util.is_not_on_exclude_list(user_id):
#                logger.info("export_user_balances_to_db - user_id: %s", user_id)
#                logger.info("export_user_balances_to_db - user_balance: %s", user_balance)
#                user_balance = util.get_decimal(util.OP_MUL, user_balance, 1)
#                cursor.execute("INSERT INTO users_balances (user_id, balance) VALUES ('{}', {})".format(user_id, user_balance))
#        logger.info("export_user_balances_to_db - commit to db")
#        DB_CONN.commit()
#        logger.info("export_user_balances_to_db - commited to db")
#        cursor.close()
