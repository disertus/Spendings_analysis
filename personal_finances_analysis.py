import config as cfg
import pandas as pd
import plotly.graph_objects as go
import requests
import time

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache


# todo: replace current visualization method with add_trace
# todo: add percentage view for the daily spending visualization
# todo: connect a database for retrieved data collection
# todo: build visualisations with plotly package
# todo: add telebot notifications
# todo: transform into a web-app with Flask/Dash, deploy


class UserData:

    def __init__(self, auth_token: str, account: str, username: str):
        self.account = account
        self.balance = 'balance'
        self.name = username
        self.spending_source = 'description'
        self.spending_amount = 'amount'
        self.spending_time = 'time'
        self.token = auth_token

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
            df_dict[self.spending_amount].append(int(item[self.spending_amount]) / 100)
            df_dict[self.spending_time].append(datetime.utcfromtimestamp(item[self.spending_time]))
            df_dict[self.balance].append(item[self.balance])
        return df_dict

    def dict_to_dataframe(self):
        """Transfers the data from json into a Dataframe"""

        dataframe = pd.DataFrame.from_dict(self.parsed_json_to_dict())
        dataframe['name'] = self.name
        return dataframe


class FamilyBudget:

    def __init__(self, *df):
        self.dataframes = df

    def concat_dataframes(self):
        return pd.concat(self.dataframes)


class Analyzer:

    def __init__(self, dataset: pd.DataFrame):
        self.dataset = dataset

    def sum_by_source(self):
        """Calculates the sum by spending source"""

        amount_sum_by_source = self.dataset.groupby(['source', 'name']).sum()
        return amount_sum_by_source.sort_values(by=['amount'], ascending=False).reset_index()

    def spending_vs_balance_by_date(self):
        """Spending distribution by date"""
        amount_sum_by_date = self.dataset
        amount_sum_by_date['time'] = self.dataset['time'].dt.round(freq='D')
        return amount_sum_by_date.reset_index()

    def sum_by_hour(self):
        """Spending distribution by hour of day"""

        amount_sum_by_hour = self.dataset.groupby(self.dataset['time'].dt.hour).sum()
        return amount_sum_by_hour


class Visualizer:

    def __init__(self, dataset):
        self.data = dataset

    def show_bar_chart(self, x_coord, y_coord, grouping=None, chart_name=None):
        fig = go.Figure([go.Bar(name=chart_name,
                                x=self.data[x_coord],
                                y=self.data[y_coord])])
        fig.update_layout(barmode='relative')
        return fig.show()

    def show_family_budget(self, x_coord, y_coord):

        #use the add_trace method through a loop for a list of dataframes (delete this function)
        fig = go.Figure([go.Bar(name=user1.name,
                                x=self.data.query('name == @user1.name')[x_coord],
                                y=self.data.query('name == @user1.name')[y_coord]),
                         go.Bar(name=user2.name,
                                x=self.data.query('name == @user2.name')[x_coord],
                                y=self.data.query('name == @user2.name')[y_coord])])
        #fig.update_layout(barmode='relative')
        return fig.show()


if __name__ == '__main__':
    user1 = UserData(cfg.token1, cfg.account1, 'roman')
    user2 = UserData(cfg.token2, cfg.account2, 'nika')
    analysis1 = Analyzer(user1.dict_to_dataframe())
    analysis2 = Analyzer(user2.dict_to_dataframe())
    viz1 = Visualizer(analysis1.spending_vs_balance_by_date())
    viz2 = Visualizer(analysis2.spending_vs_balance_by_date())

    viz1.show_bar_chart('time', 'amount')
    viz2.show_bar_chart('time', 'amount')

    print(f'\n{analysis1.spending_vs_balance_by_date()}')
    print(f'by hour \n{analysis1.sum_by_hour()}')

    family_spendings = FamilyBudget(user1.dict_to_dataframe(), user2.dict_to_dataframe()).concat_dataframes()
    print(family_spendings.head(50))
    print(family_spendings.tail(50))
    print(Analyzer(family_spendings).sum_by_source())
    print(Analyzer(family_spendings).spending_vs_balance_by_date())

    Visualizer(Analyzer(family_spendings).spending_vs_balance_by_date()).show_family_budget('time', 'amount')

    # temporary gipsy solution for data saving instead of a database
    # user1.dict_to_dataframe().to_csv('user1_11_15.csv', index=False)
    # user2.dict_to_dataframe().to_csv('user2_11_15.csv', index=False)
