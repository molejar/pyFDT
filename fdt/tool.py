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


# Base options
@click.group(context_settings=dict(help_option_names=['-?', '--help']), help=DESCRIP)
@click.version_option(VERSION, '-v', '--version')
def cli():
    click.echo()


@cli.command(short_help="Convert *.dtb to *.dts")
@click.argument('infile', nargs=1, type=click.Path(exists=True))
@click.option('-t', '--tabsize', type=click.INT, default=4, show_default=True, help="Tabulator Size")
@click.option('-o', '--outfile', type=click.Path(), default=None, help="Output path/file name (*.dts)")
def todts(outfile, infile, tabsize):
    """ Convert device tree binary blob (*.dtb) into readable text file (*.dts) """
    fdt_obj = None

    if outfile is None:
        outfile = os.path.splitext(os.path.basename(infile))[0] + ".dts"

    try:
        with open(infile, 'rb') as f:
            try:
                fdt_obj = fdt.parse_dtb(f.read())
            except:
                raise Exception('Not supported file format: {}'.format(infile))

        with open(outfile, 'w') as f:
            f.write(fdt_obj.to_dts(tabsize))

    except Exception as e:
        click.echo(" Error: {}".format(str(e) if str(e) else "Unknown!"))
        sys.exit(ERROR_CODE)

    click.secho(" DTS saved as: %s" % outfile)


@cli.command(short_help="Convert *.dts to *.dtb")
@click.argument('infile', nargs=1, type=click.Path(exists=True))
@click.option('-v', '--version', type=click.INT, default=None, help="DTB Version")
@click.option('-l', '--lcversion', type=click.INT, default=None, help="DTB Last Compatible Version")
@click.option('-c', '--cpuid', type=click.INT, default=None, help="Boot CPU ID")
@click.option('-a', '--align', type=click.INT, default=None, help="Make the blob align to the <bytes>")
@click.option('-p', '--padding', type=click.INT, default=None, help="Add padding to the blob of <bytes> long")
@click.option('-s', '--size', type=click.INT, default=None, help="Make the blob at least <bytes> long")
@click.option('-o', '--outfile', type=click.Path(), default=None, help="Output path/file name (*.dtb)")
def todtb(outfile, infile, version, lcversion, cpuid, align, padding, size):
    """ Convert device tree as readable text file (*.dts) into binary blob (*.dtb) """
    fdt_obj = None

    if outfile is None:
        outfile = os.path.splitext(os.path.basename(infile))[0] + ".dtb"

    try:
        if version is not None and version > fdt.Header.MAX_VERSION:
            raise Exception("DTB Version must be lover or equal {} !".format(fdt.Header.MAX_VERSION))

        with open(infile, 'r') as f:
            try:
                fdt_obj = fdt.parse_dts(f.read(), os.path.dirname(infile))
            except:
                raise Exception('Not supported file format: {}'.format(infile))

        raw_data = fdt_obj.to_dtb(version, lcversion, cpuid)

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
        click.echo(" Error: {}".format(str(e) if str(e) else "Unknown!"))
        sys.exit(ERROR_CODE)

    click.secho(" DTB saved as: %s" % outfile)


@cli.command(short_help="Merge two and more *.dtb or *.dts files")
@click.argument('outfile', nargs=1, type=click.Path())
@click.argument('infiles', nargs=-1, type=click.Path(exists=True))
@click.option('-t', '--tabsize', type=click.INT, default=4, show_default=True, help="Tabulator Size")
@click.option('-i', '--intype', type=click.Choice(['auto', 'dts', 'dtb']),
              default='auto', show_default=True, help="Input file type")
def merge(outfile, infiles, tabsize, intype):
    """ Merge two and more *.dtb or *.dts files into one *.dts file """
    def open_fdt(file_path, file_type):
        if file_type == 'auto':
            if file_path.endswith(".dtb"):
                file_type = 'dtb'
            elif file_path.endswith(".dts"):
                file_type = 'dts'
            else:
                raise Exception('Not supported file extension: {}'.format(file_path))
        try:
            if file_type == 'dtb':
                with open(file_path, 'rb') as f:
                    obj = fdt.parse_dtb(f.read())
            else:
                with open(file_path, 'r') as f:
                    obj = fdt.parse_dts(f.read(), os.path.dirname(file_path))
        except Exception as e:
            raise Exception('Not supported file format: {} {}'.format(file_path, str(e)))

        return obj

    fdt_obj = None

    if not infiles:
        click.echo("Usage: pydtc todtb [OPTIONS] [INFILES]...")
        click.echo("\nError: Missing argument \"infiles\"")
        sys.exit(ERROR_CODE)

    if len(infiles) < 2:
        click.echo("Usage: pydtc todtb [OPTIONS] [INFILES]...")
        click.echo("\nError: Minimum is two \"infiles\"")
        sys.exit(ERROR_CODE)

    try:
        for file in infiles:
            if fdt_obj is None:
                fdt_obj = open_fdt(file, intype)
            else:
                fdt_obj.merge(open_fdt(file, intype))

        with open(outfile, 'w') as f:
            f.write(fdt_obj.to_dts(tabsize))

    except Exception as e:
        click.echo(" Error: {}".format(str(e) if str(e) else "Unknown!"))
        sys.exit(ERROR_CODE)

    click.secho(" Merge output saved as: %s" % outfile)


@cli.command(short_help="Compare two *.dtb or *.dts files")
@click.argument('file1', nargs=1, type=click.Path(exists=True))
@click.argument('file2', nargs=1, type=click.Path(exists=True))
@click.option('-t', '--intype', type=click.Choice(['auto', 'dts', 'dtb']),
              default='auto', show_default=True, help="Input file type")
@click.option('-o', '--outdir', type=click.Path(), default=None, help="Output directory/path [default: diff_out]")
def diff(file1, file2, intype, outdir):
    """ Compare two *.dtb or *.dts files """

    def open_fdt(file_path, file_type):
        if file_type == 'auto':
            if file_path.endswith(".dtb"):
                file_type = 'dtb'
            elif file_path.endswith(".dts"):
                file_type = 'dts'
            else:
                raise Exception('Not supported file extension: {}'.format(file_path))
        try:
            if file_type == 'dtb':
                with open(file_path, 'rb') as f:
                    obj = fdt.parse_dtb(f.read())
            else:
                with open(file_path, 'r') as f:
                    obj = fdt.parse_dts(f.read(), os.path.dirname(file_path))
        except:
            raise Exception('Not supported file format: {}'.format(file_path))

        return obj

    try:
        # load input files
        fdt1 = open_fdt(file1, intype)
        fdt2 = open_fdt(file2, intype)
        # compare it
        diff = fdt.diff(fdt1, fdt2)
        if diff[0].empty:
            click.echo(" Input files are completely different !")
            sys.exit()
        # create output directory
        if outdir is None:
            outdir = "diff_out"
        os.makedirs(outdir, exist_ok=True)
        # save the diff
        file_name = (
            "same.dts",
            os.path.splitext(os.path.basename(file1))[0] + ".dts",
            os.path.splitext(os.path.basename(file2))[0] + ".dts")
        for index, obj in enumerate(diff):
            if not obj.empty:
                with open(os.path.join(outdir, file_name[index]), 'w') as f:
                    f.write(obj.to_dts())

    except Exception as e:
        click.echo(" Error: {}".format(str(e) if str(e) else "Unknown!"))
        sys.exit(ERROR_CODE)

    click.secho(" Diff output saved into: %s" % outdir)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
