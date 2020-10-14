import config as cfg
import pandas as pd
import requests

from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache


# todo: cached function retrieving data from monobank's endpoint
# todo: build a class for user differentiation
# todo: connect a database for retrieved data collection
# todo: build visualisations with plotly package
# todo: add telebot notifications


@lru_cache(maxsize=128)     # cache the request result
def retrieve_bank_data():
    from_date = round((datetime.today() - timedelta(days=30)).timestamp())
    response_currencies = requests.get('https://api.monobank.ua/bank/currency')
    response_personal = requests.get('https://api.monobank.ua/personal/client-info',
                                     headers={'X-Token': cfg.token})
    response_statement = requests.get(f'https://api.monobank.ua/personal/statement/{cfg.account}/{from_date}',
                                      headers={'X-Token': cfg.token})
    return response_statement.json(), response_personal, response_currencies


def json_to_dataframe(dataset):
    """Transfers the data from json into a Dataframe"""

    df_dict = defaultdict(list)
    for item in dataset:
        df_dict['source'].append(item['description'])
        df_dict['amount'].append(item['amount'])
        df_dict['time'].append(datetime.utcfromtimestamp(item['time']))
        df_dict['balance'].append(item['balance'])
        df_dict['cashbackAmount'].append(item['cashbackAmount'])
    return pd.DataFrame.from_dict(df_dict)


def sum_by_source(dataset):
    """Calculates the sum by spending source"""

    amount_sum_by_source = dataset.groupby(['source']).sum()
    return amount_sum_by_source['amount'].sort_values(ascending=False) / 100


def sum_by_date(dataset):
    """Spending distribution by date"""

    dataset.update(dataset['time'].dt.round(freq='D'))
    amount_sum_by_date = dataset.groupby(['time']).sum()
    return amount_sum_by_date['amount'] / 100


def sum_by_hour(dataset):
    """Spending distribution by hour of day"""

    amount_sum_by_hour = dataset.groupby(dataset['time'].dt.hour).sum()
    return amount_sum_by_hour['amount'] / 100


def sum_by_user_and_date(dataset_u1, dataset_u2=None):
    """Spending by user and date of transaction"""

    dataset_u1.update(dataset_u1['time'].dt.round(freq='D'))
    dataset_u2.update(dataset_u2['time'].dt.round(freq='D'))
    pass


print(sum_by_source(json_to_dataframe(retrieve_bank_data()[0])))
print(f'\n{sum_by_date(json_to_dataframe(retrieve_bank_data()[0]))}')
print(f'\n{sum_by_hour(json_to_dataframe(retrieve_bank_data()[0]))}')

# currencies_dict = {'978': 'Euro',
#                    '643': 'Ruble',
#                    '840': 'Dollar',
#                    '985': 'Zloty'}
