import os
import sys
import json
from datetime import datetime
from os import system, name
from time import sleep
import copy
import threading
import imp

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except:
    pass

GLOBAL_DATA_STORE = None

class Utility:
    '''
    Utility class to handle things that all of the other classes may need.  File / screen access etc.
    '''

    screen_width = 76
    def __init__(self):
        self.bozo ="bozo"
        self.screen_width = 76
    # define our clear function
    def clear(self):
        # for windows
        if name == 'nt':
            _ = system('cls')
        # for mac and linux(here, os.name is 'posix')
        else:
            _ = system('clear')

    def center_with_stars(self,input_string,screen_width=76):
        '''
        Print stuff out with * characters on either side *
        :param input_string: text to print
        :param screen_width: max console width to use
        :return:
        '''
        buffer = int((screen_width -len(input_string)-2)/2)
        input_string = "*" + " " *buffer+ input_string +" "*buffer+"*"
        if(len(input_string)<screen_width):
            input_string.replace(" *","  *")
        # print(len(input_string))
        return input_string

    def print_header(self):
        '''
        Print a generic header.
        :return:
        '''
        print("*"*self.screen_width)
        print(self.center_with_stars("U.C. Berkeley MIDS Summer 2021 W200 Project 1 -- Don Irwin",self.screen_width))
        print("*"*self.screen_width)
        print(self.center_with_stars("Real Estate Market Info by Zip Code System",self.screen_width))
        print("*"*self.screen_width)

    def get_data_from_file(self,str_file_name):
        '''
        Read an entire file and push the data back.
        :param str_file_name:
        :return:
        '''
        with open(str_file_name, 'r') as file:
            data = file.read()

        return data

    def get_this_dir(self):
        '''
        Return the working directory.
        :return:
        '''
        thisdir = os.getcwd()
        return thisdir

    def display_splash_screen(self):
        '''
        Read text file to display vainglorious splash screen.
        :return:
        '''
        self.clear()
        splash_file = os.path.join(self.get_this_dir(),'splash_text.txt')
        print(self.get_data_from_file(splash_file))
        sleep(2)

    def display_exit_screen(self):
        '''
        Exit file for same vainglorious splash screen.
        :return:
        '''

        self.clear()
        splash_file = os.path.join(self.get_this_dir(),'goodbye.txt')
        print(self.get_data_from_file(splash_file))
        sleep(2)

    def do_dependency_check(self):
        '''
        Check for library dependencies which are non-standard python libraries
        Alert use if some environment update is needed.
        :return:
        '''
        try:
            exists = imp.find_module("matplotlib")
            exists = True
        except:
            exists = False

        if not exists:
            self.clear()
            self.print_header()
            print(self.center_with_stars("DEPENDENCY MISSING:"))
            print("")
            print(self.center_with_stars("This program requires the module 'matplotlib'"))
            print("")
            print(self.center_with_stars(" Please view the link below on how to install: "))
            print(self.center_with_stars(" https://matplotlib.org/stable/users/installing.html "))
            print("")
            print(self.center_with_stars(" Install the missing module, then run the program again. "))
            print("")
            print("*"*self.screen_width)
            sys.exit()

class AreaInformationByZipcode(Utility):
    '''
    Simple Class representation of json, probably unnecessary, but we will see.
    '''

    def __init__(self,**kwargs):
        allowed_keys = {'zipcode', 'search_uri', 'description'}
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)

    def __init__(self, json_string):
        super().__init__()
        '''
        Load it up
        :param json_string:
        '''
        self.__dict__ = json.loads(json_string)

    def print_internal_directory(self):
        '''
        print the name value pairs in the simple json file
        :return:
        '''
        for k,v in self.__dict__.items():
            print("{} is \"{}\"".format(k,v))

