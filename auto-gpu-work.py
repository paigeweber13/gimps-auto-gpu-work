### TODO:
# - if no 'config.yml' file exists, program un-gracefully dies

# built-in
import configparser
import datetime
import os
import pathlib
import pickle
import re
import signal
import subprocess
import sys

# third-party
import requests

# codes
BAD_PARAMS_CODE = 1
NETWORK_ERROR_CODE = 2
BAD_CONFIG_CODE = 3
BAD_SESSION_CODE = 4
NO_RESULTS_CODE = 5

# urls
login_url = "https://www.mersenne.org/"
get_manual_assignment_url = "https://www.mersenne.org/manual_assignment/"
post_manual_results_url = "https://www.mersenne.org/manual_result/"

# filenames
session_data_file = "session.pkl"
config_file = "config.ini"
worktodo_file = "worktodo.txt"
results_file = "results.txt"
old_results_folder = "old_results"
old_results_html_name = "results.html"

def check_config_file(config):
    if 'User Info' not in config or 'username' not in config['User Info']:
        print('Malformed config.ini file! Please redownload it.')
        sys.exit(BAD_CONFIG_CODE)

    if config['User Info']['username'] == '' or \
            config['User Info']['password'] == '':
        print('Please open config.ini and add your username and/or password')
        sys.exit(BAD_CONFIG_CODE)

def get_gpu_work(num_jobs=1):
    cores = 1
    pref = 2 # 2 is the code for trial factoring jobs
    exp_lo = None # lower exponent limit
    exp_hi = None # upper exponent limit
    p = {
        "cores": cores,
        "num_to_get": num_jobs,
        "pref": pref,
        "exp_lo": exp_lo,
        "exp_hi": exp_hi,
    }
    r = requests.get(get_manual_assignment_url, params=p)

    if (r.status_code != 200):
        print("error retrieving new work! Got error code ", r.status_code)
        sys.exit(NETWORK_ERROR_CODE)
    
    pattern = re.compile(r"<!--BEGIN_ASSIGNMENTS_BLOCK-->(?P<work>.*)"
                    "<!--END_ASSIGNMENTS_BLOCK-->", re.DOTALL)
    m = pattern.search(r.text)

    with open(worktodo_file, 'a') as f:
        f.write(m.group("work"))

def mersenne_login():
    s = requests.Session()
    config = configparser.ConfigParser()
    config.read(config_file)
    check_config_file(config)

    payload = {
        'user_login': config['User Info']['username'],
        'user_password': config['User Info']['password'],
        }
    r = s.post(login_url, payload)

    if (r.status_code != 200):
        print("error retrieving new work! Got error code ", r.status_code)
        sys.exit(NETWORK_ERROR_CODE)

    print("successfully logged in, saving session data to disk for later use")
    with open(session_data_file, 'wb') as f:
        pickle.dump(s, f)

def post_results():
    config = configparser.ConfigParser()
    config.read(config_file)
    check_config_file(config)

    # try to create a folder for old results
    try:
        pathlib.Path(old_results_folder).mkdir(exist_ok=True)
    except OSError as e:
        print("problem with creating folder!")
        print()
        raise

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")

    # load session
    try:
        with open(session_data_file, 'rb') as f:
            s = pickle.load(f)
    except(FileNotFoundError):
        print("session data not found on disk. Please login.")
        sys.exit(BAD_SESSION_CODE)

    try:
        with open(results_file, 'r') as f:
            payload = {
                'was_logged_in_as': config['User Info']['username'],
                'data': f.read(),
            }

            print("sending data...")
            r = s.post(post_manual_results_url, payload)

            if r.status_code != 200:
                print("Network problem while sending results.")
                print("error is:", r.status_code)
                sys.exit(NETWORK_ERROR_CODE)

            if re.search(r'login session expired', r.text):
                print("Login session expired! Please login and try again.")
                sys.exit(BAD_SESSION_CODE)
    except FileNotFoundError:
        print("no results file! you need to check factoring to get results "
              "before running this script.")
        sys.exit(NO_RESULTS_CODE)

    # write response to html file for examination if desired
    html_name_components = old_results_html_name.split(sep='.')
    new_html_name = html_name_components[0] + '_' + timestamp + '.' + \
                    html_name_components[1]

    with open(old_results_folder + '/' + new_html_name, 'w') as f:
        f.write(r.text)

    # move results file
    results_name_components = results_file.split(sep='.')
    new_results_file_name = results_name_components[0] + '_' + timestamp \
                            + '.' + results_name_components[1]

    # copy
    os.rename(results_file, old_results_folder + '/' + new_results_file_name)

def interrupt_handler(signal_received, frame):
    print('SIGINT (ctrl-c) received, exiting...')
    sys.exit(0)

def auto_run():
    signal.signal(signal.SIGINT, interrupt_handler)

    while(True):
        num_lines = sum(1 for line in open('worktodo.txt', 'r'))
        if num_lines == 0:
            get_gpu_work(50)
    
        subprocess.run(['./mfaktc.exe'])

        post_results()

def main():
    # get_gpu_work(1000)
    # mersenne_login()
    # post_results()
    # post_results()
    auto_run()

if __name__ == "__main__":
    main()
