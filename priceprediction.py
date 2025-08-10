import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import calendar
from datetime import date
import warnings


class PriceForecast:
    def __init__(self):
        self.past_data = pd.read_csv('/content/data/Nat_Gas.csv')
        self.past_data['Dates'] = pd.to_datetime(self.past_data['Dates'], format='%m/%d/%y')
        self.past_data['Year'] = self.past_data['Dates'].dt.year
        self.past_data['Month'] = self.past_data['Dates'].dt.month
        self.final_df = self.past_data

    def price_prediction(self, input_date):
        day, month, year = map(int, input_date.split("/"))
        whole_year_list = []
        last_days = []

        for i in range(1, 13):
            # creating a list containing last of each month of a year
            last_day = calendar.monthrange(year, i)[1]
            last_days.append(date(year, i, last_day))

            # Predicting price for the given year
            x = np.array(self.past_data[self.past_data['Month'] == i]['Year']).reshape((-1, 1))
            y = np.array(self.past_data[self.past_data['Month'] == i]['Prices'])

            model = LinearRegression().fit(x, y)
            predicted_price = round(float(model.predict([[year]])), 2)
            whole_year_list.append(predicted_price)

        projected_price = pd.DataFrame({'Dates': last_days, 'Prices': whole_year_list})
        projected_price['Dates'] = pd.to_datetime(projected_price['Dates'], format='%m/%d/%y')
        projected_price['Year'] = projected_price['Dates'].dt.year
        projected_price['Month'] = projected_price['Dates'].dt.month

        final_df = pd.concat([self.past_data, projected_price], ignore_index=True)
        final_df = final_df.sort_values(by='Dates')
        estimated_price = projected_price[(projected_price['Year'] == year) & (projected_price['Month'] == month)]
        return estimated_price['Prices'].iloc[0]

    def predict_margin_price(self, inj_dates, wtdhr_dates):
        self.past_data.set_index('Dates', inplace=True)

        # Gas Prices at the time of injection
        inj_prices = [float(self.price_prediction(inj_date)) for inj_date in inj_dates]  # price of gas/litre
        # print(inj_prices)

        # Gas Prices at the time of withdrawl
        wtdhr_prices = [float(self.price_prediction(witr_date)) for witr_date in wtdhr_dates]  # price of gas/litre
        # print(wtdhr_prices)

        # Constant Costs
        injection_rate_cost = 0.01  # 10000/1million litre. 0.01/litre
        withdrawal_rate_cost = 0.01  # $ 0.01/litre
        transp_cost = 50000  # $
        max_inventory = 1500000  # BTU total
        storage_cost_monthly = 100000  # $

        # Total injection and withdrawl cost assuming injecting and withdrawing full storage - 90000 (inj_dates and withdrawl dates are 3)
        planned_injection_cost = injection_rate_cost * max_inventory * len(inj_dates)
        planned_withdrawal_cost = withdrawal_rate_cost * max_inventory * len(wtdhr_dates)

        # Margin = planned_Withdrawal - planned_injection

        storage_time = 0
        for i in range(len(inj_dates)):
            storage_time += (len(pd.date_range(start=inj_dates[i], end=wtdhr_dates[i], freq='M')) - 1)

        total_storage_cost = storage_time * storage_cost_monthly

        total_buying_price, total_selling_price = 0, 0
        for i in range(len(inj_prices)):
            total_buying_price += inj_prices[i] * max_inventory
            total_selling_price += wtdhr_prices[i] * max_inventory

        # Value of the contract
        net_margin = total_selling_price - (
                    total_buying_price + planned_injection_cost + planned_withdrawal_cost + (transp_cost * 2))
        return net_margin


if __name__ == '__main__':
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    # from datetime import date
    # input_date = input("Enter the date in mm/dd/yyyy format: ")
    # estimated_price = PriceForecast().price_prediction(input_date)
    # # print(future_price)

    # try:
    #   print(f"Estimated price for {input_date}: {estimated_price}")
    # except:
    #   print("Invalid Input or no data available for the given date.")
    inj_dates = ['30/03/2024', '31/03/2025', '31/05/2026']
    wtdhr_dates = ['30/11/2024', '31/10/2025', '30/11/2026']
    print(f"Net Profit: {PriceForecast().predict_margin_price(inj_dates, wtdhr_dates)}")