class AreaDataStore(Utility):
    '''
    Primary Data object with different internal structures used by all classes.
    This is loaded from disk once at the beginning then re-used throughout.
    '''

    beginning_day_id = "20210318"
    ending_day_id = "20210606"
    smooth_data_dir = "historical_data"
    rough_data_dir = "historical_data_original_do_not_delete"

    def __init__(self,use_rough_data=False):
        super().__init__()
        '''
        Initializer which sets up iternal objects.
        loads either rough un-smoothed data, or smoothed data.
        :param use_rough_data:
        '''
        if use_rough_data:
            self.data_directory = AreaDataStore.rough_data_dir
        else:
            self.data_directory = AreaDataStore.smooth_data_dir
        self.area_data_objects_by_zipcode = {}
        self.area_name_by_zipcode = {}
        self.load_area_data_objects()
        self.beginning_day_id = "20210318"
        self.ending_day_id = "20210606"

    def load_area_data_objects(self):
        '''
        Most important method in the class.
        Loads all of the data objects into nested dictionaries for consumption by the other classes.
        :return:
        '''
        historical_data_dir = os.path.join(self.get_this_dir(), self.data_directory)
        day_id_dirs = [day_id_directory for day_id_directory in os.listdir(historical_data_dir) ]

        l_area_data_by_zipcode = []
        zip_code_set = set()

        for day_id in day_id_dirs:
            try:
                my_day_id = int(day_id)
            except:
                continue
            if not (int(day_id)<int(self.beginning_day_id)) and not (int(day_id)>int(self.ending_day_id)):
                day_id_directory = os.path.join(historical_data_dir,day_id)
                json_files = [full_directory for full_directory in os.listdir(day_id_directory) ]
                for json_file in json_files:
                    zip_code = json_file.split('_')[0]
                    file_name = os.path.join(day_id_directory,json_file)
                    file_data = self.get_data_from_file(file_name)
                    zip_code_by_day_id_data_object = AreaInformationByZipcode(file_data)
                    l_area_data_by_zipcode.append((zip_code_by_day_id_data_object))
                    zip_code_set.add(zip_code)

        for zip_code in zip_code_set:
            dict_day_data_in_zipcode = {}
            for zip_code_area_object in l_area_data_by_zipcode:
                if zip_code_area_object.zipcode ==zip_code:
                    dict_day_data_in_zipcode[zip_code_area_object.extract_day_id] = zip_code_area_object
                    self.area_name_by_zipcode[zip_code] = zip_code_area_object.description
            self.area_data_objects_by_zipcode[zip_code] = dict_day_data_in_zipcode

    def get_area_info_by_zipcode(self,zip_code):
        '''
        Returns a list of objects keyed by "day_id" YYYYMMDD for a supplied zipcode.
        :param zip_code:
        :return:
        '''
        l_return = [self.area_data_objects_by_zipcode[zip_code][key] for key in sorted(self.area_data_objects_by_zipcode[zip_code].keys())]
        return l_return

    def get_areas_by_max_price(self,max_price):
        l_zipcodes = set()
        for zip_code in self.area_data_objects_by_zipcode.keys():
            for key in self.area_data_objects_by_zipcode[zip_code].keys():
                area_property_data = self.area_data_objects_by_zipcode[zip_code][key]
                try:
                    if max_price <= int(area_property_data.median_list_price.replace(",","")):
                        l_zipcodes.add(zip_code)
                except:
                    pass

        l_return = {key: self.area_name_by_zipcode[key] for key in self.area_name_by_zipcode.keys() if key in l_zipcodes}
        return l_return


