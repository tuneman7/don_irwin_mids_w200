from project_1_objects import AreaDataMenu
from project_1_objects import AreaDisplay

def main():
    #This will exit us out if we're not cool
    area_data_menu = AreaDataMenu()
    area_data_menu.do_dependency_check()
    area_data_menu.display_splash_screen()
    area_data_menu.set_data_source()
    stil_running = True
    while stil_running:

        area_data_menu.display_area_data_menu()

        zip_code_to_display = area_data_menu.get_main_menu_input()

        not_price_filter = True
        while not_price_filter:
            if zip_code_to_display in area_data_menu.area_name_by_zipcode.keys():
                not_price_filter = False
                break
            else:
                area_data_menu.display_area_data_menu(zip_code_to_display)
                zip_code_to_display = area_data_menu.get_main_menu_input()

        area_display_object = AreaDisplay(zip_code_to_display)

        return_to_main_menu = False
        while not return_to_main_menu:
            area_display_object.display_area_data_menu()
            area_display_option = area_display_object.get_area_menu_input()

            if area_display_option[0] == 'return':
                return_to_main_menu = True
                break
            else:
                # print(area_display_option)
                area_display_object.display_graph_based_on_input(area_display_option,zip_code_to_display)

main()
