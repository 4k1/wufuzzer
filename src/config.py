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

import yaml

class ConfigFile():

    yml = None
    last_confid = "default"

    def get_yml(self):
        return self.yml

    def load_config(self):
        confs = []
        
        # load config
        try:
            f = open("wufuzzer.yml")
            self.yml = yaml.load(f, Loader=yaml.SafeLoader)
            f.close()
        except:
            print ("[-] Missing config to read 'wufuzzer.yml'.")
            exit(-1)
        
        # check version
        if str(self.get_config("version", "1")) != "2":
            print ("[-] Configuration 'wufuzzer.yml' version mismatch. version = " + str(get_config("version", "1")))
            exit(-1)
        
    def get_config(self, key, default=None):
        if key in self.yml["core"]:
            if type(self.yml["core"][key]) is int:
                return int(self.yml["core"][key])
            else:
                return str(self.yml["core"][key])
        elif default == None:
            raise
        else:
            return default

    def is_exists_user_config(self, confid):
        try:
            _ = self.yml["config"][confid]
            self.last_confid = confid
            return True
        except:
            return False

    def get_user_config(self, key, default=None):
        if self.yml["config"][self.last_confid] == None:
            None
        
        elif key in self.yml["config"][self.last_confid]:
            return self.yml["config"][self.last_confid][key]
            
        if default == None:
            raise
        else:
            return default

