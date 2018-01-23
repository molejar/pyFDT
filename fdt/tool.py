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

import os
import sys
import fdt
import click

# Application error code
ERROR_CODE = 1

# The version of u-boot tools
VERSION = fdt.__version__

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

        dt = fdt.parse_dtb(data)

        with open(outfile, 'w') as f:
            f.write(dt.to_dts(tabsize))

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
@click.option('-a', '--align', type=click.INT, default=None, help="Make the blob align to the <bytes>")
@click.option('-p', '--padding', type=click.INT, default=None, help="Add padding to the blob of <bytes> long")
@click.option('-s', '--size', type=click.INT, default=None, help="Make the blob at least <bytes> long")
def todtb(outfile, infiles, version, lcversion, cpuid, align, padding, size):
    """ Convert *.dts to *.dtb """
    try:
        dt = None

        if version is not None and version > fdt.Header.MAX_VERSION:
            raise Exception("DTB Version must be lover or equal {} !".format(fdt.Header.MAX_VERSION))

        if not isinstance(infiles, (list, tuple)):
            infiles = [infiles]
        for file in infiles:
            with open(file, 'r') as f:
                data = fdt.parse_dts(f.read(), os.path.dirname(file))
            if dt is None:
                dt = data
            else:
                dt.merge(data)

        raw_data = dt.to_dtb(version, lcversion, cpuid)

        if align is not None:
            if size is not None:
                raise Exception("The \"-a/--align\" option can't be used together with \"-s/--size\"")
            if not align % 2:
                raise Exception("The \"-a/--align\" option must be dividable with two !")
            if len(raw_data) % align:
                raw_data += bytes([0] * (len(raw_data) % align))

        if padding is not None:
            if align is not None:
                raise Exception("The \"-p/--padding\" option can't be used together with \"-a/--align\"")
            raw_data += bytes([0] * padding)

        if size is not None:
            if size < len(raw_data):
                raise Exception("The \"-s/--size\" option must be > {}".format(len(raw_data)))
            raw_data += bytes([0] * (size - len(raw_data)))

        with open(outfile, 'wb') as f:
            f.write(raw_data)

    except Exception as e:
        click.echo(" ERROR: {}".format(str(e) if str(e) else "Unknown!"))
        sys.exit(ERROR_CODE)

    click.secho(" DTB saved as: %s" % outfile)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