class AreaDataMenu(Utility):
    '''
    The opening menu of the program.
    consumes the AreaDataStore()
    '''

    def __init__(self):
        super().__init__()
        '''
        Initializer which prompts user for what data set to use
        sets that set to global.
        '''

    def set_data_source(self):

        data_store_selection = self.display_data_source_menu()
        if data_store_selection == '1':
            global_data_store = AreaDataStore()
        else:
            use_rough_data = True
            global_data_store = AreaDataStore(use_rough_data)

        global GLOBAL_DATA_STORE
        GLOBAL_DATA_STORE = global_data_store
        self.area_data_store = GLOBAL_DATA_STORE


    def display_data_source_menu(self):
        '''
        Displays the data source menu.
        :return:
        '''
        self.clear()
        self.print_header()
        print(self.center_with_stars("DATA SOURCE MENU",76))
        print("*"*self.screen_width)
        print(" "*self.screen_width)

        self.menu_dict = {}
        self.menu_dict['1']="Smoothed Data (default)"
        self.menu_dict['2']="Original Rough Data"


        for option in self.menu_dict.keys():
            if(int(option)<10):
                to_print = "{}.  : {}".format(option,self.menu_dict[option])
            else:
                to_print = "{}. : {}".format(option,self.menu_dict[option])
            # side_buffer = (len(to_print)-screen_width)/2
            to_print = " "*int(20) + to_print
            print(to_print)

        print(" "*self.screen_width)
        print(" "*self.screen_width)

        print("*"*self.screen_width)
        print(self.center_with_stars("Select what data you would like to use. ",self.screen_width))

        print("*"*self.screen_width)
        print(" "*self.screen_width)

        data_type_selection = input("Please make your selection:")
        while data_type_selection not in self.menu_dict.keys():
            print("The value you selected {} is not a valid input.".format(data_type_selection))
            data_type_selection = input("Please make your selection:")

        return data_type_selection

    def display_area_data_menu(self,price_filter=None):
        '''
        Displays all zipcodes and their names.
        :return:
        '''
        self.clear()
        max_key = max(self.area_data_store.area_name_by_zipcode, key=lambda k: len(self.area_data_store.area_name_by_zipcode[k]))
        max_len = len(self.area_data_store.area_name_by_zipcode[max_key])
        screen_width = 76
        self.print_header()
        title1 = "HOME MENU "
        print(self.center_with_stars(title1))
        print("*"*screen_width)
        print(" "*screen_width)

        if price_filter is None:
            self.area_name_by_zipcode = self.area_data_store.area_name_by_zipcode
        else:
            self.area_name_by_zipcode = self.area_data_store.get_areas_by_max_price(price_filter)

        int_menu = 1
        for zip_code in self.area_name_by_zipcode.keys():
            if(int_menu<10):
                to_print = "{}.  {} : {}".format(int_menu,zip_code,self.area_data_store.area_name_by_zipcode[zip_code])
            else:
                to_print = "{}. {} : {}".format(int_menu, zip_code,
                                                 self.area_data_store.area_name_by_zipcode[zip_code])
            # side_buffer = (len(to_print)-screen_width)/2
            to_print = " "*int(5) + to_print
            print(to_print)
            int_menu+=1

        if(price_filter is None):
            to_print = "{}. {} : {}".format(int_menu, "n/a",
                                            "Filter zipcodes by max price")
            to_print = " " * int(5) + to_print
            print(to_print)

        print(" "*screen_width)

        print("*"*screen_width)
        print(self.center_with_stars("Enter a number corresponding to the zipcode you wish to view or 'quit'"))

        print("*"*screen_width)
        print(" "*screen_width)


    def get_main_menu_input(self):
        '''
        prompts the user to select what area they wish to get info on.
        :return:
        '''
        if(len(self.area_data_store.area_name_by_zipcode.keys())==len(self.area_name_by_zipcode.keys())):

            menu_dict = {str(list(self.area_name_by_zipcode).index(zip_code)+1):zip_code for zip_code in self.area_name_by_zipcode.keys()}
            menu_dict["14"]="price_filter"
            menu_dict['quit']=""
        else:
            menu_dict = {str(list(self.area_name_by_zipcode).index(zip_code)+1):zip_code for zip_code in self.area_name_by_zipcode.keys()}
            menu_dict['quit']=""


        good_input=False
        while not good_input:
            my_input = input("Please make your selection:").lower()
            if my_input not in menu_dict.keys():
                self.display_area_data_menu()
                print("The input your provided '{}' is not a valid menu choice.".format(my_input))
                continue
            else:
                if my_input == "14":
                    good_price = False
                    while not good_price:
                        price_filter = input("Please enter max price:")
                        price_filter = price_filter.replace(",","")
                        try:
                            if isinstance(int(price_filter),int):
                                good_price = True
                                return int(price_filter)
                        except:
                            print("The value entered '{}' is not a valid integer:".format(price_filter))
                            pass
                if my_input == "quit":
                    # print("Quitting -- goodbye.")
                    self.display_exit_screen()
                    sys.exit()
                else:
                    good_input = True
                    return menu_dict[my_input]

