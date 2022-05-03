from full_fred.fred import Fred
from full_fred.categories import Categories
from full_fred.series import Series
import pandas as pd
import numpy as np
import json
import os
from os import path
from plotting_objects.objects import GraphUtility
from plotting_objects.objects import GraphDataObject
import datetime

import unicodedata
import string

valid_filename_chars = "-_() %s%s" % (string.ascii_letters, string.digits)
char_limit = 255

def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace spaces
    for r in replace:
        filename = filename.replace(r, '_')
    filename = filename.replace("%","_pct_")

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename) > char_limit:
        print(
            "Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
    return cleaned_filename[:char_limit]

categories = Categories()
categories.set_api_key_file('full_fred_key.txt')
category_dict = {}
categories_dict = {}
category_dict["categories"]=categories_dict
l_ids_rate_limited = []
inflation_file_name = "inflation_json.json"

def output_file():
    global category_dict
    global inflation_file_name
    with open(inflation_file_name, "w") as outfile:
        json.dump(category_dict, outfile, indent=4, sort_keys=True)

def get_category_detail(id):
    if id==1:
        return
    global categories
    global l_ids_rate_limited
    my_dict = categories.get_a_category(id)
    if my_dict is not None and "categories" in my_dict.keys():
        print(my_dict["categories"][0])
        category_dict["categories"][int(my_dict["categories"][0]["id"])] = my_dict["categories"][0]
        series = categories.get_series_in_a_category(id)
        if len(series.keys())>0:
            category_dict["categories"][int(my_dict["categories"][0]["id"])]["series"]=series
    else:
        print(my_dict)
    if "error_code" in my_dict.keys():
        if my_dict["error_message"] == "Too Many Requests.  Exceeded Rate Limit":
            l_ids_rate_limited.append(id)
        print(my_dict)

    if id % 30 == 0:
        output_file()

class FredSeriesObject:
    '''
    Poco object that holds information to be passed to graphing function.
    '''

    def __init__(self):
        self.series_dict = {}
        self.graph_label     = 'CPI and Median Income Jan 1984 through Jan 2021'
        self.x_axis_label    = 'Year'
        self.width   =   18
        self.height  =   6
        self.frequency="yearly"
        self.frequency_interval = 1
        self.dual_axis = True
        self.linewidth = 3.0

def do_fed_extract_and_graph_multi_series(fred_series_object):

    my_csv_directory = "inflation_file_series"
    my_directory = "inflation_excel_series"

    try:
        os.makedirs(my_csv_directory)
    except OSError as e:
        print(e)

    try:
        os.makedirs(my_directory)
    except OSError as e:
        print(e)


    l_excel_file_names = []
    l_csv_file_names = []
    output_dict = {}
    series = Series()
    series.set_api_key_file('full_fred_key.txt')
    for key in fred_series_object.series_dict.keys():
        key
        print(key)
        my_data_frame = series.get_series_df(key)
        # print(my_data_frame.dtypes)
        # dealio = input("dealio")
        excel_title = clean_filename(fred_series_object.series_dict[key]["filename"]) + "_" + key + ".xlsx"
        csv_title = excel_title.replace(".xlsx",".csv")
        file_name = path.join(os.path.abspath(os.getcwd()),my_directory,excel_title)
        file_name_csv = path.join( os.path.abspath(os.getcwd()), my_csv_directory, csv_title )
        print(file_name)
        output_dict[key]=file_name_csv
        with pd.ExcelWriter(file_name,engine='xlsxwriter') as writer:
            my_data_frame.to_excel(writer,sheet_name="Sheet1",freeze_panes=(1,0))
            # writer.save()
        with open(file_name_csv, "w") as outfile:
            my_data_frame.to_csv(outfile)
            l_csv_file_names.append(outfile)

        l_excel_file_names.append(excel_title)
        # print(my_data_frame)
        print(excel_title)

    with open("excel_file_names.txt","w") as outfile:
        for line in l_excel_file_names:
            outfile.write(line + "\n")


    # print(historic_fed_rate.columns)

    # date_time_str = '2018-06-29 08:15:27.243860'
    # date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d')

    list_of_graph_data_objects = []

    list_colors=['orangered','blue','darkolivegreen','crimson']

    color_index = 0
    for key in fred_series_object.series_dict.keys():
        # output_file()
        d = lambda x: pd.datetime.strptime(x, '%Y-%m-%d')
        series_1 = pd.read_csv(output_dict[key], index_col=False, parse_dates=['date'], date_parser=d)

        series_1["value"] = pd.to_numeric(series_1["value"] ,errors='coerce')

        my_graph_data_object = GraphDataObject()

        my_graph_data_object.linewidth = fred_series_object.linewidth

        if bool(fred_series_object.series_dict[key]["dollar_format"])==True:
            my_graph_data_object.dollar_format = True

        my_graph_data_object.label = "FED Series \""+ key +"\""+ fred_series_object.series_dict[key]["filename"] +"\""

        my_graph_data_object.x_axis_values = series_1[(series_1['date'] >= datetime.datetime.strptime(fred_series_object.series_dict[key]["series_start"], '%Y-%m-%d'))].sort_values(by=['date'])['date']
        my_graph_data_object.y_axis_values = series_1[(series_1['date'] >= datetime.datetime.strptime(fred_series_object.series_dict[key]["series_start"], '%Y-%m-%d'))].sort_values(by=['date'])['value']


        if "x_step_size" in fred_series_object.series_dict[key].keys():
            my_graph_data_object.x_step_size = fred_series_object.series_dict[key]["x_step_size"]


        my_graph_data_object.y_lim_low = series_1[(series_1['date'] >= datetime.datetime.strptime(fred_series_object.series_dict[key]["series_start"], '%Y-%m-%d'))]["value"].min()
        my_graph_data_object.y_lim_high = series_1[(series_1['date'] >= datetime.datetime.strptime(fred_series_object.series_dict[key]["series_start"], '%Y-%m-%d'))]["value"].max()
        my_graph_data_object.line_color = list_colors[color_index]
        my_graph_data_object.y_label = fred_series_object.series_dict[key]["y_label"]

        if "y_step_size" in fred_series_object.series_dict[key].keys():
            my_graph_data_object.y_step_size = fred_series_object.series_dict[key]["y_step_size"]

        list_of_graph_data_objects.append(my_graph_data_object)
        color_index += 1


    my_graphing_object = GraphUtility()
    file_name_to_save = path.join(os.path.abspath(os.getcwd()),"pictures",clean_filename(fred_series_object.graph_label)+".png")
    if fred_series_object.dual_axis == True:
        my_graphing_object.plot_multi_line_graph_month_interval_different_scales(list_of_graph_data_objects,fred_series_object.graph_label,
                                                                             fred_series_object.x_axis_label,
                                                                             width=fred_series_object.width,
                                                                             height=fred_series_object.height,
                                                                             output_file_name=file_name_to_save,
                                                                             save_only=True,
                                                                             frequency=fred_series_object.frequency,
                                                                             interval=fred_series_object.frequency_interval)
    else:
        my_graphing_object.plot_multi_line_graph_year_interval(list_of_graph_data_objects,
                                                                fred_series_object.graph_label,
                                                                fred_series_object.x_axis_label,
                                                                fred_series_object.y_axis_label,
                                                               output_file_name=file_name_to_save,
                                                               width=fred_series_object.width,
                                                               height=fred_series_object.height)




l_fred_series_objects = []


fred_series_object = FredSeriesObject()


fred_series_object.series_dict = {
               'MEHOINUSA672N':{'filename':'Median Household Income',
                           'y_label':'Adjusted Dollars',
                           'series_start':'1984-01-01',
                            'dollar_format': True     },
                'CPIAUCSL':{'filename':'CPI Urban Consumers',
                                           'y_label':'CPI Index',
                                           'series_start':'1984-01-01'
                            ,'dollar_format':False}
               }

fred_series_object.graph_label     = 'CPI and Median Income Jan 1984 through Jan 2021'
fred_series_object.x_axis_label    = 'Year'
fred_series_object.width   =   18
fred_series_object.height  =   6


l_fred_series_objects.append(fred_series_object)

fred_series_object = FredSeriesObject()


fred_series_object.series_dict = {
               'MEHOINUSA672N':{'filename':'Median Household Income',
                           'y_label':'Adjusted Dollars',
                           'series_start':'1984-01-01',
                                'dollar_format':True},
                'PCE':{'filename':'Personal Consumption Expenditures',
                                           'y_label':'PCE Index',
                                           'series_start':'1984-01-01',
                       'dollar_format':True}
               }
fred_series_object.graph_label     = 'Personal Consumption Expenditures and Median Income Jan 1984 through Jan 2021'
fred_series_object.x_axis_label    = 'Year'
fred_series_object.width   =   18
fred_series_object.height  =   6
fred_series_object.frequency="yearly"

l_fred_series_objects.append(fred_series_object)

fred_series_object = FredSeriesObject()

fred_series_object.series_dict = {
        'CPIAUCSL': {'filename': 'Consumer Price Index All Items',
                     'y_label': 'CPI Index',
                     'series_start': '1975-01-01',
                     'dollar_format': False},
        'WPS0811': {'filename': 'Lumber Price Per Hundred Pounds',
                    'y_label': 'Lumber Costs',
                    'series_start': '1975-01-01',
                    'dollar_format': True,
                    'y_step_size': 100
                    }
    }

fred_series_object.graph_label = 'CPI and Lumber Costs Jan 1975 through Present'
fred_series_object.x_axis_label = 'Year'
fred_series_object.width = 18
fred_series_object.height = 6
fred_series_object.frequency = "yearly"

l_fred_series_objects.append(fred_series_object)

fred_series_object = FredSeriesObject()

fred_series_object.series_dict = {
    'CPIAUCSL': {'filename': 'Consumer Price Index All Items',
                 'y_label': 'CPI Index',
                 'series_start': '1990-01-01',
                 'dollar_format': False},
    'PCOPPUSDM': {'filename': 'Copper Price Per Ton',
                  'y_label': 'Copper Cost',
                  'series_start': '1990-01-01',
                  'dollar_format': True,
                  'y_step_size': 1000
                  }
}

fred_series_object.graph_label = 'CPI and Copper Costs Jan 1990 through Present'
fred_series_object.x_axis_label = 'Year'
fred_series_object.width = 18
fred_series_object.height = 6
fred_series_object.frequency = "yearly"

l_fred_series_objects.append(fred_series_object)

fred_series_object = FredSeriesObject()

fred_series_object.series_dict = {
    'PSAVERT': {'filename': 'Personal Savings Rate',
                 'y_label': 'Savings Rate Percentage',
                 'series_start': '2008-01-01',
                 'dollar_format': False},
    'PCEC96': {'filename': 'Personal Consumption (Billions)',
                  'y_label': 'Personal Consumption (Billions)',
                  'series_start': '2008-01-01',
                  'dollar_format': True
                  }
}

fred_series_object.graph_label = 'Personal Savings Rate & Consumption'
fred_series_object.x_axis_label = 'Month and Year'
fred_series_object.width = 18
fred_series_object.height = 6
fred_series_object.frequency = "monthly"
fred_series_object.frequency_interval = 6

l_fred_series_objects.append(fred_series_object)

fred_series_object = FredSeriesObject()

fred_series_object.series_dict = {
    'TCU': {'filename': 'Manufacturing Capacity',
                 'y_label': 'Manufacturing Capacity',
                 'series_start': '1996-04-01',
                 'dollar_format': False},
    'CPIAUCSL': {'filename': 'CPI all',
                  'y_label': 'CPI Urban All',
                  'series_start': '1996-04-01',
                  'dollar_format': False},
     'CPILFESL': {'filename': 'CPI Less Food And Energy',
                  'y_label': 'CPI No Food Or Energy',
                  'series_start': '1996-04-01',
                              'dollar_format': False
                  }
}

fred_series_object.graph_label = 'Manufacturing Capacity Utilization & CPI with and Without Food and Energy'
fred_series_object.x_axis_label = 'Month and Year'
fred_series_object.width = 18
fred_series_object.height = 6
fred_series_object.frequency = "monthly"
fred_series_object.frequency_interval = 6

l_fred_series_objects.append(fred_series_object)

fred_series_object = FredSeriesObject()

fred_series_object.series_dict = {
    'CSUSHPINSA': {'filename': 'Case-Schiller U.S. National Price Index',
                 'y_label': 'House Price Index',
                 'series_start': '1988-01-01',
                 'dollar_format': False},
    'MABMM301USM189S': {'filename': 'FED M3 Money Supply',
                  'y_label': 'Fed M3 Money Supply',
                  'series_start': '1988-01-01',
                  'dollar_format': True
                  }
}

fred_series_object.graph_label = 'Case Schiller Home Index and M3 Money Supply 1988 through Present'
fred_series_object.x_axis_label = 'Month and Year'
fred_series_object.width = 18
fred_series_object.height = 6
fred_series_object.frequency = "yearly"
fred_series_object.frequency_interval = 1

l_fred_series_objects.append(fred_series_object)

fred_series_object = FredSeriesObject()

fred_series_object.series_dict = {
    'UNRATE': {'filename': 'Unemployment Rate',
                 'y_label': 'Unemployment Rate',
                 'series_start': '1996-04-01',
                 'dollar_format': False},
    'CPIAUCSL': {'filename': 'Consumer Price Index All Urban Consumers',
                  'y_label': 'CPI All Urban Consumers',
                  'series_start': '1996-04-01',
                  'dollar_format': False
                  }
}

fred_series_object.graph_label = 'Unemployment Rate & CPI Urban 1996 Through Present'
fred_series_object.x_axis_label = 'Month and Year'
fred_series_object.width = 18
fred_series_object.height = 6
fred_series_object.frequency = "monthly"
fred_series_object.frequency_interval = 6

l_fred_series_objects.append(fred_series_object)

fred_series_object = FredSeriesObject()

fred_series_object.series_dict = {
    'FPCPITOTLZGUSA': {'filename': 'Inflation, consumer prices for the United States',
                 'y_label': 'Inflation Rate',
                 'series_start': '1961-01-01',
                 'dollar_format': False},
    'FEDFUNDS': {'filename': 'Effective Federal Funds Rate',
                  'y_label': 'Federal Funds Rate',
                  'series_start': '1961-01-01',
                  'dollar_format': False
                  }
}

fred_series_object.graph_label = 'Inflation and Federal Funds Rate'
fred_series_object.x_axis_label = 'Year'
fred_series_object.y_axis_label = 'Rate'
fred_series_object.width = 10
fred_series_object.height = 6
fred_series_object.frequency = "yearly"
fred_series_object.frequency_interval = 5
fred_series_object.linewidth = 1.25
fred_series_object.dual_axis = False

l_fred_series_objects.append(fred_series_object)


for fed_report_object in l_fred_series_objects:
    do_fed_extract_and_graph_multi_series(fed_report_object)