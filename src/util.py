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

import os
import datetime
import threading

class Logging():
    
    logmode = False
    
    def __init__(self):
        self.__lock = threading.Lock()
        
        # create dir
        projdir     = "proj_" + datetime.datetime.today().strftime("%Y%m%d_%H%M%S")
        os.mkdir(projdir)
        
        self.__fn   = projdir + "/" + datetime.datetime.today().strftime("%Y%m%d_%H%M%S_#")
    
    def get_basename(self):
        return self.__fn
    
    def set_logging_mode(self, logmode):
        self.logmode = logmode
    
    def log(self, tid, value):
        if self.logmode:
            return
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
