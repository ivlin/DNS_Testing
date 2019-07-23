#
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#
import sys, os, re, sqlite3
import subprocess
import itertools
import psutil
import time
from collections import Counter

def test_domain(domain, out_path, num_trials=1):
    driver = webdriver.Firefox()

    extension_dir = "~/.mozilla/firefox/au1p11i6.default-default/extensions/"
    extensions = [
        'uBlock0@raymondhill.net.xpi',
    ]

    for extension in extensions:
        driver.install_addon(extension_dir + extension, temporary=True)

    #time.sleep(3)

    outname="%s/tcpdump_raw"%out_path
    with open(outname, "w") as tcpout:
        #Begin TCPDump
        sudo_password="altairdenebvega"
        #sudo_password="fe2d2cd42390e2b300b548eb80f3c23f36ea41"
        command = 'sudo tcpdump'.split()
        p = subprocess.Popen(['sudo', '-S'] + command, stdin=subprocess.PIPE, stderr=tcpout, stdout=tcpout,
          universal_newlines=True)
        time.sleep(3)
        #automation issue: tcpdump must be run as sudo separately, but we must also pass the password to it
        #for now, it will be done manually
        #sudo_prompt = p.communicate(sudo_password + '\n')[1]

        #Run Selenium
        driver.get(domain)


        #time.sleep(3)
        print("Killing\n")
        subprocess.check_call(["sudo","kill","-9",str(p.pid)])
        os.waitpid(p.pid, 0)
        print("Killed\n")

        #assert "Python" in driver.title
        elem = driver.find_element_by_name("q")
        elem.clear()
        elem.send_keys("pycon")
        elem.send_keys(Keys.RETURN)
        assert "No results found." not in driver.page_source
        driver.close()
    return outname

def test_domain_browsertime(domain, out_path, num_trials=1):
    outname="%s/tcpdump_raw"%out_path
    # credit to jfs, https://stackoverflow.com/questions/13045593/using-sudo-with-python-script
    # for code on running sudo commands in python
    with open(outname, "w") as tcpout:
        #Begin TCPDump
        #sudo_password="fe2d2cd42390e2b300b548eb80f3c23f36ea41"
        command = 'sudo tcpdump'.split()
        p = subprocess.Popen(['sudo', '-S'] + command, stdin=subprocess.PIPE, stderr=tcpout, stdout=tcpout,
          universal_newlines=True)

        #automation issue: tcpdump must be run as sudo separately, but we must also pass the password to it
        #for now, it will be done manually
        sudo_prompt = p.communicate(sudo_password + '\n')[1]

        #Run Browsertime
        print("Testing domain %s"%domain)
        os.system("./browsertime.js -b firefox -n %d %s"%(num_trials, domain))


        subprocess.check_call(["sudo","kill","-9",str(p.pid)])
        os.waitpid(p.pid, 0)
    return outname

def parse_dns_records(filename,out_path):
    with open(filename,"r") as tcpout:
        tcplist = tcpout.readlines()
        dns_req_captures=[]
        domain_captures=set()
        print(len(tcplist))
        ind=0
        for line in tcplist:
            # A? indicates IPv4, AAAA? indicates IPv6, this captures both, also give higher priority to ignoring www.
            capture = re.search("A\?\s(.+). ",line)
            if capture:
                dns_req_captures.append(line)
                domain = capture.group(1)[4:] if capture.group(1).startswith("www.") else capture.group(1)
                domain_captures.add(domain)
                print [ind, line, domain_captures]
            ind+=1
        print ind
        with open("%s/dns_aux"%out_path,"w") as dns_aux:
            for line in dns_req_captures:
                dns_aux.write(line)
        with open("%s/dns_main"%out_path,"w") as dns_main:
            for domain in domain_captures:
                dns_main.write(domain+"\n")
        with open("%s/summary"%out_path,"w") as summary:
            summary.write("raw wc: %d\n"%len(tcplist))
            summary.write("aux wc: %d\n"%len(dns_req_captures))
            summary.write("main wc: %d\n"%len(domain_captures))

# modification of itertools.combinations so that everything isn't loaded to main memory at once
def my_combinations(iterable, r, commit_every=5000):
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)

def extract_combinations(filename, group_size):
    with open(filename,"r") as domains_raw:
        domains = domains_raw.readlines()
        domains = [domain.strip() for domain in domains]
    return itertools.combinations(domains, group_size)


'''
     MAIN FUNCTIONS
'''

DATA_DIRECTORY="tcpout"

