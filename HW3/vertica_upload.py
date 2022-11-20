import sqlalchemy as sa
import pandas as pd

connect_vc = {'host': 'localhost',
              'port': 5433,
              'user': 'dbadmin',
              'database': 'Vmart'
             }


def vertica_connect(host, port, user, password='', database=''):
    return sa.create_engine(f'vertica+vertica_python://{user}:{password}@{host}:{port}/{database}')


print('Reading csv\'s...')
orders_df = pd.read_csv('csv/orders.csv')
users_df = pd.read_csv('csv/users.csv')
split_info_df = pd.read_csv('csv/split_info.csv')
split_users_df = pd.read_csv('csv/split_users.csv')

print('Transforming df\'s to csv\'s ')
orders_df = orders_df.to_csv(header=False, index=False, sep=',')
users_df = users_df.to_csv(header=False, index=False, sep=',')
split_info_df = split_info_df.to_csv(header=False, index=False, sep=',')
split_users_df = split_users_df.to_csv(header=False, index=False, sep=',')

print('Connecting to vertica...')
with vertica_connect(**connect_vc).raw_connection().cursor() as v_cursor:
    print('Creating schema...')
    v_cursor.execute('create schema split_service;')
    print('Creating tables...')
    v_cursor.execute("""create table split_service.split_users(
                        user_id int,
                        split_id int,
                        split_group int
                    );""")
    v_cursor.execute("""create table split_service.split_info(
                        id int,
                        name varchar(64)
                    );""")
    v_cursor.execute("""create table split_service.users (
                        id int,
                        email varchar(64),
                        reg_dt timestamp
                    );""")
    v_cursor.execute("""create table split_service.orders (
                        user_id int,
                        gross_usd float,
                        net_usd float,
                        dt timestamp,
                        type int
                    );""")
    print('Inserting data...')
    v_cursor.copy(f"COPY split_service.users FROM stdin DELIMITER ','", users_df)
    v_cursor.copy(f"COPY split_service.orders FROM stdin DELIMITER ','", orders_df)
    v_cursor.copy(f"COPY split_service.split_info FROM stdin DELIMITER ','", split_info_df)
    v_cursor.copy(f"COPY split_service.split_users FROM stdin DELIMITER ','", split_users_df)