class GraphDataObject:
    '''
    Poco object that holds information to be passed to graphing function.
    '''

    def __init__(self):
        self.x_axis_values = None
        self.y_axis_values = None
        self.label = None

class AreaDisplay(Utility):
    '''
    Handles options for what a user can view about a zipcode.
    '''


    def __init__(self,input_zip_code):
        super().__init__()
        '''
        Initializer
        :param input_zip_code: zip code to view.
        '''
        global GLOBAL_DATA_STORE
        self.area_data_store = GLOBAL_DATA_STORE
        # self.area_data_store = AreaDataStore()
        self.zip_code = input_zip_code

    def display_area_data_menu(self):
        '''
        Display options about a specific zipcode.
        :return:
        '''
        self.clear()
        max_key = max(self.area_data_store.area_name_by_zipcode, key=lambda k: len(self.area_data_store.area_name_by_zipcode[k]))
        max_len = len(self.area_data_store.area_name_by_zipcode[max_key])
        screen_width = 76

        self.print_header()

        print(self.center_with_stars("AREA DETAILS MENU ".format(self.zip_code),screen_width))

        print(self.center_with_stars("You have selected zip code {}".format(self.zip_code),screen_width))
        print(self.center_with_stars("Area Name: {}".format(self.area_data_store.area_name_by_zipcode[self.zip_code]),screen_width))

        print("*"*screen_width)
        print(" "*screen_width)
        print(" "*screen_width)

        self.menu_dict = {}
        self.menu_dict['1']="Graph Median Home Price"
        self.menu_dict['2']="Graph Listings in Market"
        self.menu_dict['3']="Graph Price Per Squre Foot"
        self.menu_dict['4']="Graph All"


        for option in self.menu_dict.keys():
            if(int(option)<10):
                to_print = "{}.  : {}".format(option,self.menu_dict[option])
            else:
                to_print = "{}. : {}".format(option,self.menu_dict[option])
            # side_buffer = (len(to_print)-screen_width)/2
            to_print = " "*int(20) + to_print
            print(to_print)

        self.menu_dict['return']='return'
        self.menu_dict['quit']='quit'

        print(" "*screen_width)
        print(" "*screen_width)

        print("*"*screen_width)
        print(self.center_with_stars("Please enter the number of the graph to view. ",screen_width))
        print(self.center_with_stars("Enter 'return' to return to the Home Menu, 'quit' to exit.",screen_width))

        print("*"*screen_width)
        print(" "*screen_width)

    def get_area_menu_input(self):
        '''
        Captures the users input of the type of graph the want to see.
        :return:
        '''


        good_input=False
        while not good_input:
            good_input = True
            my_input = input("Please make your selection:").lower()
            if my_input not in self.menu_dict.keys():
                self.display_area_data_menu()
                print("The input your provided '{}' is not a valid menu choice.".format(my_input))
                good_input = False
                continue

        if my_input == 'quit':
            self.display_exit_screen()
            sys.exit()


        return my_input, self.menu_dict[my_input]

    def display_graph_based_on_input(self,input_tuple,zip_code):
        '''
        Prepares the x and y axis data then feeds it to the graphing class.
        :param input_tuple:
        :param zip_code:
        :return:
        '''
        graph_option = int(input_tuple[0])
        graph_description = input_tuple[1]
        graph_title = graph_description.replace("Graph","Graph of") + \
                      " For\n" + self.area_data_store.area_name_by_zipcode[zip_code] + \
                      ", Zipcode: {}".format(zip_code)
        # datetime(object.extract_dt.split(",")[0]).date()
        x_axis_values = [datetime.strptime(object.extract_dt.split(",")[0],'%m/%d/%Y').date()  for object in self.area_data_store.get_area_info_by_zipcode(zip_code)]
        y_label = ""
        if graph_option == 1:
            y_axis_values = [int(object.median_list_price.replace(",", "")) if len(object.median_list_price.replace(",", ""))>0 else 0  for object in
                             self.area_data_store.get_area_info_by_zipcode(zip_code)]
            if max(y_axis_values)>1000000:
                y_label = "Median Listing Price in Millions"
            else:
                y_label = "Median Listing Price in Dollars"

        if graph_option == 2:
            y_axis_values = [int(object.active_listings) if len(str(object.active_listings).strip())>0 else 0 for object in
                             self.area_data_store.get_area_info_by_zipcode(zip_code)]
            y_label = "Active Listings in Zipcode"

        if graph_option == 3:
            y_axis_values = [int(object.median_price_per_sqft)  for object in
                             self.area_data_store.get_area_info_by_zipcode(zip_code)]
            y_label = "Median Price Per Sq Ft in Dollars"

        #Simple single lined graphs.
        if graph_option != 4:
            area_graph = AreaGraph()
            area_graph.plot_single_line_graph(x_axis_values, y_axis_values, "Day", y_label, graph_title)

        #Multi_line_graph
        if graph_option == 4:
            lgo = []
            mpgdo = GraphDataObject()
            mpgdo.label = "Median Price"
            mpgdo.x_axis_values = x_axis_values
            mpgdo.y_axis_values = [int(object.median_list_price.replace(",", "")) if len(object.median_list_price.replace(",", ""))>0 else 0  for object in
                             self.area_data_store.get_area_info_by_zipcode(zip_code)]
            lgo.append(mpgdo)
            algdo = GraphDataObject()
            algdo.label = "Active Listings"
            algdo.x_axis_values = x_axis_values
            algdo.y_axis_values = [int(object.active_listings)*200 if len(str(object.active_listings).strip())>0 else 0 for object in
                             self.area_data_store.get_area_info_by_zipcode(zip_code)]
            lgo.append(algdo)
            ppsqftgdo = GraphDataObject()
            ppsqftgdo.label = "Sqft Price"
            ppsqftgdo.x_axis_values = x_axis_values
            ppsqftgdo.y_axis_values = [int(object.median_price_per_sqft)*1000  for object in
                             self.area_data_store.get_area_info_by_zipcode(zip_code)]
            lgo.append(ppsqftgdo)

            area_graph = AreaGraph()
            graph_title = "Multi Line Graph" + \
                          " For\n" + self.area_data_store.area_name_by_zipcode[zip_code] + \
                          ", Zipcode: {}".format(zip_code)

            area_graph.plot_multi_line_graph(lgo,graph_title)


