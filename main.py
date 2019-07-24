import sys, os
import time
import counter
import crawler

DATA_DIRECTORY="tcpout"

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
            raw_dump_path=crawler.test_domain(domain, out_path, num_trials)
            crawler.parse_dns_records(raw_dump_path, out_path)
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
    starttime = time.clock()
    parse_args()
    if PULL_DATA:
        print("Pulling data from internet using example_domains")
        pull_data(NUM_TRIALS)
    if COUNT_DATA:
        print("Using tcpout records to extract combinations")
        counter.calculate_all(NUM_RESOLVERS)
    endtime = time.clock()
    print("Runtime: %f ms"%(endtime-starttime))










