from flask import Flask, render_template, request
import pandas as pd
import vertica_python as vp
import numpy as np
from scipy.stats import norm

from helpers import make_nice_plot, make_nice_html_table

import warnings
warnings.filterwarnings("ignore")

connect_vc = {'host': 'localhost',
              'port': 5433,
              'user': 'dbadmin',
              'database': 'Vmart'
             }

conn_vc = vp.connect(**connect_vc)

app = Flask(__name__)


def get_metrics(split_id: int):
    query = f"""
        select split_group,
               count(distinct users.id) as registered_users,
               count(orders.user_id) as orders_count,
               count(distinct orders.user_id)/count(distinct users.id) as buyers_prcnt,
               sum(orders.gross_usd) as gross_usd,
               sum(orders.gross_usd)/count(distinct users.id) as arpu
        from split_service.users as users
        left join split_service.split_users su
            on su.user_id = users.id
        left join split_service.orders as orders
            on orders.user_id = users.id
        where split_id = {split_id}
        group by 1
        order by 1
    """

    df = pd.read_sql(query, conn_vc)
    html_table = make_nice_html_table(df)
    return html_table


def get_splits():
    query = f"""
            select id, name
            from split_service.split_info
        """

    splits = pd.read_sql(query, conn_vc)
    return splits.to_dict('records')


# TASK 1
def get_p_value(split_id: int):
    query = f"""
        select split_group,
        count(orders.user_id)/count(distinct users.id) as conversion_rate,
        count(distinct users.id) as users_number
        from split_service.users as users
            left join split_service.split_users su
                on su.user_id = users.id
            left join split_service.orders as orders
                on orders.user_id = users.id
        where split_id = {split_id}
        group by split_group
        order by 1
    """

    df = pd.read_sql(query, conn_vc)
    n1 = df.users_number[df.split_group == 0].values[0]
    n2 = df.users_number[df.split_group == 1].values[0]
    cr1 = df.conversion_rate[df.split_group == 0].values[0]
    cr2 = df.conversion_rate[df.split_group == 1].values[0]
    return _p_value(cr1, cr2, n1, n2)


def _p_value(cr1, cr2, n1, n2):
    se1 = np.sqrt(cr1 * (1 - cr1) / n1)
    se2 = np.sqrt(cr2 * (1 - cr2) / n2)
    z_score = (cr2 - cr1) / np.sqrt(se1**2 + se2**2)
    return 1 - norm.cdf(z_score)


# TASK 2
def get_min_sample_size(split_id: int, uplift, power=0.8, sig_level=0.05):
    query = f"""
        select split_group,
        count(orders.user_id)/count(distinct users.id) as conversion_rate
        from split_service.users as users
             left join split_service.split_users su
                on su.user_id = users.id
             left join split_service.orders as orders
                on orders.user_id = users.id
        where split_id = {split_id}
        group by split_group
        order by 1
    """

    df = pd.read_sql(query, conn_vc)
    cr = df.conversion_rate[df.split_group == 0].values[0]
    standard_norm = norm(0, 1)
    z_beta = standard_norm.ppf(power)
    z_alpha = standard_norm.ppf(1 - sig_level / 2)
    pooled_prob = (2 * cr + uplift) / 2
    min_n = (2 * pooled_prob * (1 - pooled_prob) * (z_beta + z_alpha)**2 / uplift**2)
    return np.ceil(min_n)


# TASK 3
def get_dates_p_value(split_id: int):
    query = f"""
        select cast(users.reg_dt as date) as dt, split_group,
        count(distinct users.id) as registered_users_count,
        count(orders.user_id) as orders_count
        from split_service.users as users
            left join split_service.split_users su
                on su.user_id = users.id
            left join split_service.orders as orders
                on orders.user_id = users.id
        where split_id = {split_id}
        group by cast(users.reg_dt as date), split_group
        order by cast(users.reg_dt as date)
    """

    df = pd.read_sql(query, conn_vc)
    df0 = df[df.split_group == 0]
    df1 = df[df.split_group == 1]
    df0.registered_users_count = np.cumsum(df0.registered_users_count.values)
    df0.orders_count = np.cumsum(df0.orders_count.values)
    df1.registered_users_count = np.cumsum(df1.registered_users_count.values)
    df1.orders_count = np.cumsum(df1.orders_count.values)
    n1 = df0.registered_users_count.values
    n2 = df1.registered_users_count.values
    cr1 = df0.orders_count.values / df0.registered_users_count.values
    cr2 = df1.orders_count.values / df1.registered_users_count.values
    return df0.dt.values, _p_value(cr1, cr2, n1, n2)


@app.route("/")
def main():

    split_id = request.args.get('split_id')
    splits = get_splits()

    if split_id is not None:
        split_id = int(split_id)
        metrics_table = get_metrics(split_id)
        p_value = get_p_value(split_id)
        expected_uplift = int(request.args.get('uplift')) / 100
        stat_power = int(request.args.get('power')) / 100
        min_sample_size = int(get_min_sample_size(split_id, expected_uplift, stat_power))
        dates, p_values = get_dates_p_value(split_id)
        p_value_plot = make_nice_plot(dates, p_values)

        return render_template('index.html',
                               splits=splits,
                               table=metrics_table,
                               split_id=int(split_id),
                               p_value=p_value,
                               min_sample_size=min_sample_size,
                               p_value_plot=p_value_plot
                               )

    return render_template('index.html', splits=splits, split_id=None)


app.run('localhost', port=7377)
