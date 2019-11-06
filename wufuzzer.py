#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# ==============================================================================
# MIT License
# 
# Copyright (c) 2017-2019 4k1
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

import requests
import threading
import time
import curses
import argparse

from src import config
from src import util

# disable InsecureRequestWarning
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

__PRODUCT_ID = "Web URL Fuzzer 2.0 (c) 4k1/wufuzzer"

fuzzdb_dirs  = ["/"]
fuzzdb_files = []

confid       = "default"
stdscr       = None
ymlobj       = None

def fuzzdb(adddb_list):    
    default_db = ""
    try:
        default_db = ymlobj.get_config("default_db")
        __fuzzdb_load(default_db)
    except:
        print ("[-] Missing config 'core.default_db'.")
        exit(-1)
    
    add_db = adddb_list.split(",")
    for add_db_name in add_db:
        if add_db_name.strip() == "":
            continue
        if __fuzzdb_load(add_db_name) == 1:
            print ("[-] Missing config '" + add_db_name + "'.")
            exit(-1)

def __fuzzdb_load(dbkey):
    global fuzzdb_dirs
    global fuzzdb_files
    
    base = ""
    try:
        base = util.passed(ymlobj.get_yml()[dbkey]["base"])
    except:
        print ("[*] Missing config '" + dbkey + ".base'.")
        return 1
    
    for deffile in ymlobj.get_yml()[dbkey]["files"]:
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
                e = util.urled(e)
                
                if (deffile["type"] == "dironly"):
                    fuzzdb_dirs.append(util.passed(e))
                elif(deffile["type"] == "mixed"):
                    if (deffile["option"] == "fixed"):
                        if (e[-1:] == "/"):
                            fuzzdb_dirs.append(util.passed(e))
                        else:
                            fuzzdb_files.append(e)
                    else:
                        if "/" in e:                            
                            pos = 0
                            while True:
                                ev = e[:e.find("/", pos)]
                                fuzzdb_dirs.append(util.passed(ev))
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

    print ("[+] Loaded database '" + dbkey + "'.")

    fuzzdb_dirs = list(set(fuzzdb_dirs))
    fuzzdb_files = list(set(fuzzdb_files)) 

class FuzzerRunner(threading.Thread):
    
    __target    = ""
    __dirs      = []
    __files     = []
    __stop      = False
    __stopped   = True
    __term      = False
    __tid       = -1
    __status    = ""
    __log       = ""
    __logger    = None
    __nowcnt    = 0
    
    def __init__(self, dirs, files, tid, target, logger):
        super(FuzzerRunner, self).__init__()
        self.started    = threading.Event()
        self.__dirs     = dirs
        self.__files    = files
        self.__tid      = tid
        self.__target   = target
        self.__logger   = logger
    
    def isStop(self):
        return self.__stop
    
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
    
    def cont(self):
        self.__stop = False
        self.__status = "[ RUN ]"
        self.__stopped = True
        self.started.set()

    def term(self):
        self.__term = True
        self.started.set()
    
    def __scan(self, cpath):
        err_times = 0
        v_proxies = ymlobj.get_user_config("proxies", {})
        v_headers = ymlobj.get_user_config("headers", {})
        v_method  = ymlobj.get_user_config("method", "get").lower()
        v_verify  = ymlobj.get_user_config("ssl_cert_verify", True)
        
        # scanning loop
        while True:
            
            # check stop status
            if (self.__stop):
                self.__status = "[PAUSE]"
                self.__stopped = True
                self.started.wait()     # suspend thread
                self.started.clear()

            # check termination status
            if (self.__term):
                return False            # exit thread

            try:
                res = None
                if v_method == "head":
                    res = requests.head(util.passed(self.__target) + cpath, allow_redirects=False, headers=v_headers, proxies=v_proxies, verify=v_verify)
                else:
                    res = requests.get(util.passed(self.__target) + cpath, allow_redirects=False, headers=v_headers, proxies=v_proxies, verify=v_verify)
                    
                rcode = res.status_code
                res.connection.close()
                
                self.__log = "#" + str(self.__tid) + " " + str(rcode) + " '" + util.passed(self.__target) + cpath + "'"
                if str(rcode) not in str(ymlobj.get_user_config("ignore_responses", 404)):
                    self.__logger.warn(self.__log)
                else:
                    self.__logger.log(self.__tid, self.__log)
                
                time.sleep(ymlobj.get_config("request_interval", 0))
                break
            
            except:
                err_times += 1
                self.__log = "Warning : Request failed (" + str(err_times) + " time(s).). '" + util.passed(self.__target) + cpath + "' - waiting " + str(ymlobj.get_config("retry_interval", 10)) + " sec..."
                self.__logger.log(self.__tid, self.__log)
                time.sleep(ymlobj.get_config("retry_interval", 10))
        
        return True     # Continue
    
    def run(self):
        self.__stop     = False
        self.__stopped  = False
        self.__status   = "[ RUN ]"
        self.__nowcnt   = 0
        
        for dv in sorted(self.__dirs):
            cpath = util.passed(dv)
            if not self.__scan(cpath):
                return
            self.__nowcnt += 1
            
            for fv in sorted(self.__files):
                cpath = util.passed(dv) + util.filed(fv)
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
    
    cnt = int(ymlobj.get_config('max_threads', 1))
    
    scnt_dir = int(len(fuzzdb_dirs) / cnt) + 1
    sdirs = util.vsplit(fuzzdb_dirs, scnt_dir)
    cnt = len(sdirs)
    
    th = {}
    
    def th_all_stop():
        for i in range(0, cnt):
            th[i].stop()
    
    def th_is_all_stopped():
        all_stopped = True
        for i in range(0, cnt):
            all_stopped = all_stopped and th[i].isStop()
        return all_stopped
    
    def th_all_terminate():
        for i in range(0, cnt):
            th[i].term()
    
    for i in range(0, cnt):
        th[i] = FuzzerRunner(sdirs[i], fuzzdb_files, i, target, logger)
        th[i].start()
    
    output_status(cnt, th)
    
    while True:
        stdscr.timeout(1)
        try:
            c = stdscr.getch()
            # p - pause
            if c == ord('p'):
                # stop all threads
                th_all_stop()

            # q - quit
            elif c == ord('q'):
                # terminate all threads after stop all
                if th_is_all_stopped():
                    th_all_terminate()
                    return
                else:
                    th_all_stop()
            
            # c - continue
            elif c == ord('c'):
                # continue all threads
                for i in range(0, cnt):
                    th[i].cont()

        except:
            None
            
        output_status(cnt, th)
        time.sleep(0.1)

