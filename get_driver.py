#!/usr/bin/env python
# coding: utf-8

import wget

import zipfile

import platform

import os.path

# ## Setup driver

import logging
logger = logging.getLogger()

web_driver_path = './chromedriver.exe'

logger_level = logging.INFO

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

fhandler = logging.FileHandler(filename='get_driver.log', mode='a')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fhandler.setFormatter(formatter)
logger.addHandler(fhandler)


# ### If running on widows download windows chromedriver 

if( os.path.exists(web_driver_path)  ):
    logger.info("chrome driver is in current directory")
else:
    logger.info("chrome gi not in current directory, will try to download")

    if( 'Windows' in platform.platform() ):

        filename = wget.download('https://chromedriver.storage.googleapis.com/100.0.4896.60/chromedriver_win32.zip')

        logger.info(filename)

        with zipfile.ZipFile(filename, 'r') as zip_ref:
            try:
                zip_ref.extractall('./')
            except:
                logger.info("Issue found extracting driver to current folder")

    else:
        logger.info("Please place chromdrive in current directory")
