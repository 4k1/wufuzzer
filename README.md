[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/4k1/wufuzzer/blob/master/LICENSE)
# Web URL Fuzzer - wufuzzer

wufuzzer is very simple URL fuzzer to assess unnecessary files running on Python3.

## System requirements

* Python3
* (Optional) fuzzdb database as a list of well-known directories and files to scan.

# Usage
```
$ python3 ./wufuzzer.py http://example.com/
```

Demonstrated console:
![file](https://github.com/4k1/wufuzzer/blob/master/demo.png?raw=true)

## Features

* Simple scanning listed directories and files on specified files.
* Fast scanning with multiple threads and auto-retry when any errors occurred.
* Dump scanned logs.
* Graphical interface shows progresses clearly understandable.

## How to install

### Step 1: Getting wufuzzer

Shallow clone the source from github.

```
git clone --depth 1 https://github.com/4k1/wufuzzer.git
```

### Step 2: (Optional) Getting database

(e.g.) Shallow clone the database of Mozilla fuzzdb-project.

```
git clone --depth 1 https://github.com/fuzzdb-project/fuzzdb.git
```

### Step 3: Configure wufuzzer config

Put some database directories on wufuzzer.conf.

```
vi wufuzzer.conf
```

```
# Web URL Fuzzer Configuration

# Scanner thread(s)
# (default : 1)
max_threads             8

# Interval second(s) per request. 
# (default : 0)
request_interval        0

# Retry interval second(s) when error has occurred.
# (default : 10)
retry_interval          1

# Except http response code(s) e.g. 400,404,500
# (default : 404)
except_http_codes       400,402,404,405,406,407,408,409,410,411,412,413,414,415,416,417,421,422,423,424,426,451,500,501,502,503,504,505,506,507,508,509,510

# FuzzDB root directory
fuzzdb.base             /YOUR_FUZZDB_DIR/fuzzdb

# Default databases
fuzzdb.default          dir,discovery/predictable-filepaths/KitchensinkDirectories.txt
fuzzdb.default          mix,discovery/predictable-filepaths/Randomfiles.txt
fuzzdb.default          mix,discovery/predictable-filepaths/UnixDotfiles.txt
```    
- fuzzed.base : Location of your database.
- fuzzdb.default : List to load default.
    - dir : It will be loaded as directories database.
    - mix : It will be loaded as directories and files database.
