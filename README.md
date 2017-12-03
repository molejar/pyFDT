# pyFDT: Flattened Device Tree Python Module 

> Some parts in this module have been reused from https://github.com/superna9999/pyfdt project.

This python module is usable for manipulation with Device Tree Data.

Dependencies
------------

- [Python 3](https://www.python.org) - The interpreter
- [Click](http://click.pocoo.org/6) - Python package for creating beautiful command line interface.

Installation
------------

To install the latest version from master branch execute in shell following command:

``` bash
    $ pip3 install -U https://github.com/molejar/pyFDT/archive/master.zip
```

In case of development, install it from cloned sources:

``` bash
    $ git clone https://github.com/molejar/pyFDT.git
    $ cd pyFDT
    $ pip3 install -U -e .
```

**NOTE:** You may run into a permissions issues running these commands. Here are a few options how to fix it:

1. Run with `sudo` to install pyIMX and dependencies globally
2. Specify the `--user` option to install locally into your home directory (export "~/.local/bin" into PATH variable if haven't).
3. Run the command in a [virtualenv](https://virtualenv.pypa.io/en/latest/) local to a specific project working set.


Usage
-----

```python
    import pyfdt
    
    #-----------------------------------------------
    # convert *.dtb to *.dts
    # ----------------------------------------------
    with open("example.dtb", "rb") as f:
        dtb_data = f.read()
        
    fdt = pyfdt.parse_dtb(dtb_data)
    
    with open("example.dts", "w") as f:
        f.write(fdt.to_dts())
        
    #-----------------------------------------------
    # convert *.dts to *.dtb
    # ----------------------------------------------
    with open("example.dts", "r") as f:
        dts_text = f.read()
        
    fdt = pyfdt.parse_dts(dts_text)
    
    with open("example.dtb", "wb") as f:
        f.write(fdt.to_dtb(version=17))
```

pydtc Tool
----------

The python device tree converter **pydtc** is partly a replacement of the device tree compiler tool [**dtc**](https://git.kernel.org/pub/scm/utils/dtc/dtc.git).  

#### $ pydtc todts OUTFILE INFILE

Convert Device Tree in binary blob (*.dtb) to readable text file (*.dts)

**OUTFILE** - The path and name of output file *.dts <br>
**INFILE** - The path and name of input file *.dtb <br>

##### options:
* **-t, --tabsize** - Tabulator Size
* **-?, --help** - Show help message and exit

##### Example:

``` bash
  $ pydtc todts output.dts input.dtb                                                                                               

    DTS saved as: output.dts
```

#### $ pydtc todtb OUTFILE INFILES

Convert Device Tree in readable text file (*.dts) to binary blob (*.dtb)

> If used more than one input file, all will be merged into one *.dtb

**OUTFILE** - The path and name of output file *.dtb <br>
**INFILES** - List of input files *.dts <br>

##### options:
* **-v, --version** - DTB Version
* **-l, --lcversion** - DTB Last Compatible Version
* **-c, --cpuid** - Boot CPU ID
* **-?, --help** - Show help message and exit

##### Example:

``` bash
  $ pydtc todtb -v 17 output.dtb input.dts                                                                                               

    DTB saved as: output.dtb
```