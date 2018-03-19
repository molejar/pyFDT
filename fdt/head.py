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

from struct import unpack_from, pack


########################################################################################################################
# Binary Blob Constants
########################################################################################################################

DTB_BEGIN_NODE = 0x1
DTB_END_NODE = 0x2
DTB_PROP = 0x3
DTB_NOP = 0x4
DTB_END = 0x9


########################################################################################################################
# Header Class
########################################################################################################################

class Header(object):

    MIN_SIZE = 4 * 7
    MAX_SIZE = 4 * 10

    MAX_VERSION = 17

    MAGIC_NUMBER = 0xD00DFEED

    @property
    def magic(self):
        return self.MAGIC_NUMBER

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        if value > self.MAX_VERSION:
            raise ValueError("Not supported version, use: 0 - 17 !")
        # update size and padding
        self._size = self.MIN_SIZE
        if value >= 2:
            self._size += 4
        if value >= 3:
            self._size += 4
        if value >= 17:
            self._size += 4
        self._padding = 8 - (self._size % 8) if self._size % 8 != 0 else 0
        self._version = value
        self.last_comp_version = value - 1

    @property
    def size(self):
        return self._size + self._padding

    @property
    def padding(self):
        return self._padding

    def __init__(self):
        # private variables
        self._version = None
        self._size = 0
        self._padding = 0
        # public variables
        self.total_size = 0
        self.off_dt_struct = 0
        self.off_dt_strings = 0
        self.off_mem_rsvmap = 0
        self.last_comp_version = 0
        # version depend variables
        self.boot_cpuid_phys = 0
        self.size_dt_strings = None
        self.size_dt_struct = None

    def __str__(self):
        return '<FDT-v{}, size: {}>'.format(self.version, self.size)

    def info(self):
        nfo = 'FDT Header:'
        nfo += '- Version: {}'.format(self.version)
        nfo += '- Size:    {}'.format(self.size)
        return nfo

    @classmethod
    def parse(cls, data, offset=0):
        data_offset = cls.MIN_SIZE
        if len(data) < (offset + data_offset):
            raise ValueError("Data size too small !")

        header_vals = unpack_from('>7I', data, offset)
        if header_vals[0] != cls.MAGIC_NUMBER:
            raise Exception('Invalid Magic')
        if header_vals[5] > cls.MAX_VERSION:
            raise Exception('Invalid Version {}'.format(header_vals[5]))
        if header_vals[6] > cls.MAX_VERSION - 1:
            raise Exception('Invalid last compatible Version {}'.format(header_vals[6]))

        header = cls()
        header.total_size = header_vals[1]
        header.off_dt_struct = header_vals[2]
        header.off_dt_strings = header_vals[3]
        header.off_mem_rsvmap = header_vals[4]
        header.version = header_vals[5]
        header.last_comp_version = header_vals[6]

        if header.version >= 2:
            header.boot_cpuid_phys = unpack_from('>I', data, offset + data_offset)[0]
            data_offset += 4

        if header.version >= 3:
            header.size_dt_strings = unpack_from('>I', data, offset + data_offset)[0]
            data_offset += 4

        if header.version >= 17:
            header.size_dt_struct = unpack_from('>I', data, offset + data_offset)[0]
            data_offset += 4

        return header

    def export(self):
        if self.version is None:
            raise Exception("Header Version must be specified !")

        blob = pack('>7I', self.magic, self.total_size, self.off_dt_struct, self.off_dt_strings,
                    self.off_mem_rsvmap, self.version, self.last_comp_version)
        if self.version >= 2:
            blob += pack('>I', self.boot_cpuid_phys)
        if self.version >= 3:
            blob += pack('>I', self.size_dt_strings)
        if self.version >= 17:
            blob += pack('>I', self.size_dt_struct)
        if self.padding:
            blob += bytes([0] * self.padding)

        return blob
