#!/usr/bin/env python

# Copyright 2017 Martin Olejar
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import click
import pyfdt

# Application error code
ERROR_CODE = 1

# The version of u-boot tools
VERSION = pyfdt.__version__

# Short description of DTC tool
DESCRIP = (
    "Device Tree Converter tool for converting FDT blob (*.dtb) to readable text file (*.dts) and reverse"
)


# DTC: Base options
@click.group(context_settings=dict(help_option_names=['-?', '--help']), help=DESCRIP)
@click.version_option(VERSION, '-v', '--version')
def cli():
    click.echo()


# DTC: Convert DT in binary blob (*.dtb) to readable text file (*.dts)
@cli.command(short_help="Convert *.dtb to *.dts")
@click.argument('outfile', nargs=1, type=click.Path())
@click.argument('infile', nargs=1, type=click.Path(exists=True))
@click.option('-t', '--tabsize', type=click.INT, default=4, show_default=True, help="Tabulator Size")
def todts(outfile, infile, tabsize):
    """ Convert *.dtb to *.dts """
    try:
        with open(infile, 'rb') as f:
            data = f.read()

        fdt = pyfdt.parse_dtb(data)

        with open(outfile, 'w') as f:
            f.write(fdt.to_dts(tabsize))

    except Exception as e:
        click.echo(" ERROR: {}".format(str(e) if str(e) else "Unknown!"))
        sys.exit(ERROR_CODE)

    click.secho(" DTS saved as: %s" % outfile)


# DTC: Convert DT in readable text file (*.dts) to binary blob (*.dtb)
@cli.command(short_help="Convert *.dts to *.dtb")
@click.argument('outfile', nargs=1, type=click.Path())
@click.argument('infiles', nargs=-1, type=click.Path(exists=True))
@click.option('-v', '--version', type=click.INT, default=None, help="DTB Version")
@click.option('-l', '--lcversion', type=click.INT, default=None, help="DTB Last Compatible Version")
@click.option('-c', '--cpuid', type=click.INT, default=None, help="Boot CPU ID")
def todtb(outfile, infiles, version, lcversion, cpuid):
    """ Convert *.dts to *.dtb """
    try:
        fdt = None

        if version is not None and version > pyfdt.FDT_MAX_VERSION:
            raise Exception("DTB Version must be lover or equal {} !".format(pyfdt.FDT_MAX_VERSION))

        if not isinstance(infiles, (list, tuple)):
            infiles = [infiles]
        for file in infiles:
            with open(file, 'r') as f:
                data = pyfdt.parse_dts(f.read())
            if fdt is None:
                fdt = data
            else:
                fdt.merge(data)

        with open(outfile, 'wb') as f:
            f.write(fdt.to_dtb(version, lcversion, cpuid))

    except Exception as e:
        click.echo(" ERROR: {}".format(str(e) if str(e) else "Unknown!"))
        sys.exit(ERROR_CODE)

    click.secho(" DTB saved as: %s" % outfile)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
