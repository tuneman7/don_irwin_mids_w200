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


#Interest rate series
series_dict = {'CPIAUCSL':{'filename':'Inflation, consumer prices for the United States',
                           'y_label':'CPI Index',
                           'series_start':'2019-01-01'},
               'FEDFUNDS':{'filename':'Effective Federal Funds Rate',
                           'y_label':'Fed Funds Rate',
                           'series_start':'2019-01-01'}
               }

graph_label     = 'CPI Compared to FED funds rate Jan-2019 through Jun-2021'
x_axis_label    = 'Year'
width   =   18
height  =   6



l_excel_file_names = []
l_csv_file_names = []
output_dict = {}
series = Series()
series.set_api_key_file('full_fred_key.txt')
for key in series_dict.keys():
    key
    my_data_frame = series.get_series_df(key)
    excel_title = clean_filename(series_dict[key]["filename"]) + "_" + key + ".xlsx"
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

#output_file()
d = lambda x: pd.datetime.strptime(x, '%Y-%m-%d')
series_1  = pd.read_csv(output_dict[list(series_dict.keys())[0]], index_col=False, parse_dates=['date'], date_parser=d)
series_2   = pd.read_csv(output_dict[list(series_dict.keys())[1]], index_col=False, parse_dates=['date'], date_parser=d)

# print(historic_fed_rate.columns)

# date_time_str = '2018-06-29 08:15:27.243860'
# date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d')

list_of_graph_data_objects = []

my_graph_data_object = GraphDataObject()
my_graph_data_object.label = "FED Series \""+ list(series_dict.keys())[0] +"\""+ series_dict[list(series_dict.keys())[0]]["filename"] +"\""
my_graph_data_object.x_axis_values = series_1[(series_1['date'] >= datetime.datetime.strptime(series_dict[list(series_dict.keys())[0]]["series_start"], '%Y-%m-%d'))].sort_values(by=['date'])['date']
my_graph_data_object.y_axis_values = series_1[(series_1['date'] >= datetime.datetime.strptime(series_dict[list(series_dict.keys())[0]]["series_start"], '%Y-%m-%d'))].sort_values(by=['date'])['value']
my_graph_data_object.y_lim_low = series_1[(series_1['date'] >= datetime.datetime.strptime(series_dict[list(series_dict.keys())[0]]["series_start"], '%Y-%m-%d'))]["value"].min()
my_graph_data_object.y_lim_high = series_1[(series_1['date'] >= datetime.datetime.strptime(series_dict[list(series_dict.keys())[0]]["series_start"], '%Y-%m-%d'))]["value"].max()
my_graph_data_object.line_color = "orange"
my_graph_data_object.y_label = series_dict[list(series_dict.keys())[0]]["y_label"]

list_of_graph_data_objects.append(my_graph_data_object)

my_graph_data_object = GraphDataObject()
my_graph_data_object.label = "FED Series \"" + list(series_dict.keys())[1] + "\"" + series_dict[list(series_dict.keys())[1]]["filename"] + "\""
my_graph_data_object.x_axis_values = series_2[(series_2['date'] >= datetime.datetime.strptime(series_dict[list(series_dict.keys())[0]]["series_start"], '%Y-%m-%d'))].sort_values(by=['date'])['date']
my_graph_data_object.y_axis_values = series_2[(series_2['date'] >= datetime.datetime.strptime(series_dict[list(series_dict.keys())[0]]["series_start"], '%Y-%m-%d'))].sort_values(by=['date'])['value']
my_graph_data_object.y_lim_low = series_2[(series_2['date'] >= datetime.datetime.strptime(series_dict[list(series_dict.keys())[0]]["series_start"], '%Y-%m-%d'))]["value"].min()
my_graph_data_object.y_lim_high = series_2[(series_2['date'] >= datetime.datetime.strptime(series_dict[list(series_dict.keys())[0]]["series_start"], '%Y-%m-%d'))]["value"].max()
my_graph_data_object.line_color = "Blue"
my_graph_data_object.y_label = "FED Funds Rate"
my_graph_data_object.y_label = series_dict[list(series_dict.keys())[1]]["y_label"]
# print(my_graph_data_object.x_axis_values)
# print(my_graph_data_object.y_axis_values)
# exit()
list_of_graph_data_objects.append(my_graph_data_object)
my_graphing_object = GraphUtility()
file_name_to_save = path.join(os.path.abspath(os.getcwd()),"pictures",clean_filename(graph_label)+".png")
my_graphing_object.plot_multi_line_graph_month_interval_different_scales(list_of_graph_data_objects,graph_label,x_axis_label,width=width,height=height,output_file_name=file_name_to_save)

exit()

x_axis_values = series_2[(series_2['date'] >= datetime.datetime(2019, 10, 1))].sort_values(by=['date'])['date']
y_axis_values = series_2[(series_2['date'] >= datetime.datetime(2019, 10, 1))].sort_values(by=['date'])['value']
x_label = "Year"
y_label = "Interest Rate"
graph_label = "Historic Interest Rate"

my_graphing_object.plot_single_line_graph_year_interval(x_axis_values, y_axis_values, x_label, y_label, graph_label)
