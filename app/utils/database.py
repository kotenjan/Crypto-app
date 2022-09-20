from numpy import NaN
import psycopg2
from psycopg2 import sql
import pandas as pd
from utils.logger import Logger
from time import sleep
import os


# framework for communication with PostgreSQL
class Database:

    def __init__(self):
        self.logger = Logger()

    def sql_create_history_table(self, cursor, table):
        cursor.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    date TIMESTAMP PRIMARY KEY,
                    count NUMERIC
                )
                """
            ).format(
                table=sql.Identifier(table.lower())
            )
        )

    def sql_create_extremes_table(self, cursor, table):
        cursor.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    date TIMESTAMP PRIMARY KEY,
                    interval_1 NUMERIC,
                    crypto_1 NUMERIC,
                    crypto_15 NUMERIC,
                    crypto_60 NUMERIC,
                    crypto_240 NUMERIC,
                    gold_15 NUMERIC,
                    gold_60 NUMERIC,
                    gold_240 NUMERIC,
                    vix_15 NUMERIC,
                    vix_60 NUMERIC,
                    vix_240 NUMERIC,
                    sap_15 NUMERIC,
                    sap_60 NUMERIC,
                    sap_240 NUMERIC,
                    trend_15 NUMERIC,
                    trend_60 NUMERIC,
                    trend_240 NUMERIC,
                    interval_15 NUMERIC,
                    interval_60 NUMERIC,
                    interval_240 NUMERIC
                )
                """
            ).format(
                table=sql.Identifier(table.lower())
            )
        )

    def sql_create_prediction_table(self, cursor, table):
        cursor.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    name VARCHAR PRIMARY KEY,
                    symbol NUMERIC,
                    time_from TIMESTAMP,
                    time_to TIMESTAMP,
                    interval_from NUMERIC,
                    interval_to NUMERIC,
                    gain NUMERIC,
                    transformed_time NUMERIC,
                    transformed_gain NUMERIC
                )
                """
            ).format(
                table=sql.Identifier(table.lower())
            )
        )

    def sql_create_purchase_table(self, cursor, table):
        cursor.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    name VARCHAR PRIMARY KEY,
                    bought BOOLEAN,
                    value NUMERIC,
                    cash NUMERIC,
                    transactions NUMERIC
                )
                """
            ).format(
                table=sql.Identifier(table.lower())
            )
        )

    def sql_create_name_table(self, cursor, table):
        cursor.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    name VARCHAR PRIMARY KEY,
                    symbol NUMERIC
                )
                """
            ).format(
                table=sql.Identifier(table.lower())
            )
        )

    def sql_insert_into_history_table(self, cursor, table, date, count):
        cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table} (date, count) 
                VALUES(%s, %s)
                ON CONFLICT (date) 
                DO 
                    UPDATE SET count = EXCLUDED.count;
                """
            ).format(
                table=sql.Identifier(table.lower())
            ),
            [date, count]
        )

    def sql_insert_into_extremes_table(self, cursor, table, date, data):
        cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table} (
                    date, 
                    interval_1,
                    crypto_1,
                    crypto_15,
                    crypto_60,
                    crypto_240,
                    gold_15,
                    gold_60,
                    gold_240,
                    vix_15,
                    vix_60,
                    vix_240,
                    sap_15,
                    sap_60,
                    sap_240,
                    trend_15,
                    trend_60,
                    trend_240,
                    interval_15,
                    interval_60,
                    interval_240
                ) 
                VALUES(
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT (date) 
                DO 
                    UPDATE SET (
                        interval_1,
                        crypto_1,
                        crypto_15,
                        crypto_60,
                        crypto_240,
                        gold_15,
                        gold_60,
                        gold_240,
                        vix_15,
                        vix_60,
                        vix_240,
                        sap_15,
                        sap_60,
                        sap_240,
                        trend_15,
                        trend_60,
                        trend_240,
                        interval_15,
                        interval_60,
                        interval_240
                    ) = (
                        EXCLUDED.interval_1,
                        EXCLUDED.crypto_1,
                        EXCLUDED.crypto_15,
                        EXCLUDED.crypto_60,
                        EXCLUDED.crypto_240,
                        EXCLUDED.gold_15,
                        EXCLUDED.gold_60,
                        EXCLUDED.gold_240,
                        EXCLUDED.vix_15,
                        EXCLUDED.vix_60,
                        EXCLUDED.vix_240,
                        EXCLUDED.sap_15,
                        EXCLUDED.sap_60,
                        EXCLUDED.sap_240,
                        EXCLUDED.trend_15,
                        EXCLUDED.trend_60,
                        EXCLUDED.trend_240,
                        EXCLUDED.interval_15,
                        EXCLUDED.interval_60,
                        EXCLUDED.interval_240
                    );
                """
            ).format(
                table=sql.Identifier(table.lower())
            ),
            [date, *data]
        )

    def sql_insert_into_prediction_table(self, cursor, table, name, data):
        cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table} (
                    name, 
                    symbol,
                    time_from,
                    time_to,
                    interval_from,
                    interval_to,
                    gain,
                    transformed_time,
                    transformed_gain
                ) 
                VALUES(
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT (name) 
                DO 
                    UPDATE SET (
                        symbol,
                        time_from,
                        time_to,
                        interval_from,
                        interval_to,
                        gain,
                        transformed_time,
                        transformed_gain
                    ) = (
                        EXCLUDED.symbol,
                        EXCLUDED.time_from,
                        EXCLUDED.time_to,
                        EXCLUDED.interval_from,
                        EXCLUDED.interval_to,
                        EXCLUDED.gain,
                        EXCLUDED.transformed_time,
                        EXCLUDED.transformed_gain
                    );
                """
            ).format(
                table=sql.Identifier(table.lower())
            ),
            [name, *data]
        )

    def sql_insert_into_purchase_table(self, cursor, table, data):
        cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table} (
                    name,
                    bought,
                    value,
                    cash,
                    transactions
                ) 
                VALUES(
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT (name) 
                DO 
                    UPDATE SET (
                        bought,
                        value,
                        cash,
                        transactions
                    ) = (
                        EXCLUDED.bought,
                        EXCLUDED.value,
                        EXCLUDED.cash,
                        EXCLUDED.transactions
                    );
                """
            ).format(
                table=sql.Identifier(table.lower())
            ),
            data
        )

    def sql_insert_into_name_table(self, cursor, table, data):
        cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table} (
                    name,
                    symbol
                ) 
                VALUES(
                    %s,
                    %s
                )
                ON CONFLICT (name)
                DO
                    UPDATE SET symbol = EXCLUDED.symbol;
                """
            ).format(
                table=sql.Identifier(table.lower())
            ),
            data
        )

    def sql_select_all_from(self, cursor, table, order='date'):
        cursor.execute(
            sql.SQL(
                """
                SELECT *
                FROM {table}
                ORDER BY {order};
                """
            ).format(
                table=sql.Identifier(table.lower()),
                order=sql.Identifier(order)
            )
        )

    def sql_select_last_date(self, cursor, table):
        cursor.execute(
            sql.SQL(
                """
                SELECT date
                FROM {table}
                ORDER BY date DESC
                LIMIT 1;
                """
            ).format(
                table=sql.Identifier(table.lower())
            )
        )

    def sql_select_all_from_and_fill_missing_timestamp(self, cursor, table, order='date'):
        cursor.execute(
            sql.SQL(
                """
                SELECT dates.date AS date, {table}.count AS count
                FROM (
                    SELECT generate_series(min(date), now(), '1M')::timestamp AS date FROM {table}
                ) dates
                LEFT JOIN {table} USING (date)
                ORDER BY {order};
                """
            ).format(
                table=sql.Identifier(table.lower()),
                order=sql.Identifier(order)
            )
        )
    
    def sql_remove_from_name_table(self, cursor, table, data):
        cursor.execute(
            sql.SQL(
                """
                DELETE FROM {table}
                WHERE name = %s;
                """
            ).format(
                table=sql.Identifier(table.lower())
            ),
            data
        )

    def sql_remove_table(self, cursor, table):
        cursor.execute(
            sql.SQL(
                """
                DROP TABLE {table};
                """
            ).format(
                table=sql.Identifier(table.lower())
            )
        )

    def sql_select_version(self, cursor):
        cursor.execute(
            sql.SQL(
                """
                SELECT version();
                """
            )
        )

    def sql_clean(self, cursor):
        cursor.execute(
            sql.SQL(
                """
                DROP SCHEMA public CASCADE;
                CREATE SCHEMA public;
                GRANT ALL ON SCHEMA public TO postgres;
                GRANT ALL ON SCHEMA public TO public;
                """
            )
        )

    def test(self):
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_select_version(cursor)
                data = cursor.fetchone()
                self.logger.log(f'CONNECTED: {data}')
            self.close_connection(connection)
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN test: {str(e)}')
            self.close_connection(connection)

    def clean(self):
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_clean(cursor)
            self.logger.log('ALL DB TABLES REMOVED')
            self.close_connection(connection)
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN clean: {str(e)}')
            self.close_connection(connection)

    def get_connection(self):
        while True:
            try:
                return psycopg2.connect(user="postgres",
                                        password="postgres",
                                        host="database", # name of the docker container
                                        port="5432",
                                        database="postgres")
            except Exception as e:
                self.logger.log(f'POSTGRES EXCEPTION IN get_connection: {str(e)}')
                sleep(1)
                

    def close_connection(self, connection):
        try:
            connection.close()
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN close_connection: {str(e)}')

    def insert_into_history_table(self, type_name, dataframe):
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                for crypto_name in dataframe.columns:
                    name = f'{type_name}_{crypto_name}'
                    self.sql_create_history_table(cursor, name)
                    for row in pd.DataFrame(dataframe[crypto_name]).iterrows():
                        date = row[0]
                        count = float(row[1])
                        self.sql_insert_into_history_table(cursor, name, date, count)
            self.close_connection(connection)
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN insert_into_history_table: {str(e)}')
            self.close_connection(connection)

    def insert_into_extremes_table(self, crypto_name, data_type, dataframe):
        name = f"{data_type}_{crypto_name}"
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_create_extremes_table(cursor, name)
                for date, data in zip(dataframe.index, dataframe.values.tolist()):
                    self.sql_insert_into_extremes_table(cursor, name, date, data)
            self.close_connection(connection)
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN insert_into_extremes_table: {str(e)}')
            self.close_connection(connection)

    def insert_into_prediction_table(self, dataframe):
        table_name = "predictions_predictions"
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_create_prediction_table(cursor, table_name)
                for name, data in zip(dataframe.index, dataframe.values.tolist()):
                    self.sql_insert_into_prediction_table(cursor, table_name, name, data)
            self.close_connection(connection)
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN insert_into_prediction_table: {str(e)}')
            self.close_connection(connection)

    def insert_into_purchase_table(self, data):
        table_name = "purchases_purchases"
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_create_purchase_table(cursor, table_name)
                self.sql_insert_into_purchase_table(cursor, table_name, data)
            self.close_connection(connection)
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN insert_into_purchase_table: {str(e)}')
            self.close_connection(connection)

    def insert_into_name_table(self, name, symbol):
        print(name, symbol)
        table_name = "name_name"
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_create_name_table(cursor, table_name)
                self.sql_insert_into_name_table(cursor, table_name, [name.upper(), symbol])
            self.close_connection(connection)
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN insert_into_name_table: {str(e)}')
            self.close_connection(connection)

    def select_all_from(self, crypto_name, data_type, order='date', index='date'):
        name = f"{data_type}_{crypto_name}"
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_select_all_from(cursor, name, order)
                data = cursor.fetchall()
                names = [description.name for description in cursor.description]
                dataframe = pd.DataFrame(data, columns=names)
                dataframe = dataframe.set_index(index)
            self.close_connection(connection)
            return dataframe
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN select_all_from: {str(e)}')
            self.close_connection(connection)

    def select_last_date(self, crypto_name, type_name):
        name = f'{type_name}_{crypto_name}'
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_select_last_date(cursor, name)
                date = cursor.fetchone()
            self.close_connection(connection)
            if date:
                return date[0]
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN select_last_date: {str(e)}')
            self.close_connection(connection)
    
    # this method will fix missing and 0 values in dataset before returning it
    # it can limit the data by returning only the tail() and save the data in csv
    def select_all_from_and_fix_missing(self, crypto_name, data_type, method, order='date', replace_null=True, limit_area=None, save_to_csv=False, tail=None):
        name = f"{data_type}_{crypto_name}"
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_select_all_from_and_fill_missing_timestamp(cursor, name, order)
                data = cursor.fetchall()
                names = [description.name for description in cursor.description]
                dataframe = pd.DataFrame(data, columns=names)
                dataframe = dataframe.set_index('date')
                dataframe = dataframe.astype(float)
                if replace_null:
                    dataframe['count'] = dataframe['count'].replace(0, NaN)
                dataframe['count'] = dataframe['count'].interpolate(method=method, limit_area=limit_area)
                dataframe = dataframe.dropna()
            if save_to_csv:
                dataframe.to_csv(f'/workspace/data/{name.lower()}.csv')
            if tail:
                dataframe = dataframe.tail(tail)
            self.close_connection(connection)
            return dataframe
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN select_all_from_and_fix_missing: {str(e)}')
            self.close_connection(connection)

    def remove_from_name_table(self, name):
        table_name = "name_name"
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_create_name_table(cursor, table_name)
                self.sql_remove_from_name_table(cursor, table_name, [name.upper()])
            self.close_connection(connection)
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN insert_into_purchase_table: {str(e)}')
            self.close_connection(connection)

    def remove_table(self, name, type_name):
        table_name = f"{type_name}_{name}"
        try:
            connection = self.get_connection()
            with connection, connection.cursor() as cursor:
                self.sql_remove_table(cursor, table_name)
            self.close_connection(connection)
        except Exception as e:
            self.logger.log(f'POSTGRES EXCEPTION IN insert_into_purchase_table: {str(e)}')
            self.close_connection(connection)

    def get_names(self, symbols=False):
        names = self.select_all_from('name', 'name', 'name', 'name')
        if names is not None:
            if symbols:
                return zip(list(names.index), list(names['symbol']))
            return list(names.index)
        else:
            return list()


if __name__ == '__main__':
    db = Database()
    db.test()
    