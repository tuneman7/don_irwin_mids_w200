from full_fred.fred import Fred
from full_fred.categories import Categories
from full_fred.series import Series
import pandas as pd
import numpy as np
import json
import os
from os import  path

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



my_cats = [9]
for i in my_cats:
    get_category_detail(i)

my_csv_directory = "inflation_csv_files"
my_directory = "inflation_excel_files"

try:
    os.makedirs(my_csv_directory)
except OSError as e:
    print(e)

try:
    os.makedirs(my_directory)
except OSError as e:
    print(e)


l_excel_file_names = []
series = Series()
series.set_api_key_file('full_fred_key.txt')
for series_dict in category_dict["categories"][my_cats[0]]["series"]["seriess"]:
    # print(series_dict.keys())
    id = series_dict["id"]
    my_data_frame = series.get_series_df(id)
    excel_title = clean_filename(series_dict["title"].replace(" ","_") + series_dict["units"].replace(" ","_")) + "_" + id + ".xlsx"
    # excel_title = "demo.xlsx"
    csv_title = excel_title.replace(".xlsx",".csv")
    file_name = path.join(os.path.abspath(os.getcwd()),my_directory,excel_title)
    file_name_csv = path.join( os.path.abspath(os.getcwd()), my_csv_directory, csv_title )
    print(file_name)
    # print(my_data_frame)
    with pd.ExcelWriter(file_name,engine='xlsxwriter') as writer:
        my_data_frame.to_excel(writer,sheet_name="Sheet1",freeze_panes=(1,0))
        # writer.save()
    with open(file_name_csv, "w") as outfile:
        my_data_frame.to_csv(outfile)

    l_excel_file_names.append(excel_title)
    # print(my_data_frame)
    print(excel_title)

with open("excel_file_names.txt","w") as outfile:
    for line in l_excel_file_names:
        outfile.write(line + "\n")

output_file()

