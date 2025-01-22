#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author: Oliver Webb
"""

import config
import util
import time
from datetime import datetime
import inspect
from typing import List
import sqlalchemy
from sqlalchemy.orm import sessionmaker


class DbMySQL:
    # global application scope
    task_name = None
    tx_start_time = 0
    tx_end_time = 0
    session = sessionmaker()
    db_engine = sqlalchemy.create_engine("mysql+mysqlconnector://{}:{}@{}:{}/{}".format(config.db_mysql_user, config.db_mysql_password, config.db_mysql_host, config.db_mysql_port, config.db_mysql_name), echo=config.db_sql_stdout_debug)
    db_session = session(bind=db_engine.connect())
    util.logger.info("Database was initialized - db_session: %s", db_session)

    @classmethod
    def start_tx(cls):
        cls.tx_start_time = time.time()
        try:
            caller = inspect.stack()[2][3]
            if caller == "handle_update":
                #util.logger.info("inspect.stack(): %s", inspect.stack())
                caller = inspect.stack()[1][3]
        except IndexError:
            caller = "unknown"
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S.%f')
        task_name = caller + '__' + timestamp
        util.logger.info("Caller of start_tx: %s", task_name)

        while cls.db_session._transaction is not None:
            util.logger.info("Current tx %s not completed yet - need to wait a bit longer...", cls.task_name)
            time.sleep(0.1)
            if time.time() - cls.tx_start_time > 300:
                util.logger.warning("Current tx %s was not completed after %s seconds - cancelling tx...", cls.task_name, time.time() - cls.tx_start_time)
                cls.task_name = None
                cls.db_session.close()
                break

        cls.task_name = task_name
        cls.db_session.begin()
        util.logger.info("Transaction was started with task name: %s", task_name)
        return task_name

    @classmethod
    def rollback_tx(cls, task_name=None):
        if cls.task_name is None:
            util.logger.warning("Could not rollback tx - it was already ended or task_name was not set previously.")
        elif cls.task_name != task_name:
            util.logger.warning("Could not rollback tx - given task_name %s does not match the current running task: %s", task_name, cls.task_name)
        else:
            cls.db_session.rollback()
            util.logger.info("Transaction was rolled back for task: %s", task_name)

    @classmethod
    def end_tx(cls, task_name=None):
        if cls.task_name is None:
            util.logger.warning("Could not stop tx - it was already ended or task_name was not set previously.")
        elif cls.task_name != task_name:
            util.logger.warning("Could not stop tx - given task_name %s does not match the current running task: %s", task_name, cls.task_name)
        else:
            cls.task_name = None
            cls.db_session.commit()
            cls.db_session.close()
            cls.tx_end_time = time.time()
            util.logger.info("Transaction was ended for task: %s (took %s seconds)", task_name, cls.tx_end_time - cls.tx_start_time)

    @classmethod
    def execute(cls, query, task_name=None):
        if cls.task_name is not task_name or task_name is None:
            util.logger.info("cls.task_name: %s", cls.task_name)
            util.logger.info("task_name: %s", task_name)
            raise NameError(f'{cls.__class__.__name__}.task_name is invalid.')
        elif cls.db_session._transaction is not None:
            try:
                result = cls.__process_query(query)
                return result
            except:
                cls.rollback_tx(task_name=task_name)
                raise

    @classmethod
    def __process_query(cls, query):
        if isinstance(query, List):
            for query_entry in query:
                cls.db_session.execute(query_entry)
        elif query.startswith("SELECT"):
            result = cls.db_session.execute(query).fetchall()
            if len(result) > 0:
                if len(result[0].keys()) == 1:
                    result_list = []
                    for entry in result:
                        result_list.append(entry[0])
                    return result_list
                else:
                    return result
            else:
                return []
        else:
            cls.db_session.execute(query)
            return []

#    @classmethod
#    def __process_result(cls, result):
#        if result is not None and result.returns_rows:
#            result = result.fetchall()
#            result_list = []
#            if len(result) > 0:
#                if len(result[0].keys()) == 1:
#                    for entry in result:
#                        result_list.append(entry[0])
#                    return result_list
#                else:
#                    result
#            else:
#                return result
#        else:
#            return []
