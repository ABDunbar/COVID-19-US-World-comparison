import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from urllib.request import urlretrieve
plt.style.use('seaborn')


def data_from_url(url, csv_file):
    urlretrieve(url, csv_file)
    dataframe = pd.read_csv(csv_file)
    return dataframe

def get_states_from_counties(county_list):
    states_list = []
    for i in range(len(county_list)):
        if county_list[i][0] in states_list:
            continue
        else:
            states_list.append(county_list[i][0])
    return states_list


# Define URLs
URL_us_pop = 'http://www2.census.gov/programs-surveys/popest/datasets/2010-2019/national/totals/nst-est2019-alldata.csv'
URL_who = 'https://covid19.who.int/WHO-COVID-19-global-table-data.csv'
URL_ecdc = 'https://opendata.ecdc.europa.eu/covid19/casedistribution/csv/data.csv'

def load_data():
    # Returns a DataFrame
    
    # Load from URLs
    us_pop = data_from_url(URL_us_pop, 'us_all_pop.csv')
    who = data_from_url(URL_who, 'WHO_global_covid.csv')
    # ecdc = data_from_url(URL_ecdc, 'ecdc_covid.csv')
    ecdc = pd.read_csv('ecdc_covid.csv')

    # Load from csv
    cov_us_deaths = pd.read_csv('CONVENIENT_us_deaths.csv', header=[0,1], parse_dates=True, index_col=0)
    cov_us_cases = pd.read_csv('CONVENIENT_us_confirmed_cases.csv', header=[0,1], parse_dates=True, index_col=0)

    # Edit DataFrames
    us_pop = us_pop[['NAME', 'CENSUS2010POP', 'POPESTIMATE2019', 'DEATHS2019']]
    us_pop.set_index('NAME', inplace=True)
    who = who[['Name', 'Cases - cumulative total', 'Cases - cumulative total per 1 million population',
               'Deaths - cumulative total', 'Deaths - cumulative total per 1 million population']]
    who.set_index('Name', inplace=True)
    ecdc = ecdc.groupby('countriesAndTerritories').max()
    ecdc = ecdc[['countryterritoryCode', 'popData2019', 'continentExp']]
    ecdc = ecdc.dropna()

    # Merge WHO and ECDC data
    who_ecdc_comb = who.merge(ecdc, left_index=True, right_index=True)

    who_ecdc_comb = who_ecdc_comb[['continentExp', 'popData2019',
                                      'Cases - cumulative total',
                                      'Deaths - cumulative total',
                                      'Cases - cumulative total per 1 million population',
                                      'Deaths - cumulative total per 1 million population']]

    # Process US data
    counties_deaths = cov_us_deaths.columns
    counties_cases = cov_us_cases.columns
    states_deaths = get_states_from_counties(counties_deaths)
    states_cases = get_states_from_counties(counties_cases)
    cov_us_comb = {}
    for state in states_deaths:
        cov_us_comb[state] = [cov_us_cases[state].sum().sum(), cov_us_deaths[state].sum().sum()]

    # Dictionary to DataFrame
    cov_us_combined = pd.DataFrame(cov_us_comb, index=['Cases - cumulative total', 'Deaths - cumulative total']).T
    # Merge US population with COVID-19 cases/deaths
    us_cov_pop_comb = us_pop.merge(cov_us_combined, left_index=True, right_index=True)
    # Feature Engineering US data to match GLOBAL data 
    us_cov_pop_comb['continentExp'] = 'US State'
    us_cov_pop_comb['Cases - cumulative total per 1 million population'] = us_cov_pop_comb['Cases - cumulative total'] / (us_cov_pop_comb['POPESTIMATE2019'] / 1000000)
    us_cov_pop_comb['Deaths - cumulative total per 1 million population'] = us_cov_pop_comb['Deaths - cumulative total'] / (us_cov_pop_comb['POPESTIMATE2019'] / 1000000)
    us_cov_pop_comb = us_cov_pop_comb.rename(columns={"POPESTIMATE2019": 'popData2019', 'DEATHS2019': 'Deaths - 2019'})
    us_cov_pop_comb = us_cov_pop_comb[['continentExp', 'popData2019',
                                      'Cases - cumulative total',
                                      'Deaths - cumulative total',
                                      'Cases - cumulative total per 1 million population',
                                      'Deaths - cumulative total per 1 million population']
                                     ]
    # FINAL COMBINED, MERGED, APPENDED DATAFRAME
    df = us_cov_pop_comb.append(who_ecdc_comb, sort=True)
    
    return df