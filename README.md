# Web URL Fuzzer - wufuzzer

[![Python3](https://img.shields.io/badge/python-3.x-green.svg)](https://img.shields.io/badge/python-3.x-green.svg)
[![category](https://img.shields.io/badge/Category-WebAssessment-blue.svg)](https://img.shields.io/badge/Category-WebAssessment-blue.svg)

wufuzzer is very simple URL fuzzer to assess unnecessary files running on Python3 for all professionals of web security assessment.

## Features

* Simple scanning listed directories and files on specified files.
* Fast scanning with multiple threads and auto-retry when any errors occurred.
* Dump scanned logs.
* Graphical interface shows progresses clearly understandable.
* Scanning step by step a path based on a separator.

## System requirements

* Python3
* requests (pip), yaml (pip)
* (Optional) fuzzdb database as a list of well-known directories and files to scan.

# Usage
```
$ python3 ./wufuzzer.py http://example.com/
```

Demonstrated console:
![file](https://github.com/4k1/wufuzzer/blob/master/demo.png?raw=true)

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

Put some database directories on wufuzzer.yml.

```
# Web URL Fuzzer Configuration

# Core settings
core:
    # Scanner thread(s)
    # (default : 1)
    max_threads:        8
    
    # Interval second(s) per request. 
    # (default : 0)
    request_interval:   0
    
    # Retry interval second(s) when error has occurred.
    # (default : 10)
    retry_interval:     1
    
    # Except http response code(s) e.g. 400,404,500
    # (default : 404)
    except_http_codes:  400,402,404,405,406,407,408,409,410,411,412,413,414,415,416,417,421,422,423,424,426,451,500,501,502,503,504,505,506,507,508,509,510

    # db defines
    default_db:          default

# Default db
default:
    base:               /YOUR_FUZZDB_DIR/fuzzdb
    files:
          - file:           discovery/predictable-filepaths/KitchensinkDirectories.txt
            type:           dironly
            option:         dirs

          - file:           discovery/predictable-filepaths/Randomfiles.txt
            type:           mixed
            option:         fixed

          - file:           discovery/predictable-filepaths/UnixDotfiles.txt
            type:           mixed
            option:         fixed
```    

#### `core` Section

|Key|Description|
|-|-|
|max_threads      |Scanner threads.(Default: 1)                                                     |
|request_interval |An interval second(s) per request.(Default: 0)                                   |
|retry_interval   |Retry interval second(s) when error has occurred.(Default: 10)                   |
|except_http_codes|Except http response code(s).(Defalt: 404 only)                                  |
|default_db       |A default database id that scanner will be loaded automatically when it launched.|

#### database id Section

|Key|Description|
|-|-|
|id(e.g. default)|An unique id on this yaml.            |
|->base          |A base directory of database file(s). |
|->files         |(Files Entry)                         |
|->->file        |A database file path without the base.|
|->->type        |A file type of the file. It must be specified `dironly` or `mixed`.|
|->->option      |A method to load the database. It must be specified `dirs` or `fixed`.(If type is `dironly`, option must be setted `dirs`.)|

#### `type` Property

- `dironly` : Only directories in the file.
  -  e.g.
     ```
     test/
     data/
     debug/
     asset/
     cms/
       :
     ```

- `mixed` : Directories and Files in the file.
  - e.g.
    ```
    test/.gitconfig
    data/index.html
    debug/phpinfo.php
      :
    ```

#### `option` Property

- `dirs` : Scanner will be loaded it as a directories.
  - e.g.
    ```
    test.php         -> as a 'test.php/' directory pattern
    test/            -> as a 'test/' directory pattern
    test/test.d      -> as a 'test/test.d/' directory pattern
    ```

- `fixed` : Depends on its `type` option. Basically, scanner will be loaded it as a directory and file path pair.
  - e.g. (`type`=`mixed`)
    ```
    test.php         -> as a 'test.php' file pattern
    test/            -> as a 'test/' directory pattern
    test/test.d/test -> as a 'test/test.d/test' file pattern (fixed pair.)
    ```

  - e.g. (`type`=`dironly`)
    ```
    test.php         -> as a 'test.php/' directory pattern
    test/            -> as a 'test/' directory pattern
    test/test.d/test -> as a 'test/', a 'test/test.d/', a 'test/test.d/test/' directory pattern 
    ```
    - `type`=`dironly` and `option`=`fixed` case, the row of a database will be separated as a graded directory.

## How to scan effectually a target site

### Step 1: Set up the default databases.
- Refer to the above.

### Step 2: Make an URL list of the target site.
- e.g. (As the URL list is located `/home/foo/Desktop/urllist_example_com.txt`)
  ```
  http://example.com/
  http://example.com/products/index.html
  http://example.com/products/qa/qalist.html
  http://example.com/form/inquery.php
  http://example.com/login/login.php
  http://example.com/cms/products/users/index.php
    :
  ```

### Step 3: Add database entry to the `wufuzzer.yml`
- e.g.
  ```
  # Optional db
  sitedb:
      base:               /home/foo/Desktop/
      files:
            - file:           urllist_example_com.txt
              type:           mixed
              option:         dirs
  ```
- If you specified to use the `sitedb` when you call the scanner, it will be loaded the urllist file as a directory patterns. Therefore scanner is able to be checked all of actual directories on the target site.

### Step 4: Do the scan
- e.g.
  ```
  $ python3 ./wufuzzer.py -d sitedb http://example.com/
  ```
  - If you specified a parameter `-d {database-id}`, scanner will be extra loaded databases you specified.
