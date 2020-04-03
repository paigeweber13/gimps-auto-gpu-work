import re
import requests

BAD_PARAMS_CODE = 1
NETWORK_ERROR_CODE = 2

get_manual_assignment_url = "https://www.mersenne.org/manual_assignment/"

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
    
    m = re.search(r"<!--BEGIN_ASSIGNMENTS_BLOCK-->(?P<work>.*)"
                   "\\n<!--END_ASSIGNMENTS_BLOCK-->", r.text)
    write_line_to_file(m.group("work"))

def write_line_to_file(line, filename="worktodo.txt"):
    with open(filename, 'a') as f:
        f.write(line + '\n')

def main():
    get_gpu_work()
    # write_line_to_file("test")

if __name__ == "__main__":
    main()
