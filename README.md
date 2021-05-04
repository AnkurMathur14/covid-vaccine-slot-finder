# covid-vaccine-slot-finder

Govt has opened vaccination for all above 18 but vaccination slots come and go in no time.
If you are facing difficulty in finding out available vaccination centers and free slots by constantly login into cowin.gov.in website, then you can use below script.

This script monitors available vaccination centers and free slots based on given age and location (pincode/district) and will notify you at every hour via email if vaccination centers and free slots are available.


    Help:
    python3 vaccine_slot_finder.py -h
    usage: vaccine_slot_finder.py [-h] -a AGE [-p PINCODE] [-d DISTRICT] [-np]

    Search for available vaccination center near you!

    optional arguments:
      -h, --help            show this help message and exit
      -a AGE, --age AGE     Enter your age
      -p PINCODE, --pincode PINCODE
                            Enter your area pincode
      -d DISTRICT, --district DISTRICT
                            Enter your district id
      -np, --noprint        Will not print anything on terminal


    Examples:

    python3 vaccine_slot_finder.py -a <your_age> -p <pin_code>
    python3 vaccine_slot_finder.py -a 30 -p 123456
    
    python3 vaccine_slot_finder.py -a <your_age> -d <district_id>
    python3 vaccine_slot_finder.py -a 30 -d 123
    
    To find out your district id, just run:
    python3 vaccine_slot_finder.py -a <your_age>
    
    To run this in background:
    nohup python3 vaccine_slot_finder.py -a <your_age> -p <pin_code> -np &

Pre-requisites:
1. pip3 install tabulate
2. pip3 install requests
3. Open the py file and provide your email settings in the global section.

Note: You need to generate your(sender) email's app password. Follow this link to do the same https://support.google.com/accounts/answer/185833?hl=en
