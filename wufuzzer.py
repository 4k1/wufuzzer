#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import threading
import time
import curses
import argparse
import datetime
import yaml

__PRODUCT_ID = "Web URL Fuzzer 1.0 (c) 4k1/wufuzzer"

fuzzdb_dirs  = ["/"]
fuzzdb_files = []

stdscr       = None
confyml      = None

class Logging():
    
    def __init__(self):
        self.__lock = threading.Lock()
        self.__fn   = datetime.datetime.today().strftime("%Y%m%d_%H%M%S_#")
    
    def get_basename(self):
        return self.__fn
    
    def log(self, tid, value):
        try:
            f = open(self.__fn + str(tid) + ".log", "a")
            f.write(value + '\r\n')
            f.close()
        except:
            None

    def warn(self, value):
        with self.__lock:
            try:
                f = open(self.__fn + "!.log", "a")
                f.write(value + '\r\n')
                f.close()
            except:
                None

def vsplit(iterable, n):
    return [iterable[x:x + n] for x in range(0, len(iterable), n)]

def load_config():
    confs = []
    try:
        f = open("wufuzzer.yml")
        global confyml
        confyml = yaml.load(f)
        f.close()
    except:
        print ("[-] Missing config to read 'wufuzzer.yml'.")
        exit(-1)
    
def get_config(key, default=None):
    if key in confyml["core"]:
        if type(confyml["core"][key]) is int:
            return int(confyml["core"][key])
        else:
            return str(confyml["core"][key])
    elif default == None:
        raise
    else:
        return default

def urled(p):
    if "://" in p:
        p = p[p.find("://")+3:]
        if "/" not in p:
            return ""
        else:
            p = p[p.find("/")+1:]
            if p.split() == "":
                return ""
            else:
                return p
    else:
        return p

def passed(p):
    if p == "/":
        return ""
    if p[0:1] == "/":
        p = p[1:]
    if p[-1:] != "/":
        return p + "/"
    return p

def filed(p):
    if p[0:1] == "/":
        p = p[1:]
    return p

def fuzzdb():
    global fuzzdb_dirs
    global fuzzdb_files
    
    default_db = ""
    try:
        default_db = confyml["core"]["default_db"]
    except:
        print ("[-] Missing config 'core.default_db'.")
        exit(-1)
        
    base = ""
    try:
        base = passed(confyml[default_db]["base"])
    except:
        print ("[*] Missing config '" + default_db + ".base'.")
        print ("[*] No default database.")
        return
    
    for deffile in confyml[default_db]["files"]:
        try:
            if deffile["option"] not in ["dirs","fixed"]:
                print ("[-] Unknown option '" + deffile["option"] + "'.") 
                raise()
            if deffile["type"] not in ["dironly","mixed"]:
                print ("[-] Unknown type '" + deffile["type"] + "'.") 
                raise()            
            
            f = open("/" + base + deffile["file"])
            dbrecords = f.readlines()
            f.close()
            
            for row in dbrecords:
                e = row.strip()
                e = urled(e)
                
                if (deffile["type"] == "dironly"):
                    fuzzdb_dirs.append(passed(e))
                elif(deffile["type"] == "mixed"):
                    if (deffile["option"] == "fixed"):
                        if (e[-1:] == "/"):
                            fuzzdb_dirs.append(passed(e))
                        else:
                            fuzzdb_files.append(e)
                    else:
                        if "/" in e:                            
                            pos = 0
                            while True:
                                ev = e[:e.find("/", pos)]
                                fuzzdb_dirs.append(passed(ev))
                                pos = e.find("/", pos)
                                if pos == -1:
                                    break
                                pos += 1

                        else:
                            fuzzdb_dirs.append(e)
                else:
                    print ("[-] Mismatch options.")
                    raise() 

        except:
            print ("[*] Error has occurred to read '" + "/" + base + deffile["file"] + "'. Skipped.")

    fuzzdb_dirs = list(set(fuzzdb_dirs))
    fuzzdb_files = list(set(fuzzdb_files)) 

class FuzzerRunner(threading.Thread):
    
    __target    = ""
    __dirs      = []
    __files     = []
    __stop      = False
    __stopped   = True
    __tid       = -1
    __status    = ""
    __log       = ""
    __logger    = None
    __nowcnt    = 0
    
    def __init__(self, dirs, files, tid, target, logger):
        super(FuzzerRunner, self).__init__()
        self.__dirs     = dirs
        self.__files    = files
        self.__tid      = tid
        self.__target   = target
        self.__logger   = logger
    
    def get_status(self):
        return self.__status
    
    def get_log(self):
        return self.__log
    
    def get_stopped(self):
        return self.__stopped
        
    def get_max(self):
        return len(self.__dirs) * len(self.__files) + len(self.__dirs)
    
    def get_now(self):
        return self.__nowcnt
    
    def stop(self):
        self.__stop = True
    
    def __scan(self, cpath):
        err_times = 0
        while True:
            if (self.__stop):
                self.__status = "[PAUSE]"
                self.__stopped = True
                return False     # Abort

            try:
                res = requests.head(passed(self.__target) + cpath, allow_redirects=False, headers={'Connection':'close'})
                rcode = res.status_code
                res.connection.close()
                
                self.__log = "#" + str(self.__tid) + " " + str(rcode) + " '" + passed(self.__target) + cpath + "'"
                if str(rcode) not in str(get_config("except_http_codes", 404)):
                    self.__logger.warn(self.__log)
                else:
                    self.__logger.log(self.__tid, self.__log)
                
                time.sleep(get_config("request_interval", 0))
                break
            
            except:
                err_times += 1
                self.__log = "Warning : Request failed (" + str(err_times) + " time(s).). '" + passed(self.__target) + cpath + "' - waiting " + str(get_config("retry_interval", 10)) + " sec..."
                self.__logger.log(self.__tid, self.__log)
                time.sleep(get_config("retry_interval", 10))
        
        return True     # Continue
    
    def run(self):
        self.__stop     = False
        self.__stopped  = False
        self.__status   = "[ RUN ]"
        self.__nowcnt   = 0
        
        for dv in sorted(self.__dirs):
            cpath = passed(dv)
            if not self.__scan(cpath):
                return
            self.__nowcnt += 1
            
            for fv in sorted(self.__files):
                cpath = passed(dv) + filed(fv)
                if not self.__scan(cpath):
                    return
                self.__nowcnt += 1

        self.__status = "[FINSH]"
        self.__stopped = True

