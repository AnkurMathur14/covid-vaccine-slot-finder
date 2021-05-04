#!/usr/bin/python3
# -------------------------------------------------------------------------------
# Name:        vaccine_slot_finder
# Purpose:     This is to find out available slots for covid vaccination
#              based on given age and location.
#
# Author:      Ankur.Mathur
#
# Created:     02/05/2021
# Copyright:   (c) Ankur.Mathur 2021
# Licence:     <your licence>
# -------------------------------------------------------------------------------

# *************************************************************************
# I.M.P.O.R.T.S
# *************************************************************************

import os
import sys
import json
import time
import copy
import datetime
import argparse
import logging
import warnings
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    import tabulate
except:
    print("Please install 'tabulate' module first. pip3 install tabulate")
    sys.exit(1)

try:
    import requests
except:
    print("Please install 'requests' module first. pip3 install requests")
    sys.exit(1)


warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# *************************************************************************
# G.L.O.B.A.L.S
# *************************************************************************
TO_PRINT = True
SLEEP_FOR = 3600    # 1Hr
PORT = 465
SMTP_SERVER = "smtp.gmail.com"
SENDER_EMAIL = None         # "you@gmail.com"
SENDER_APP_PASSWORD = None  # "exdhohdydfljqqqq"
# To generate app password of the sender, follow the link below:
# https://support.google.com/accounts/answer/185833?hl=en
RECEIVER_EMAIL = None       # ["someone@gmail.com", "anotherone@yahoo.com"]
    
# Configure logger
logging.basicConfig(
    filename=sys.argv[0][:-3]+".log",
    level=logging.DEBUG,
    format='%(asctime)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(funcName)3s() - %(message)s'
)
logger = logging.getLogger()

# *************************************************************************
# C.L.A.S.S.E.S
# *************************************************************************


# *************************************************************************
# F.U.N.C.T.I.O.N.S
# *************************************************************************

def myprint(message):
    if TO_PRINT:
        print(message)
    logger.info(message)