def calculate_all_bad(num_resolvers=2):
    cumulative_count=[]
    cumulative_database = sqlite3.connect("db/combination_database_%dr"%num_resolvers)
    cursor = cumulative_database.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS resolution_combinations (tuple_hash VARCHAR(30), tuple_str VARCHAR(100))''')
    curproc=psutil.Process()
    try:
        ind=0
        while True:
            path="%s/%d/dns_main"%(DATA_DIRECTORY, ind)
            combinations = extract_combinations(path, num_resolvers)
            for combination in combinations:
                combination = tuple(sorted(combination))
                tuple_hash = hash(combination)
                tuple_str = ",".join(combination)
                #cursor.execute('''INSERT OR IGNORE INTO resolution_combinations VALUES(?, ?)''', (tuple_hash,tuple_str))
                cumulative_count.append(tuple_hash)
            print("PROGRESS %d"%ind)
            ind+=1
            print("CPU PERCENT: %f"%curproc.cpu_percent())
            print(psutil.virtual_memory())
    except IOError:
        cumulative_database.commit()
        distribution={}
        with open("%s/cumulative_%dr_data"%(DATA_DIRECTORY, num_resolvers),"w") as histogram_file:
            counted = Counter(cumulative_count)
            len_counted=len(counted)
            #progress=0
            #ind=0.0
            for combination in counted:
                distribution[counted[combination]] = 1 if counted[combination] not in distribution else distribution[counted[combination]] + 1
                #if (ind/len_counted * 20 > progress):
                #    print("%d percent of the way there\n"%(progress*5))
                #    progress+=1
                #ind+=1
                #cursor.execute('''SELECT * FROM resolution_combinations WHERE tuple_hash = ? LIMIT 1''', (combination,))
                #histogram_file.write("%s : %s\n"%(cursor.fetchone()[1], str(counted[combination])))
                histogram_file.write("%s : %s\n"%(combination, str(counted[combination])))
            print("CPU PERCENT: %f"%curproc.cpu_percent())
            print(psutil.virtual_memory())
        with open("%s/cumulative_%dr_summary"%(DATA_DIRECTORY, num_resolvers),"w") as histogram_summary:
            histogram_summary.write("occurences_of_a_group, frequency\n")
            for count in distribution:
                histogram_summary.write("%d,%d\n"%(count,distribution[count]))
        pass
    cumulative_database.close()

def calculate_all_old(num_resolvers=2):
    cumulative_count=[]
    cumulative_database = sqlite3.connect("db/combination_database_%dr"%num_resolvers)
    cursor = cumulative_database.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS resolution_combinations (tuple_hash VARCHAR(30), tuple_str VARCHAR(100))''')
    curproc=psutil.Process()
    try:
        ind=0
        while True:
            path="%s/%d/dns_main"%(DATA_DIRECTORY, ind)
            combinations = extract_combinations(path, num_resolvers)
            for combination in combinations:
                combination = tuple(sorted(combination))
                tuple_hash = hash(combination)
                tuple_str = ",".join(combination)
                #cursor.execute('''INSERT OR IGNORE INTO resolution_combinations VALUES(?, ?)''', (tuple_hash,tuple_str))
                cumulative_count.append(tuple_hash)
            print("PROGRESS %d"%ind)
            ind+=1
            print("CPU PERCENT: %f"%curproc.cpu_percent())
            print(psutil.virtual_memory())
    except IOError:
        cumulative_database.commit()
        distribution={}
        with open("%s/cumulative_%dr_data"%(DATA_DIRECTORY, num_resolvers),"w") as histogram_file:
            counted = Counter(cumulative_count)
            len_counted=len(counted)
            #progress=0
            #ind=0.0
            for combination in counted:
                distribution[counted[combination]] = 1 if counted[combination] not in distribution else distribution[counted[combination]] + 1
                #if (ind/len_counted * 20 > progress):
                #    print("%d percent of the way there\n"%(progress*5))
                #    progress+=1
                #ind+=1
                #cursor.execute('''SELECT * FROM resolution_combinations WHERE tuple_hash = ? LIMIT 1''', (combination,))
                #histogram_file.write("%s : %s\n"%(cursor.fetchone()[1], str(counted[combination])))
                histogram_file.write("%s : %s\n"%(combination, str(counted[combination])))
            print("CPU PERCENT: %f"%curproc.cpu_percent())
            print(psutil.virtual_memory())
        with open("%s/cumulative_%dr_summary"%(DATA_DIRECTORY, num_resolvers),"w") as histogram_summary:
            histogram_summary.write("occurences_of_a_group, frequency\n")
            for count in distribution:
                histogram_summary.write("%d,%d\n"%(count,distribution[count]))
        pass
    cumulative_database.close()

def pull_data(num_trials):
    ind=0
    with open("example_domains","r") as f:
        domains = f.readlines()
        try:
            os.mkdir(DATA_DIRECTORY)
        except Exception:
            pass
        for domain in domains:
            out_path="%s/%d"%(DATA_DIRECTORY, ind)
            try:
                os.mkdir(out_path)
            except Exception:
                pass
            raw_dump_path=test_domain(domain, out_path, num_trials)
            parse_dns_records(raw_dump_path, out_path)
            ind+=1

NUM_TRIALS = 1
NUM_RESOLVERS = 2
PULL_DATA = True
COUNT_DATA = True

def parse_args():
    for i in xrange(len(sys.argv)):
        if sys.argv[i] in ["--trials","-t"]:
            global NUM_TRIALS
            NUM_TRIALS = int(sys.argv[i+1])
        elif sys.argv[i] in ["--resolvers","-r"]:
            global NUM_RESOLVERS
            NUM_RESOLVERS = int(sys.argv[i+1])
        elif sys.argv[i] in ["--pull-only","-p"]:
            global COUNT_DATA
            COUNT_DATA = False
        elif sys.argv[i] in ["--count-only","-c"]:
            global PULL_DATA
            PULL_DATA = False

if __name__ == "__main__":
    parse_args()
    if PULL_DATA:
        print("Pulling data from internet using example_domains")
        pull_data(NUM_TRIALS)
    if COUNT_DATA:
        print("Using tcpout records to extract combinations")
        calculate_all(NUM_RESOLVERS)











