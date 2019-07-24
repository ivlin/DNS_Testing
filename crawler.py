import subprocess, os
import re
import time

#   SELENIUM
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


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

        #print("Sleep to give time for all packets to be collected\n")

        subprocess.check_call(["sudo","kill","-9",str(p.pid)])
        os.waitpid(p.pid, 0)
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
        #sudo_prompt = p.communicate(sudo_password + '\n')[1]

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