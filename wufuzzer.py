#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import threading
import time
import curses
import argparse
import datetime

__PRODUCT_ID = "Web URL Fuzzer 1.0 (c) 4k1/wufuzzer"

confv        = {}

fuzzdb_dirs  = ["/"]
fuzzdb_files = []

stdscr       = None

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
        f = open("wufuzzer.conf")
        confs = f.readlines()
        f.close()
    except:
        return
    
    for l in confs:
        if l.find(" ") < 0:
            continue
        k = l[0:l.find(" ")].lower().strip()
        v = l[l.find(" ") + 1:].strip()
        if k[0:1] == "#":
            continue
    
        u = []
        if k in confv:
            u = confv[k]
        u.append(v)
        confv[k] = u
    
def get_config(key, default=None, index=0):
    if key in confv:
        if confv[key][index].isdigit():
            return int(confv[key][index])
        else:
            return confv[key][index]
    elif default == None:
        raise
    else:
        return default

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
    base = ""
    try:
        base = passed(confv["fuzzdb.base"][0])
    except:
        print ("[-] Missing read config 'fuzzdb.base'.")
        exit(-1)
    
    if "fuzzdb.default" not in confv:
        print ("[*] No default database.")
        return
        
    for deffile in confv["fuzzdb.default"]:
        try:
            ftype = deffile.split(",")[0].strip()
            fname = deffile.split(",")[1].strip()
            
            f = open("/" + base + fname)
            er = f.readlines()
            f.close()
            
            for e in er:
                e = e.strip()
                if (e[-1:] == "/" or ftype == "dir"):
                    fuzzdb_dirs.append(passed(e))
                else:
                    fuzzdb_files.append(e)
        except:
            print ("[*] Error has occurred to read '" + "/" + base + fname + "'. Skipped.")

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
        
        for dir in sorted(self.__dirs):
            cpath = passed(dir)
            if not self.__scan(cpath):
                return
            self.__nowcnt += 1
            
            for file in sorted(self.__files):
                cpath = passed(dir) + filed(file)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    args = parser.parse_args()

    load_config()
    print ("[+] Loaded config.")
    fuzzdb()
    print ("[+] Loaded databases. ")
    print ("    " + str(len(fuzzdb_dirs)) + " dir(s), " + str(len(fuzzdb_files)) + " file(s).")
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
