# imports
from dataclasses import dataclass
from datetime import date, timedelta
from re import X
from bs4 import BeautifulSoup
import requests
import json
import config

# this dictionary is used in a function to convert dates from the timeanddate site into a date
month_dict = {
    'Jan':1,
    'Feb':2,
    'Mar':3,
    'Apr':4,
    'May':5,
    'Jun':6,
    'Jul':7,
    'Aug':8,
    'Sep':9,
    'Oct':10,
    'Nov':11,
    'Dec':12
}

# api key for weather api
api_key = getattr(config, 'api_key', 'no_key_found')

# main menu
menu = """
Holiday Menu
=================
1. Add a Holiday
2. Remove a Holiday
3. Save Holiday List
4. View Holidays
5. Exit
"""


# this function turns the date string in the JSON file into a date
def make_json_date(string_date):
    date_parts = string_date.split('-')
    year = int(date_parts[0])
    month = int(date_parts[1])
    day = int(date_parts[2])
    return date(year, month, day)

# the make_scraped_date() function turns a date string (combined with a year) from timeanddate.com into a date
def make_scraped_date(short_date, year):
    date_parts = short_date.split(' ')
    month = month_dict[date_parts[0]]
    day = int(date_parts[1])
    year = year
    return date(year,month,day)

# function used to get HTML
def get_HTML(url):
    response = requests.get(url)
    return response.text

# get json weather data from api
def get_json(url):
    response = requests.get(url)
    return response.json()

# check valid exit menu response
def check_exit(response):
    active = True
    if response == 'y':
        print("Goodbye!")
        is_valid = True
        active = False
    elif response == 'n':
        print("Okay. Returning to main menu.")
        is_valid = True
    else:
        print("Please choose y or n.")
        is_valid = False
    return is_valid, active

# defining Holiday object class
@dataclass
class Holiday():
    name: str
    date: date

    def __str__(self):
        return f'{self.name} ({self.date})'

# defining HolidayList object class
class HolidayList:
   # no input is necessary to create a HolidayList. An initialized HolidayList begins with an empty list.
    def __init__(self):
        self.inner_holidays = []

   # add a holiday to a list. A holiday cannot be added more than once.
    def add_holiday(self,holiday):
        if type(holiday) == Holiday:
            if holiday in self.inner_holidays:
                return f'{holiday.name} is already in list - not added.'
            else:
                self.inner_holidays.append(holiday)
                return f'Success:\n{holiday} has been added to the holiday list.'
        else:
            return "Input not a holiday, could not add."

   # find a holiday within a HolidayList and return it
    def find_holiday(self, holiday_name, date):
        input = Holiday(holiday_name, date)
        if input in self.inner_holidays:
            for holiday in self.inner_holidays:
                if holiday == input:
                    return holiday.__str__()
                else:
                    return f'{holiday_name} ({date}) could not be found.'

   # find a holiday & remove it
    def remove_holiday(self, holiday_name):
        count = 0
        for holiday in self.inner_holidays:
            if holiday.name == holiday_name:
                self.inner_holidays.remove(holiday)
                count = count + 1
        if count == 0:
            return f'{holiday_name} not found.'
        else: 
            return f'Success:\n{holiday_name} has been removed from the list.'

   # read holidays in from the json file location
    def read_json(self):
        with open('holidays.json') as file:
            reader = json.load(file)
            holidays = reader['holidays']
        for entry in holidays:
            date = make_json_date(entry['date'])
            holiday = Holiday(entry['name'],date)
            self.add_holiday(holiday)
   
   #write to json
    def save_to_json(self):
        holiday_dict = {"holidays":[]}
        for holiday in self.inner_holidays:
            entry = {'name': holiday.name,'date': str(holiday.date)} 
            holiday_dict["holidays"].append(entry)

        json_object = json.dumps(holiday_dict, indent=4)

        with open('holidays.json','w') as file:
            file.write(json_object)
      

   # scrape holidays from timeanddate site
    def scrape_holidays(self):
        dates = []
        for year in range(2020,2025):
            html = get_HTML(f'https://www.timeanddate.com/holidays/us/{year}?hol=43122559')
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('tbody').find_all('tr',attrs={'showrow'})
            row = soup.find('tbody').find('tr', attrs = {'showrow'})

            for row in table:
                scraped_date = make_scraped_date(row.find('th').text, year)
                name = row.find('a').text
                holiday = Holiday(name, scraped_date)
                if holiday not in dates:
                    dates.append(holiday)
        for holiday in dates:
            self.add_holiday(holiday)
    
    # filter holidays by year & week number & put in a list
    def filter_holidays_by_week(self, year, week_num):
        holidays = list(filter(lambda holiday: (holiday.date.year == year) 
                                            and holiday.date.isocalendar().week == week_num, 
                                            self.inner_holidays))
        return holidays
    
    # display holidays in a given week
    def display_holidays_in_week(self, year, week_num):
        for holiday in self.filter_holidays_by_week(year, week_num):
            print(holiday.__str__())

    # get weather 
    def get_weather(self):
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/minneapolis%2Cmn/{start_of_week}/{end_of_week}?unitGroup=metric&key={api_key}&contentType=json'
        weather_days = get_json(url)['days']
        for holiday in self.inner_holidays:
            for day in weather_days:
                if holiday.date.__str__() == day['datetime']:
                    print(holiday.__str__() + ' - ' + day['conditions'])

    # view current week
    def view_current_week(self):
        year = date.today().isocalendar().year
        week = date.today().isocalendar().week
        is_valid = False
        while not is_valid:
            weather = input("Would you like to see this week's weather? [y/n] ")
            # get this week's weather
            if weather == 'y':
                self.get_weather()
                is_valid = True
            # just show the holidays
            elif weather == 'n':
                print("Okay. Showing you this week's holidays:")
                self.display_holidays_in_week(year, week)
                is_valid = True
            else: 
                print("Invalid input, try again.")


   # number of holidays
    def num_holidays(self):
        return len(self.inner_holidays)


