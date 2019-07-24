import sqlite3
import pickle
import psutil
import itertools
from collections import Counter

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
                for freq in xrange(len(cumulative_count)):
                    with open(cumulative_count[freq],"rb") as datafile_r:
                        occurence_hashes = pickle.load(datafile_r)
                    if tuple_hash in occurence_hashes:
                        occurence_hashes.remove(tuple_hash)
                        with open(cumulative_count[freq],"wb") as datafile_w:
                            pickle.dump(occurence_hashes, datafile_w)
                        if freq+1>=len(cumulative_count):
                            newname="%s/%d_occurrence.ptmp"%(DATA_DIRECTORY,freq+1)
                            cumulative_count.append(newname)
                            nextfile=open(newname,"wb")
                            nextset=set()
                        else:
                            with open(cumulative_count[freq+1],"rb") as nextfile:
                                nextset=pickle.load(nextfile)
                            nextfile=open(cumulative_count[freq+1],"wb")
                        nextset.add(tuple_hash)
                        pickle.dump(nextset,nextfile)
                        nextfile.close()
                        break
                else:
                    with open(cumulative_count[0],"rb") as datafile:
                        data=pickle.load(datafile)
                    data.add(tuple_hash)
                    with open(cumulative_count[0],"wb") as datafile:
                        pickle.dump(data,datafile)
            print("PROGRESS %d"%ind)
            ind+=1
            print("CPU PERCENT: %f"%curproc.cpu_percent())
            print(psutil.virtual_memory())

    except OSError:
        with open("%s/cumulative_%dr_summary"%(DATA_DIRECTORY, num_resolvers),"w") as histogram_summary:
            histogram_summary.write("occurences_of_a_group, frequency\n")
            with open("%s/cumulative_%dr_data"%(DATA_DIRECTORY, num_resolvers),"w") as histogram_file:
                for freq in xrange(len(cumulative_count)):

                    data = pickle.load(open(cumulative_count[freq], "rb"))

                    for group in data:
                        histogram_file.write("%d,%d\n"%(group,freq+1))
                    histogram_summary.write("%d,%d\n"%(freq+1,len(data)))
                print("CPU PERCENT: %f"%curproc.cpu_percent())
                print(psutil.virtual_memory())
        pass
    #cumulative_database.close()

def calculate_all(num_resolvers=2):
    cumulative_count=[set()]
    curproc=psutil.Process()
    try:
        ind=0
        while True:
            path="%s/%d/dns_main"%(DATA_DIRECTORY, ind)
            combinations = extract_combinations(path, num_resolvers)
            for combination in combinations:
                combination = tuple(sorted(combination))
                tuple_hash = hash(combination)
                for freq in xrange(len(cumulative_count)):
                    if tuple_hash in cumulative_count[freq]:
                        cumulative_count[freq].remove(tuple_hash)
                        if freq+1>=len(cumulative_count):
                            cumulative_count.append(set())
                        cumulative_count[freq+1].add(tuple_hash)
                        break
                else:
                    cumulative_count[0].add(tuple_hash)
            print("PROGRESS %d"%ind)
            ind+=1
            print("CPU PERCENT: %f"%curproc.cpu_percent())
            print(psutil.virtual_memory())
    except IOError:
        with open("%s/cumulative_%dr_summary"%(DATA_DIRECTORY, num_resolvers),"w") as histogram_summary:
            histogram_summary.write("occurences_of_a_group, frequency\n")
            with open("%s/cumulative_%dr_data"%(DATA_DIRECTORY, num_resolvers),"w") as histogram_file:
                for freq in xrange(len(cumulative_count)):
                    for group in cumulative_count[freq]:
                        histogram_file.write("%d,%d\n"%(group,freq+1))
                    histogram_summary.write("%d,%d\n"%(freq+1,len(cumulative_count[freq])))
                print("CPU PERCENT: %f"%curproc.cpu_percent())
                print(psutil.virtual_memory())
        pass
    #cumulative_database.close()

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
                cursor.execute('''INSERT OR IGNORE INTO resolution_combinations VALUES(?, ?)''', (tuple_hash,tuple_str))
                #cumulative_count.append(tuple_hash)
            cumulative_database.commit()
            print("PROGRESS %d"%ind)
            ind+=1
            print("CPU PERCENT: %f"%curproc.cpu_percent())
            print(psutil.virtual_memory())
    except IOError:
        #cumulative_database.commit()
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