if __name__ == '__main__':
    
    # ready parser
    print (__PRODUCT_ID)
    parser = argparse.ArgumentParser(description=__PRODUCT_ID)
    parser.add_argument("target")
    parser.add_argument("--no-execute", dest='noexec'  , action='store_true', default=False      , help='Output fuzzer table only if this flag is set (default: False)')
    parser.add_argument("--noout-ign",  dest='noourign', action='store_true', default=False      , help='Disable to output non-hit filelists (default: False)')
    parser.add_argument("-c"          , dest='config'  , action='store'     , default="default"  , help='Configuration ID (default: "default")')
    parser.add_argument("-d"          , dest='db'      , action='store'     , default=""         , help='Additional database name yaml defined.')
    args = parser.parse_args()
    
    # load yaml
    ymlobj = config.ConfigFile()
    ymlobj.load_config()
    print ("[+] Loaded config.")
    confid = str(args.config)
    
    # check config
    if not ymlobj.is_exists_user_config(confid):
        print ("[-] Unknown configure id '" + confid + "'.")
        exit(-1)
    
    # load fuzzdb
    fuzzdb(args.db)
    print ("[+] Loaded databases. ")
    print ("    " + str(len(fuzzdb_dirs)) + " dir(s), " + str(len(fuzzdb_files)) + " file(s).")

    # --no-execute
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
                f.write(util.passed(v) + util.filed(w) + "\r\n")
        f.close()
        
        print ("[+] --no-execute : dirs  = " + fn_dirs)
        print ("[+] --no-execute : files = " + fn_files)
        print ("[+] --no-execute : fuzz  = " + fn_fuzz)
        print ("[ ] exit.")
        exit(0)

    # start logging
    logger = util.Logging()
    print ("[+] Logging started. basename=./" + logger.get_basename() )
    logger.set_logging_mode(args.noourign)

    # switch screen
    stdscr = curses.initscr()
    (maxy, maxx) = stdscr.getmaxyx()
    curses.noecho()
    curses.cbreak()

    # on screen
    stdscr.addstr(0, 0, __PRODUCT_ID, curses.A_DIM)
    stdscr.refresh()
    stdscr.addstr(maxy-1,  0, "q",          curses.A_REVERSE)
    stdscr.addstr(maxy-1,  2, "Quit",       curses.A_DIM)
    stdscr.addstr(maxy-1, 10, "p",          curses.A_REVERSE)
    stdscr.addstr(maxy-1, 12, "Pause",      curses.A_DIM)
    stdscr.addstr(maxy-1, 20, "c",          curses.A_REVERSE)
    stdscr.addstr(maxy-1, 22, "Continue",   curses.A_DIM)
    stdscr.refresh()

    # start fuzzer
    try:    
        fuzzer(args.target, logger)
    finally:    
        curses.nocbreak()
        stdscr.keypad(0)
        curses.echo()
        curses.endwin()
