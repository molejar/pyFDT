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

import re
from string import printable

FDT_MAX_VERSION = 17

# DTB constants
DTB_HEADER_MAGIC = 0xD00DFEED
DTB_BEGIN_NODE = 0x1
DTB_END_NODE = 0x2
DTB_PROP = 0x3
DTB_NOP = 0x4
DTB_END = 0x9


def isstring(data):
    """ Check property string validity """
    if not len(data):
        return None
    if data[-1] != 0:
        return None
    pos = 0
    while pos < len(data):
        posi = pos
        while pos < len(data) and data[pos] != 0 and data[pos] in printable.encode() and data[pos] not in (ord('\r'), ord('\n')):
            pos += 1
        if data[pos] != 0 or pos == posi:
            return None
        pos += 1
    return True


def extract_string(data, offset=0):
    """ Extract string """
    str_end = offset
    while data[str_end] != 0:
        str_end += 1
    return data[offset:str_end].decode("ascii")


def line_offset(tabsize, offset, string):
    offset = " " * (tabsize * offset)
    return offset + string


def get_version_info(text):
    ret = dict()
    for line in text.split('\n'):
        line = line.rstrip('\0')
        if line and line.startswith('/ {'):
            break
        if line and line.startswith('//'):
            line = line.split()
            if line[1] in ('version', 'last_comp_version', 'boot_cpuid_phys'):
                ret[line[1]] = int(line[2], 0)
    return ret


def strip_comments(text):
    return re.sub('//.*?(\r\n?|\n)|/\*.*?\*/', '', text, flags=re.S)


def split_to_lines(text):
    lines = []
    mline = str()
    for line in text.split('\n'):
        line = line.replace('\t', ' ')
        line = line.rstrip('\0')
        line = line.rstrip(' ')
        line = line.lstrip(' ')
        if not line or line.startswith('/dts-'):
            continue
        if line.endswith('{') or line.endswith(';'):
            line = line.replace(';', '')
            lines.append(mline + line)
            mline = str()
        else:
            mline += line

    return lines

