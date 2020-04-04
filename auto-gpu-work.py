# built-in
import configparser
import pickle
import re
import sys

# third-party
import requests

# codes
BAD_PARAMS_CODE = 1
NETWORK_ERROR_CODE = 2
BAD_CONFIG_CODE = 3
BAD_SESSION_CODE = 4

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
    config.read('config.ini')

    if 'User Info' not in config or 'username' not in config['User Info']:
        print('Malformed config.ini file! Please redownload it.')
        sys.exit(BAD_CONFIG_CODE)

    if config['User Info']['username'] == '' or \
            config['User Info']['password'] == '':
        print('Please open config.ini and add your username and/or password')
        sys.exit(BAD_CONFIG_CODE)

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
    config.read('config.ini')

    try:
        with open(session_data_file, 'rb') as f:
            s = pickle.load(f)
    except(FileNotFoundError):
        print("session data not found on disk. Please login.")
        sys.exit(BAD_SESSION_CODE)

    # search for the string "login session expired" in the response to check if
    # login is still valid.

    with open(results_file, 'r') as f:
        payload = {
            'was_logged_in_s': config['User Info']['username'],
            'data': f.read(),
        }
        print(payload)
        r = s.post(post_manual_results_url, payload)

        print(r.text)

def main():
    get_gpu_work(1000)
    # mersenne_login()
    # post_results()

if __name__ == "__main__":
    main()