class AreaGraph(Utility):
    '''
    Object that renders the graph.
    '''

    def __init__(self):
        global GLOBAL_DATA_STORE
        self.area_data_store = GLOBAL_DATA_STORE

    def plot_multi_line_graph(self,list_graph_data_objects,title):
        '''
        Plot a multi line graph.
        :param list_graph_data_objects: list of GraphDataObjects
        :param title:
        :return:
        '''
        x_axis_values = None
        for graph_object in list_graph_data_objects:
            plt.plot(graph_object.x_axis_values,graph_object.y_axis_values,label=graph_object.label)
            x_axis_values = graph_object.x_axis_values
        plt.xlabel("Day")
        plt.ylabel("Value")
        plt.title(title)
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.gcf().subplots_adjust(bottom=0.20)
        plt.gcf().subplots_adjust(left=0.25)
        plt.gcf().autofmt_xdate()
        plt.legend()
        plt.show()


    def plot_single_line_graph(self, x_axis_values, y_axis_values, x_label, y_label, graph_label):
        '''
        Plot a single line graph.
        :param x_axis_values:  list of x values
        :param y_axis_values: list of y values
        :param x_label:
        :param y_label:
        :param graph_label:
        :return:
        '''
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.plot(x_axis_values,y_axis_values)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(graph_label)
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.gcf().subplots_adjust(bottom=0.20)
        plt.gcf().subplots_adjust(left=0.25)
        plt.gcf().autofmt_xdate()
        plt.show()