def sent_email_notification(message):
    """
    This function is to send email notification.
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Covid vaccination centers found for you!"
    msg['From'] = SENDER_EMAIL
    msg['To'] = ",".join(RECEIVER_EMAIL)
    part1 = MIMEText(message, 'plain')
    msg.attach(part1)

    try:
        print("connecting to server")
        with smtplib.SMTP_SSL(SMTP_SERVER, PORT) as server:
            print("server connected")
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            server.close()
            myprint('Email sent!')
    except ConnectionRefusedError:
        myprint('Failed to connect to the server. Bad connection settings.')
    except smtplib.SMTPServerDisconnected:
        myprint('Failed to connect to the server. Wrong user/password?')
    except smtplib.SMTPException as e:
        myprint('SMTP error occurred: ' + str(e))


def display_table(dict_list):
    """
    This function
        1. Takes a list of dictionary
        2. Add an Index column, and
        3. Displays the data in tabular format
    """
    header = ['idx'] + list(dict_list[0].keys())
    rows = [[idx + 1] + list(x.values()) for idx, x in enumerate(dict_list)]
    table_content = tabulate.tabulate(rows, header, tablefmt='pretty')
    myprint(table_content)
    return table_content


def select_districts():
    """
    This function
        1. Lists all states, prompts to select one,
        2. Lists all districts in that state, prompts to select required ones, and
        3. Returns the list of districts as list(dict)
    """
    states = requests.get('https://cdn-api.co-vin.in/api/v2/admin/location/states', verify=False)

    if states.status_code == 200:
        states = states.json()['states']

        refined_states = []
        for state in states:
            tmp = {'state': state['state_name']}
            refined_states.append(tmp)

        display_table(refined_states)

        state = int(input('Enter State index: '))
        state_id = states[state - 1]['state_id']

    else:
        logger.error('Unable to fetch states')
        logger.error(states.status_code)
        logger.error(states.text)
        os.system("pause")
        sys.exit(1)

    districts = requests.get('https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}'.format(state_id), verify=False)
    if districts.status_code == 200:
        districts = districts.json()['districts']

        refined_districts = []
        for district in districts:
            tmp = {'district': district['district_name']}
            refined_districts.append(tmp)

        display_table(refined_districts)
        reqd_district = input('Enter district index: ')
        reqd_district = int(reqd_district) - 1
        reqd_districts = [{
            'district_id': item['district_id'],
            'district_name': item['district_name'],
            'district_alert_freq': 440 + ((2 * idx) * 110)
        } for idx, item in enumerate(districts) if idx == reqd_district]

        print('Selected district: ')
        display_table(reqd_districts)
        return reqd_district
    else:
        print('Unable to fetch districts')
        print(districts.status_code)
        print(districts.text)
        sys.exit(1)


def get_availability(age, search_item, is_pincode=True):
    """
    This function
        1. Searches for available slots for vaccination based on age and pincode/district
        2. Search for availability in current week and can do for next weeks as well.
    """
    search_for_weeks = 1 # For current week, make it 2 for next week as well
    base = datetime.datetime.today()
    date_list = [base + datetime.timedelta(days=x) for x in range(0, search_for_weeks*6, 6)]
    date_str = [x.strftime("%d-%m-%Y") for x in date_list]

    for INP_DATE in date_str:
        options = []
        if is_pincode:
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/" \
                  "public/calendarByPin?pincode={}&date={}".format(search_item, INP_DATE)
        else:
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/" \
                  "public/calendarByDistrict?district_id={}&date={}".format(search_item, INP_DATE)
        response = requests.get(URL, verify=False)
        if response.ok:
            resp_json = response.json()
            #print(json.dumps(resp_json, indent=4))
            if resp_json["centers"]:
                myprint("*"*40)
                myprint("Availability in week: {}".format(INP_DATE))
                myprint("*" * 40)
                for center in resp_json["centers"]:
                    for session in center["sessions"]:
                        if session["min_age_limit"] <= age and session['available_capacity'] > 0:
                            out = {
                                'name': center['name'],
                                'district': center['district_name'],
                                'center_id': center['center_id'],
                                'available_doses': session['available_capacity'],
                                'date': session['date'],
                                'minimum_age': session["min_age_limit"],
                                #'slots': session['slots'],
                                'vaccine_type': session["vaccine"],
                                'session_id': session['session_id']
                            }
                            options.append(out)

            options = sorted(options, key=lambda k: (k['date'], k['name'].lower()))
            tmp_options = copy.deepcopy(options)
            if len(tmp_options) > 0:
                cleaned_options_for_display = []
                for item in tmp_options:
                    item.pop('session_id', None)
                    item.pop('center_id', None)
                    cleaned_options_for_display.append(item)

                content = display_table(cleaned_options_for_display)
                sent_email_notification(content)
            else:
                myprint("No available slots in week {}".format(INP_DATE))


def parse_args():
    """
    Method to parse command line parameters
    :return: Dictionary having values of command line parameters
    """

    argp = argparse.ArgumentParser(description="Search for available vaccination center near you!")
    argp.add_argument("-a", "--age",
                      help="Enter your age", type=str, required=True)
    argp.add_argument("-p", "--pincode",
                      help="Enter your area pincode", type=str)
    argp.add_argument("-d", "--district",
                      help="Enter your district id", type=str)
    argp.add_argument('-np', '--noprint',
                      help="Will not print anything on terminal", action='store_true')
    args = vars(argp.parse_args())
    return args


def main():
    """
    This is the entry point function
    :return:
    """
    global TO_PRINT
    global SLEEP_FOR
    arguments = parse_args()
    age = int(arguments['age'])
    pincode = arguments['pincode']
    district = arguments['district']
    if arguments.get("noprint"):
        TO_PRINT = False
    if pincode:
        while True:
            get_availability(age, pincode, is_pincode=True)
            time.sleep(SLEEP_FOR)
    elif district:
        get_availability(age, district, is_pincode=False)
    else:
        district_id = select_districts()
        get_availability(age, district_id, is_pincode=False)


if __name__ == '__main__':
    main()
