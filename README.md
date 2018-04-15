# Flattened Device Tree Python Module 

[![Build Status](https://travis-ci.org/molejar/pyFDT.svg?branch=master)](https://travis-ci.org/molejar/pyFDT)
[![Coverage Status](https://coveralls.io/repos/github/molejar/pyFDT/badge.svg)](https://coveralls.io/github/molejar/pyFDT)
[![PyPI Status](https://img.shields.io/pypi/v/fdt.svg)](https://pypi.python.org/pypi/fdt)
[![Python Version](https://img.shields.io/pypi/pyversions/fdt.svg)](https://www.python.org)

This python module is usable for manipulation with [Device Tree Data](https://www.devicetree.org/) and primary was 
created for [i.MX Smart-Boot Tool](https://github.com/molejar/pyIMX/blob/master/doc/imxsb.md)

> Some parts in this module have been inspired from: https://github.com/superna9999/pyfdt project.


Dependencies
------------

- [Python](https://www.python.org) - Python 3.x interpreter
- [Click](http://click.pocoo.org/6) - Python package for creating beautiful command line interface.

Installation
------------

``` bash
    $ pip install fdt
```

To install the latest version from master branch execute in shell following command:

``` bash
    $ pip install -U https://github.com/molejar/pyFDT/archive/master.zip
```

In case of development, install it from cloned sources:

``` bash
    $ git clone https://github.com/molejar/pyFDT.git
    $ cd pyFDT
    $ pip install -U -e .
```

**NOTE:** You may run into a permissions issues running these commands. Here are a few options how to fix it:

1. Run with `sudo` to install `fdt` and dependencies globally
2. Specify the `--user` option to install locally into your home directory (export "~/.local/bin" into PATH variable if haven't).
3. Run the command in a [virtualenv](https://virtualenv.pypa.io/en/latest/) local to a specific project working set.


Usage
-----

The API of **fdt** module is intuitive and implementing all general requirements for manipulation with FDT Nodes, Properties and dts/dtb files.

```python
    import fdt
    
    #-----------------------------------------------
    # convert *.dtb to *.dts
    # ----------------------------------------------
    with open("example.dtb", "rb") as f:
        dtb_data = f.read()
        
    dt1 = fdt.parse_dtb(dtb_data)
    
    with open("example.dts", "w") as f:
        f.write(dt1.to_dts())
        
    #-----------------------------------------------
    # convert *.dts to *.dtb
    # ----------------------------------------------
    with open("example.dts", "r") as f:
        dts_text = f.read()
        
    dt2 = fdt.parse_dts(dts_text)
    
    with open("example.dtb", "wb") as f:
        f.write(dt2.to_dtb(version=17))
        
    #-----------------------------------------------
    # Add Property and Node into dt2
    # ----------------------------------------------
    node = fdt.Node('test_node')
    node.append(fdt.Property('basic_property'))
    node.append(fdt.PropStrings('string_property', 'value1', 'value2'))
    node.append(fdt.PropWords('words_property', 0x1000, 0x80000000, wsize=32))
    node.append(fdt.PropBytes('bytes_property', data=[0, 200, 12]))
    dt2.add_item(node)
    
    #-----------------------------------------------
    # merge dt2 into dt1
    # ----------------------------------------------
    dt1.merge(dt2)

    with open("merged.dtb", "wb") as f:
        f.write(dt1.to_dtb(version=17))
        
    #-----------------------------------------------
    # diff two fdt objects
    # ----------------------------------------------
    out = fdt.diff(dt1, dt2)
    
    print(out[0]) # same in dt1 and dt2
    print(out[1]) # specific for dt1
    print(out[2]) # specific for dt2
```

[ pydtc ] Tool
--------------

The python device tree converter **pydtc** is a tool for conversion *.dts to *.dtb and vice versa. Is distributed
together with **fdt** module. This tool can be in some cases used as replacement of [device tree compiler](https://git.kernel.org/pub/scm/utils/dtc/dtc.git).  

```bash
  $ pydtc -?

Usage: pydtc [OPTIONS] COMMAND [ARGS]...

  Device Tree Converter (DTC) is a tool for converting device tree binary
  blob (*.dtb) to readable text file (*.dts) and reverse

Options:
  -v, --version  Show the version and exit.
  -?, --help     Show this message and exit.

Commands:
  diff   Compare two *.dtb or *.dts files
  merge  Merge two and more *.dtb or *.dts files
  todtb  Convert *.dts to *.dtb
  todts  Convert *.dtb to *.dts
```


#### $ pydtc todts [OPTIONS] INFILE

Convert Device Tree in binary blob *.dtb to readable text file *.dts

**INFILE** - Single DTB file as *.dtb

##### options:
* **-t, --tabsize** - Tabulator Size
* **-o, --outfile** - Output path/file name (*.dts)
* **-?, --help** - Show help message and exit

##### Example:

``` bash
  $ pydtc todts test.dtb
    
    DTS saved as: test.dts
```

#### $ pydtc todtb [OPTIONS] INFILE

Convert Device Tree in readable text file *.dts to binary blob *.dtb

**INFILE** - Single DTS file as *.dts

##### options:
* **-v, --version** - DTB Version
* **-l, --lcversion** - DTB Last Compatible Version
* **-c, --cpuid** - Boot CPU ID
* **-a, --align** - Make the blob align to the <bytes>
* **-p, --padding** - Add padding to the blob of <bytes> long
* **-s, --size** - Make the blob at least <bytes> long
* **-o, --outfile** - Output path/file name (*.dtb)
* **-?, --help** - Show help message and exit

##### Example:

``` bash
  $ pydtc todtb -v 17 test.dts
  
    DTB saved as: test.dtb
```

#### $ pydtc merge [OPTIONS] OUTFILE [INFILES]

Merge two and more *.dtb or *.dts files into one *.dts file

**OUTFILE** - The output file name with *.dts extension <br>
**INFILES** - Two or more input files with *.dtb or *.dts extension

##### options:
* **-t, --tabsize** - Tabulator Size
* **-t, --intype** - Input file type: 'auto', 'dts', 'dtb' (default: auto)
* **-?, --help** - Show help message and exit

##### Example:

``` bash
  $ pydtc merge out.dts test1.dtb test2.dtb
    
    Merge output saved as: out.dts
```

#### $ pydtc diff [OPTIONS] FILE1 FILE2

Compare two dtb/dts files and generate 3 dts files (same in 1 and 2, specific for 1, specific for 2)

**FILE1** - Input file 1 <br>
**FILE2** - Input file 2

##### options:
* **-t, --intype** - Input file type: 'auto', 'dts', 'dtb' (default: auto)
* **-o, --outdir** - Output directory/path (default: diff_out)
* **-?, --help** - Show help message and exit

##### Example:

``` bash
  $ pydtc diff test1.dtb test2.dtb
    
    Diff output saved into: diff_out
```
