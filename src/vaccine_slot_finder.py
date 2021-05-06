
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
from six.moves import http_client

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
PORT = 465
SMTP_SERVER = "smtp.gmail.com"

# Configure logger
logging.basicConfig(
    filename=sys.argv[0][:-3]+".log",
    level=logging.DEBUG,
    format='%(asctime)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(funcName)3s() - %(message)s'
)
logger = logging.getLogger()

BOOKING_URL = "https://cdn-api.co-vin.in/api/v2/appointment/schedule"
BENEFICIARIES_URL = "https://cdn-api.co-vin.in/api/v2/appointment/beneficiaries"
STATES_URL = "https://cdn-api.co-vin.in/api/v2/admin/location/states"
DISTRICT_URL = "https://cdn-api.co-vin.in/api/v2/admin/location/districts/{0}"
CALENDAR_URL_DISTRICT = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={0}&date={1}"
CALENDAR_URL_PINCODE = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={0}&date={1}"

# *************************************************************************
# C.L.A.S.S.E.S
# *************************************************************************


class NoAuth(requests.auth.AuthBase):
    """This "authentication" handler exists for use with custom authentication
    systems, such as the one for the Access API.  It simply passes the
    Authorization header as-is.  The default authentication handler for
    requests will clobber the Authorization header."""

    def __call__(self, r):
        return r


class APIBuilder:

    def __init__(self):
        self.session = requests.session()
        self.session.verify = False
        self.session.auth = NoAuth()
        request_header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        }
        self.session.headers.update(request_header)

    def cowin_api(self, full_url, input_data, method):

        kwargs = {'data': input_data}
        response = self.session.request(method, full_url, verify=None, **kwargs)
        if response.status_code not in (http_client.ACCEPTED, http_client.OK):
            myprint('COWIN API operation on {} failed with status code {} and error {}'.
                             format(full_url, response.status_code, response.text))
            return None
        return response

# *************************************************************************
# F.U.N.C.T.I.O.N.S
# *************************************************************************


def myprint(message):
    if TO_PRINT:
        print(message)
    logger.info(message)


def load_config_file():
    input_file = os.path.join(os.path.dirname(sys.argv[0]), "inputs.json")
    try:
        with open(input_file) as data_file:
            input_json = json.load(data_file)
            return input_json
    except Exception as e:
        myprint("Failed to read the config file {0} with exception {1}".format(input_file, str(e)))
        sys.exit(1)


def sent_email_notification(message):
    """
    This function is to send email notification.
    """

    input_json = load_config_file()
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Covid vaccination centers found for you!"
    msg['From'] = input_json['sender_email']
    msg['To'] = ",".join(input_json['receivers_email'])
    part1 = MIMEText(message, 'plain')
    msg.attach(part1)

    try:
        myprint("connecting to server")
        with smtplib.SMTP_SSL(SMTP_SERVER, PORT) as server:
            myprint("server connected")
            server.ehlo()
            server.login(input_json['sender_email'], input_json['sender_app_password'])
            server.sendmail(input_json['sender_email'], input_json['receivers_email'], msg.as_string())
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


def select_districts(cowin_api_obj):
    """
    This function
        1. Lists all states, prompts to select one,
        2. Lists all districts in that state, prompts to select required ones, and
        3. Returns the list of districts as list(dict)
    """
    states = cowin_api_obj.cowin_api(STATES_URL, '', 'GET')
    if states:
        states = states.json()['states']

        refined_states = []
        for state in states:
            tmp = {'state': state['state_name']}
            refined_states.append(tmp)

        display_table(refined_states)

        state = int(input('Enter State index: '))
        state_id = states[state - 1]['state_id']

    else:
        myprint('Unable to fetch states')
        sys.exit(1)

    districts = cowin_api_obj.cowin_api(DISTRICT_URL.format(state_id), '', 'GET')
    if districts:
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
        return reqd_districts[0]['district_id']
    else:
        print('Unable to fetch districts')
        sys.exit(1)


def get_availability(cowin_api_obj, age, search_for_weeks, search_item, is_pincode=True):
    """
    This function
        1. Searches for available slots for vaccination based on age and pincode/district
        2. Search for availability in current week and can do for next weeks as well.
    """
    base = datetime.datetime.today()
    date_list = [base + datetime.timedelta(days=x) for x in range(0, search_for_weeks*6, 6)]
    date_str = [x.strftime("%d-%m-%Y") for x in date_list]

    for INP_DATE in date_str:
        options = []
        if is_pincode:
            URL = CALENDAR_URL_PINCODE.format(search_item, INP_DATE)
        else:
            URL = CALENDAR_URL_DISTRICT.format(search_item, INP_DATE)
        response = cowin_api_obj.cowin_api(URL, '', 'GET')
        if response:
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
        else:
            myprint('Unable to fetch centers')


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

    input_json = load_config_file()
    search_for_weeks = input_json['search_for_weeks']
    search_frequency = input_json['search_frequency']
    cowin_api_obj = APIBuilder()
    if pincode:
        while True:
            get_availability(cowin_api_obj, age, search_for_weeks, pincode, is_pincode=True)
            time.sleep(search_frequency)
    elif district:
        while True:
            get_availability(cowin_api_obj, age, search_for_weeks, district, is_pincode=False)
            time.sleep(search_frequency)
    else:
        district_id = select_districts(cowin_api_obj)


if __name__ == '__main__':
    main()

