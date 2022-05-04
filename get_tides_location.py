#!/usr/bin/env python
# coding: utf-8

# # Tide scraper 

# ## Import modules

# In[39]:


from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from datetime import datetime
import json

import pandas as pd


import logging
logger = logging.getLogger()


# ## Setup Input locations
location_l = [
    "Half Moon Bay, California",
    "Huntington Beach, California",
    "Providence, Rhode Island",
    "Wrightsville Beach, North Carolina",
]
home_url = "https://www.tide-forecast.com/"
web_driver_path = './chromedriver.exe'

logger_level = logging.INFO
# Setup logging 
logger.setLevel(logger_level)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logger_level)

# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

fhandler = logging.FileHandler(filename='get_tides_location.log', mode='a')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fhandler.setFormatter(formatter)
logger.addHandler(fhandler)

# Create Functions
def tide_check(day, day_data):
    '''Process day data and find low tide during day light hours
    
    Args:
        day (str): date ('%A %d %B %Y')
        day_data (dic): dictionary containing tide and sunrise/sunset data from web.

    Returns:
        df (DataFrame): time series of sunrise, sunset and tide events 
 
    '''
    # Create dataframes
    df_sr = pd.DataFrame( day_data['sr'] )
    df_tides = pd.DataFrame( day_data['tides'] )
    # Clean names 
    df_sr['Event'] = df_sr['Event'].str.replace(":","")
    # Clean times 
    df_sr['Datetime'] = df_sr['Datetime'].str.replace('00','12')
    df_tides['Datetime'] = df_tides['Datetime'].str.replace('00','12')
     # Create datetime objeccts 
    df_sr['Datetime_obj'] = df_sr['Datetime'].apply(lambda v:  datetime.strptime("{} {}".format(day, v), '%A %d %B %Y %I:%M%p' ) )
    df_tides['Datetime_obj'] = df_tides['Datetime'].apply(lambda v:  datetime.strptime("{} {}".format(day, v.split('\n')[0]), '%A %d %B %Y %I:%M %p' ) )
   # Find sunrise and sunset 
    sunrise = df_sr.loc[ df_sr['Event']== 'Sunrise', 'Datetime_obj' ].iloc[0]
    sunset = df_sr.loc[ df_sr['Event']== 'Sunset', 'Datetime_obj' ].iloc[0]
    logger.debug("{} Sunrise:{} and Sunset:{}".format(day, sunrise,sunset))
    # Filter low tide during the day light hours 
    df_tides['daylight_lowtide'] = (df_tides['Tide'] == 'Low Tide') & (df_tides['Datetime_obj'] >= sunrise ) & (df_tides['Datetime_obj'] <= sunset )
    df_sr['daylight_lowtide'] = False
    # Set type 
    df_tides['type'] = 'tide'
    df_sr['type'] = 'sr'
    # Set day 
    day_obj  =  datetime.strptime(day,'%A %d %B %Y')
    df_tides['day_obj'] = day_obj
    df_sr['day_obj'] = day_obj
    # Combine sr and tide data into single time series 
    df_tides = df_tides.rename(columns={'Tide':'Event'})
    return df_tides.append( df_sr )


    
# ### Initialize driver

options = webdriver.ChromeOptions()
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--ignore-certificate-errors')

driver = webdriver.Chrome(web_driver_path, options=options)

# ### Initialize json to capture data
# ## Run webscraper to get data

# Initialize data object to collect data from webpage
j = {}
# Loop over input locations 
for location_i in location_l:
    # Always start at the home page
    driver.get(home_url)
    # initialize data objects
    location_json = {}
    days = {}
    # Get location name for list 
    loc_city = location_i.split(",")[0].strip()
    loc_state = location_i.split(",")[1].strip()
    #
    logger.info("Searching for {}, {}".format(loc_city, loc_state))
    location_found = False
    # Search for location using search bar
    driver.find_element_by_id("homepage-mast__location").send_keys( location_i )
    el_s = driver.find_element_by_xpath("/html/body/main/div/div[1]/div[1]/div[1]/div/div[1]/div[1]/form/div/div[2]/input")
    el_s.click()
    # If location page is found 
    if( loc_city in  driver.title ):
        location_found = True
    else:
        # Search for location using search bar region_id
        driver.find_element_by_id("region_id").send_keys( loc_state )
        driver.find_element_by_id("location_filename_part").send_keys( loc_city )
        el_s = driver.find_element_by_xpath("/html/body/header/div[2]/div/nav/div/div/form/div/div/div[4]/div/input")
        el_s.click()        
        # If location page is found 
        if( loc_city in  driver.title ):
            location_found = True     
    if( location_found ):
        logger.info("{} page found".format(location_i) )
        # Loop over days on the page
        for tideday in driver.find_elements_by_class_name('tide-day'):
            logger.debug(tideday)          
            # Get date for day 
            for tideday__date in tideday.find_elements_by_class_name('tide-day__date'):
                # Parse date from string 
                day_title = tideday__date.text
                day_date = day_title.split(':')[1].strip()
                logger.debug("{}".format(day_date))
                # Initialize lists for tide information 
                day ={}
                tide_l = []
                tide_dt_l = []
                tide_h_l = []
                sr_l = []
                sr_dt_l = []
                # Loop over tide table
                for tideday__tables in tideday.find_elements_by_class_name('tide-day__tables'):
                    for row in tideday__tables.find_elements_by_css_selector('tr'):
                        cell_l = row.find_elements_by_tag_name('td') 
                        # ToDo: 
                        #   Use class table classes "tide-day-tides" and "not-in-print tide-day__sun-moon"
                        #   to split table reads 
                        # Check if it is a tide table
                        if( ('Tide' in row.text) & (len(cell_l) == 3 ) ):
                            logger.debug(row.text)
                            tide_l.append(cell_l[0].text)
                            tide_dt_l.append(cell_l[1].text)
                            tide_h_l.append(cell_l[2].text)
                        # Check if it is a sunrise sunset table
                        elif( len(cell_l) == 4  ):
                            for cell in cell_l:
                                sr_text_l = cell.text.split('\n')
                                if( len(sr_text_l) > 1 ):
                                    sr_l.append(sr_text_l[0])
                                    sr_dt_l.append(sr_text_l[1])
                # Place lists in a dictionary 
                day['tides'] = {'Tide':tide_l,'Datetime':tide_dt_l,'Height':tide_h_l}
                # Place lists in a dictionary 
                day['sr'] = {'Event':sr_l,'Datetime':sr_dt_l}
                # Add day to days dictionary
                days[day_date] = day
        # ToDo: Add scraper for today's infromation
        # Add days to location dictionary 
        location_json['days'] = days
        location_json['city'] = loc_city
        location_json['state'] = loc_state
        j[location_i] = location_json
    else:
        logger.info("Error {} not found".format(loc_city) )

driver.close()

# ## Export data

now_str = datetime.now().strftime("%F_%R").replace(":","_")

with open('{}_web_data.json'.format(now_str), 'w') as outfile:
    json.dump(j, outfile)

# ## Process data scrapped from website

# Initialize dataframe object 
df = pd.DataFrame()
# Loop over extracted location data 
for location_i, location_data in j.items():
    logger.info("Processing {} {} {}".format(location_i,location_data['city'],location_data['state']))
    # Loop over days in and create time series for  sunrise, sunset and tide events 
    for day, day_data in location_data['days'].items():
        df_day = tide_check(day, day_data)
        df_day['City'] = location_data['city']
        df_day['State'] = location_data['state']
        df = df.append(df_day)

df = df.reset_index()

# ## Export data

df.to_csv('{}_proc_data.csv'.format(now_str))