def main():
    # initialize holiday list
    holiday_list = HolidayList()

    # read in json file
    holiday_list.read_json()
    print("Holidays from JSON file added.")

    # scrape data from timeanddate.com
    #holiday_list.scrape_holidays()
    print("Holidays from timeanddate.com added.")

    print(f"""
    Holiday Management
    ====================
    There are {holiday_list.num_holidays()} holidays stored in the system.""")

    # maintain functionality with a for loop until user wishes to exit
    active = True
    
    # begin with changes saved
    saved = True

    while active:
        print(menu) 
        # Prompt the user to choose a menu option, continue when a valid option is input
        is_valid = False
        while not is_valid:
            try: 
                choice = int(input("Choose a menu option: "))
                if choice in range (1,6):
                    is_valid = True
                else: 
                    print("Invalid menu option. Try again.")
            except:
                print("Invalid menu option. Try again.")

        # add a holiday
        if choice == 1:
            holiday_name = input("Holiday: ")
            # make sure the date input is valid
            is_valid = False
            while not is_valid:
                try: 
                    holiday_date = make_json_date(input("Date: "))
                    is_valid = True
                except:
                    print("Invalid date, try again.")
            holiday = Holiday(holiday_name, holiday_date)
            print(holiday_list.add_holiday(holiday))
            saved = False
        # remove a holiday
        elif choice == 2:
            holiday_name = input("Holiday: ")
            print(holiday_list.remove_holiday(holiday_name))
            saved = False
        # save holidays to json file
        elif choice == 3:
            holiday_list.save_to_json()
            saved = True
            print("Your changes have been saved.")
        # view holidays
        elif choice == 4:
            # ensure valid input for the year & week numbers
            is_valid = False
            while not is_valid:
                try:
                    year = int(input("Which year?: "))
                    week_num = input("Which week? #[1-52, leave blank for the current week]: ")
                    # allow a blank 
                    if week_num == '' or int(week_num) in range(1,53):
                        is_valid = True
                    else:
                        print("Invalid input, try again.")
                except:
                    print("Invalid input, try again.")
            # if the user wants to see this week's holidays
                if week_num == '':
                    holiday_list.view_current_week()
                else: 
                    holiday_list.display_holidays_in_week(year,int(week_num))
        # exit
        elif choice == 5:
            is_valid = False
            while not is_valid:
                if saved == True:
                    exit = input("Are you sure you want to exit? [y/n] ")
                    is_valid, active = check_exit(exit)
                else: 
                    exit = input("Are you sure you want to exit?\nYour changes will be lost.\n[y/n] ")
                    is_valid, active = check_exit(exit)

main()

