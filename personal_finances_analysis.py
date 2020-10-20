import config as cfg
import pandas as pd
import plotly.graph_objects as go
import requests
import time

from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache


# todo: add the possibility to join data of several users into a single dataset for analysis purposes
# todo: add user identifiers for spending events
# todo: add the possibility to create stacked charts with up to 6? distinct users' data
# todo: connect a database for retrieved data collection
# todo: build visualisations with plotly package
# todo: add telebot notifications
# todo: transform into a web-app with Flask/Dash, deploy


class UserData:

    def __init__(self, auth_token: str, account: str):
        self.token = auth_token
        self.account = account
        self.spending_source = 'description'
        self.spending_amount = 'amount'
        self.spending_time = 'time'
        self.balance = 'balance'

    @lru_cache(maxsize=64)  # cache the request result for repetitive usage
    def form_get_request(self):
        from_date = round((datetime.today() - timedelta(days=30)).timestamp())
        response_statement = requests.get(f'https://api.monobank.ua/personal/statement/{self.account}/{from_date}',
                                          headers={'X-Token': self.token})
        return response_statement

    def send_get_request(self):
        try:
            request_result = self.form_get_request()
        except:
            print("Failed to establish connection with bank's endpoint. \nRetrying...")
            time.sleep(5)
            self.send_get_request()
        return request_result

    def parsed_json_to_dict(self) -> dict:
        raw_data = self.send_get_request().json()
        df_dict = defaultdict(list)
        for item in raw_data:
            df_dict['source'].append(item[self.spending_source])
            df_dict[self.spending_amount].append(item[self.spending_amount])
            df_dict[self.spending_time].append(datetime.utcfromtimestamp(item[self.spending_time]))
            df_dict[self.balance].append(item[self.balance])
        return df_dict

    def dict_to_dataframe(self):
        """Transfers the data from json into a Dataframe"""

        return pd.DataFrame.from_dict(self.parsed_json_to_dict())


class Analyzer:

    def __init__(self, dataset: pd.DataFrame):
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


class Visualizer:

    def __init__(self, dataset):
        self.data = dataset

    def show_bar_chart(self, chart_name=None):
        fig = go.Figure([go.Bar(name=chart_name,
                                x=self.data.index,
                                y=self.data)],
                        layout={"hovermode": "x"})
        return fig.show()


if __name__ == '__main__':

    user1 = UserData(cfg.token1, cfg.account1)
    user2 = UserData(cfg.token2, cfg.account2)
    analysis1 = Analyzer(user1.dict_to_dataframe())
    analysis2 = Analyzer(user2.dict_to_dataframe())
    viz1 = Visualizer(analysis1.spending_vs_balance_by_date())
    viz2 = Visualizer(analysis2.spending_vs_balance_by_date())

    #viz1.show_bar_chart('Spendings1')
    #viz2.show_bar_chart('Spendings2')

    print(user1.dict_to_dataframe())
    print(analysis1.sum_by_source())
    print(f'\n{analysis1.spending_vs_balance_by_date()}')
    print(f'\n{analysis1.sum_by_hour()}')

    user1.dict_to_dataframe().to_csv('user1_10_21.csv', index=False)
    user2.dict_to_dataframe().to_csv('user2_10_21.csv', index=False)