def output_status(cnt, th):
    for i in range(0, cnt):
        
        (maxy, maxx) = stdscr.getmaxyx()
        
        if maxy > i + 4:
            stdscr.addstr(i + 2, 0, th[i].get_status() + " " + th[i].get_log(), curses.A_DIM)
            stdscr.clrtoeol()
        
        indic = "( " + str(th[i].get_now()) + " / " + str(th[i].get_max()) + " )"
        
        if maxy > i + 4:
            stdscr.addstr(i + 2, maxx - len(indic), indic, curses.A_DIM)
                
        stdscr.refresh()    

def fuzzer(target, logger):
    
    cnt = int(get_config('max_threads', 1))
    
    scnt_dir = int(len(fuzzdb_dirs) / cnt) + 1
    sdirs = vsplit(fuzzdb_dirs, scnt_dir)
    cnt = len(sdirs)
    
    th = {}
    
    for i in range(0, cnt):
        th[i] = FuzzerRunner(sdirs[i], fuzzdb_files, i, target, logger)
        th[i].start()
    
    output_status(cnt, th)
    
    while True:
        stdscr.timeout(1)
        try:
            c = stdscr.getch()
            if c == ord('p'):
                for i in range(0, cnt):
                    th[i].stop()
            elif c == ord('q'):
                all_stopped = True
                for i in range(0, cnt):
                    all_stopped = all_stopped and th[i].get_stopped()
                if (all_stopped):
                    break
                else:
                    for i in range(0, cnt):
                        th[i].stop()
        except:
            None
        output_status(cnt, th)
        time.sleep(0.1)

if __name__ == '__main__':
    
    print (__PRODUCT_ID)
    parser = argparse.ArgumentParser(description=__PRODUCT_ID)
    parser.add_argument("target")
    parser.add_argument("--no-execute", dest='noexec', action='store_true', default=False, help='Output fuzzer table only if this flag is set (default: False)')
    args = parser.parse_args()
    
    load_config()
    print ("[+] Loaded config.")
    fuzzdb()
    print ("[+] Loaded databases. ")
    print ("    " + str(len(fuzzdb_dirs)) + " dir(s), " + str(len(fuzzdb_files)) + " file(s).")

    if args.noexec:
        fn_key   = datetime.datetime.today().strftime("_%Y%m%d_%H%M%S_noexec_.txt")
        fn_dirs  = "./dirs" + fn_key
        fn_files = "./files" + fn_key
        fn_fuzz  = "./fuzz" + fn_key
        
        f = open(fn_dirs, 'w')
        for v in sorted(fuzzdb_dirs):
            f.write(v + "\r\n")
        f.close()
        
        f = open(fn_files, 'w')
        for v in sorted(fuzzdb_files):
            f.write(v + "\r\n")
        f.close()
        
        f = open(fn_fuzz, 'w')
        for v in fuzzdb_dirs:
            for w in fuzzdb_files:
                f.write(passed(v) +filed(w) + "\r\n")
        f.close()
        
        print ("[+] --no-execute : dirs  = " + fn_dirs)
        print ("[+] --no-execute : files = " + fn_files)
        print ("[+] --no-execute : fuzz  = " + fn_fuzz)
        print ("[ ] exit.")
        exit(0)

    logger = Logging()
    print ("[+] Logging started. basename=./" + logger.get_basename() )

    stdscr = curses.initscr()
    (maxy, maxx) = stdscr.getmaxyx()
    curses.noecho()
    curses.cbreak()

    stdscr.addstr(0, 0, __PRODUCT_ID, curses.A_DIM)
    stdscr.refresh()
    stdscr.addstr(maxy-1,  0, "q",     curses.A_REVERSE)
    stdscr.addstr(maxy-1,  2, "Quit",  curses.A_DIM)
    stdscr.addstr(maxy-1, 10, "p",     curses.A_REVERSE)
    stdscr.addstr(maxy-1, 12, "Pause", curses.A_DIM)
    stdscr.refresh()

    try:    
        fuzzer(args.target, logger)
    finally:    
        curses.nocbreak()
        stdscr.keypad(0)
        curses.echo()
        curses.endwin()
