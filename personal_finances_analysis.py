import config as cfg
import pandas as pd
import requests

from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache


# todo: cache the function retrieving data from monobank's endpoint
# todo: build a class for user differentiation
# todo: connect a database for retrieved data collection
# todo: build visualisations with plotly package
# todo: add telebot notifications
# todo: transform into a web-app with Flask/Dash, deploy


class User:

    def __init__(self, auth_token):
        self.token = auth_token

    @lru_cache(maxsize=128)  # cache the request result for repetitive usage
    def retrieve_user_bank_data(self):
        from_date = round((datetime.today() - timedelta(days=30)).timestamp())
        response_currencies = requests.get('https://api.monobank.ua/bank/currency')
        response_personal = requests.get('https://api.monobank.ua/personal/client-info',
                                         headers={'X-Token': self.token})
        response_statement = requests.get(f'https://api.monobank.ua/personal/statement/{cfg.account}/{from_date}',
                                          headers={'X-Token': self.token})
        return response_statement.json(), response_personal, response_currencies

    def json_to_dataframe(self):
        """Transfers the data from json into a Dataframe"""

        dataset = self.retrieve_user_bank_data()[0]
        df_dict = defaultdict(list)
        for item in dataset:
            df_dict['source'].append(item['description'])
            df_dict['amount'].append(item['amount'])
            df_dict['time'].append(datetime.utcfromtimestamp(item['time']))
            df_dict['balance'].append(item['balance'])
            df_dict['cashbackAmount'].append(item['cashbackAmount'])
        return pd.DataFrame.from_dict(df_dict)


class Analyzer:

    def __init__(self, dataset):
        self.dataset = dataset

    def sum_by_source(self):
        """Calculates the sum by spending source"""

        amount_sum_by_source = self.dataset.groupby(['source']).sum()
        return amount_sum_by_source['amount'].sort_values(ascending=False) / 100

    def spending_vs_balance_by_date(self):
        """Spending distribution by date"""

        amount_sum_by_date = self.dataset.groupby(self.dataset['time'].dt.round(freq='D')).sum()
        return amount_sum_by_date['amount'] / 100

    def sum_by_hour(self):
        """Spending distribution by hour of day"""

        amount_sum_by_hour = self.dataset.groupby(self.dataset['time'].dt.hour).sum()
        return amount_sum_by_hour['amount'] / 100

    def sum_by_user_and_date(self):
        """Spending by user and date of transaction (for a stacked bar chart)"""

        self.dataset.update(self.dataset['time'].dt.round(freq='D'))
        pass


user1 = User(cfg.token)
analysis = Analyzer(user1.json_to_dataframe())

print(user1.json_to_dataframe())
print(analysis.sum_by_source())
print(f'\n{analysis.spending_vs_balance_by_date()}')
print(f'\n{analysis.sum_by_hour()}')

# currencies_dict = {'978': 'Euro',
#                    '643': 'Ruble',
#                    '840': 'Dollar',
#                    '985': 'Zloty'}
