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

from .node import Node, Nop
from .prop import Property, PropBytes, PropWords, PropStrings
from .head import Header, DTB_BEGIN_NODE, DTB_END_NODE, DTB_NOP, DTB_PROP, DTB_END
from .misc import strip_comments, split_to_lines, get_version_info, extract_string

__author__  = "Martin Olejar"
__contact__ = "martin.olejar@gmail.com"
__version__ = "0.1.0"
__license__ = "Apache 2.0"
__status__  = "Development"
__all__     = [
    # FDT Classes
    'FDT',
    'Nop',
    'Node',
    'Header',
    'PropBytes',
    'PropWords',
    'PropStrings',
    # core methods
    'parse_dts',
    'parse_dtb'
]


class FDT(object):
    """ Flattened Device Tree Class """

    def __init__(self):
        self.header = Header()
        self.entries = []
        self.prenops = []
        self.postnops = []
        self.rootnode = None

    def info(self):
        pass

    def merge_entries(self, entries):
        if entries:
            for in_entry in entries:
                exist = False
                for index in range(len(self.entries)):
                    if self.entries[index]['address'] == in_entry['address']:
                        self.entries[index]['address'] = in_entry['size']
                        exist = True
                        break
                if not exist:
                    self.entries.append(in_entry)

    def merge_rootnode(self, node):
        self.rootnode.merge(node)

    def merge(self, fdt):
        if not isinstance(fdt, FDT):
            raise Exception("Error")
        if self.header.version is None:
            self.header = fdt.header
        else:
            if fdt.header.version is not None and \
               fdt.header.version > self.header.version:
                self.header.version = fdt.header.version
        self.merge_entries(fdt.entries)
        self.merge_rootnode(fdt.rootnode)

    def to_dts(self, tabsize=4):
        """Store FDT Object into string format (DTS)"""
        result = "/dts-v1/;\n"
        result += "// version: {}\n".format(self.header.version)
        result += "// last_comp_version: {}\n".format(self.header.last_comp_version)
        if self.header.version >= 2:
            result += "// boot_cpuid_phys: 0x{:X}\n".format(self.header.boot_cpuid_phys)
        result += '\n'
        if self.entries:
            for entry in self.entries:
                result += "/memreserve/ "
                result += "{:#x} ".format(entry['address']) if entry['address'] else "0 "
                result += "{:#x}".format(entry['size']) if entry['size'] else "0"
                result += ";\n"
        if self.prenops:
            result += '\n'.join([nop.to_dts(tabsize) for nop in self.prenops])
            result += '\n'
        if self.rootnode is not None:
            result += self.rootnode.to_dts(tabsize)
        if self.postnops:
            result += '\n'
            result += '\n'.join([nop.to_dts(tabsize) for nop in self.postnops])
        return result

    def to_dtb(self, version=None, last_comp_version=None, boot_cpuid_phys=None):
        """Export FDT Object into Binary Blob format (DTB)"""
        if self.rootnode is None:
            return None

        from struct import pack

        if version is not None:
            self.header.version = version
        if last_comp_version is not None:
            self.header.last_comp_version = last_comp_version
        if boot_cpuid_phys is not None:
            self.header.boot_cpuid_phys = boot_cpuid_phys
        if self.header.version is None:
            raise Exception("DTB Version must be specified !")

        blob_entries = bytes()
        if self.entries:
            for entry in self.entries:
                blob_entries += pack('>QQ', entry['address'], entry['size'])
        blob_entries += pack('>QQ', 0, 0)
        blob_data_start = self.header.size + len(blob_entries)
        (blob_data, blob_strings, data_pos) = self.rootnode.to_dtb('', blob_data_start, self.header.version)
        if self.prenops:
            blob_data = pack('').join([nop.to_dtb('')[0] for nop in self.prenops]) + blob_data
        if self.postnops:
            blob_data += pack('').join([nop.to_dtb('')[0] for nop in self.postnops])
        blob_data += pack('>I', DTB_END)
        self.header.size_dt_strings = len(blob_strings)
        self.header.size_dt_struct = len(blob_data)
        self.header.off_mem_rsvmap = self.header.size
        self.header.off_dt_struct = blob_data_start
        self.header.off_dt_strings = blob_data_start + len(blob_data)
        self.header.total_size = blob_data_start + len(blob_data) + len(blob_strings)
        blob_header = self.header.export()
        return blob_header + blob_entries + blob_data + blob_strings.encode('ascii')


def parse_dts(text):
    """Parse DTS text file and create FDT Object"""
    ver = get_version_info(text)
    text = strip_comments(text)
    dts_lines = split_to_lines(text)
    fdt = FDT()
    if 'version' in ver:
        fdt.header.version = ver['version']
    if 'last_comp_version' in ver:
        fdt.header.last_comp_version = ver['last_comp_version']
    if 'boot_cpuid_phys' in ver:
        fdt.header.boot_cpuid_phys = ver['boot_cpuid_phys']
    # parse entries
    fdt.entries = []
    for line in dts_lines:
        if line.endswith('{'):
            break
        if line.startswith('/memreserve/'):
            line = line.strip(';')
            line = line.split()
            if len(line) != 3 :
                raise Exception()
            fdt.entries.append({'address': int(line[1], 0), 'size': int(line[2], 0)})
    # parse nodes
    curnode = None
    fdt.rootnode = None
    for line in dts_lines:
        if line.endswith('{'):
            # start node
            node_name = line.split()[0]
            new_node = Node(node_name)
            if fdt.rootnode is None:
                fdt.rootnode = new_node
            if curnode is not None:
                curnode.append(new_node)
                new_node.set_parent_node(curnode)
            curnode = new_node
        elif line.endswith('}'):
            # end node
            if curnode is not None:
                curnode = curnode.get_parent_node()
        elif line.endswith('[NOP]'):
            # Nop
            if curnode is not None:
                curnode.append(Nop())
            elif fdt.rootnode is not None:
                fdt.postnops.append(Nop())
            else:
                fdt.prenops.append(Nop())
        else:
            # properties
            if line.find('=') == -1:
                prop_name = line
                prop_obj = Property(prop_name)
            else:
                line = line.split('=', maxsplit=1)
                prop_name = line[0].rstrip(' ')
                prop_value = line[1].lstrip(' ')
                if prop_value.startswith('<'):
                    prop_obj = PropWords(prop_name)
                    prop_value = prop_value.replace('<', '').replace('>', '')
                    for prop in prop_value.split():
                        prop_obj.append(int(prop, 0))
                elif prop_value.startswith('['):
                    prop_obj = PropBytes(prop_name)
                    prop_value = prop_value.replace('[', '').replace(']', '')
                    for prop in prop_value.split():
                        prop_obj.append(int(prop, 16))
                else:
                    prop_obj = PropStrings(prop_name)
                    for prop in prop_value.split('",'):
                        prop = prop.replace('"', "")
                        prop = prop.strip()
                        prop_obj.append(prop)
            if curnode is not None:
                curnode.append(prop_obj)

    return fdt


def parse_dtb(data):
    """ Parse FDT Binary Blob and create FDT Object """
    from struct import unpack_from

    fdt = FDT()
    # parse header
    fdt.header = Header.parse(data)
    # parse entries
    offset = fdt.header.off_mem_rsvmap
    aa = data[offset:]
    while True:
        entrie = dict(zip(('address', 'size'), unpack_from(">QQ", data, offset)))
        offset += 16
        if entrie['address'] == 0 and entrie['size'] == 0:
            break
        fdt.entries.append(entrie)
    # parse nodes
    curnode = None
    offset = fdt.header.off_dt_struct
    while True:
        if len(data) < (offset + 4):
            raise Exception("Error ...")

        tag = unpack_from(">I", data, offset)[0]
        offset += 4
        if tag == DTB_BEGIN_NODE:
            node_name = extract_string(data, offset)
            offset = ((offset + len(node_name) + 4) & ~3)
            if not node_name: node_name = '/'
            new_node = Node(node_name)
            if fdt.rootnode is None:
                fdt.rootnode = new_node
            if curnode is not None:
                curnode.append(new_node)
                new_node.set_parent_node(curnode)
            curnode = new_node
        elif tag == DTB_END_NODE:
            if curnode is not None:
                curnode = curnode.get_parent_node()
        elif tag == DTB_NOP:
            if curnode is not None:
                curnode.append(Nop())
            elif fdt.rootnode is not None:
                fdt.postnops.append(Nop())
            else:
                fdt.prenops.append(Nop())
        elif tag == DTB_PROP:
            prop_size, prop_string_pos, = unpack_from(">II", data, offset)
            prop_start = offset + 8
            if fdt.header.version < 16 and prop_size >= 8:
                prop_start = ((prop_start + 7) & ~0x7)
            prop_name = extract_string(data, fdt.header.off_dt_strings + prop_string_pos)
            prop_raw_value = data[prop_start: prop_start + prop_size]
            offset = prop_start + prop_size
            offset = ((offset + 3) & ~0x3)
            if curnode is not None:
                curnode.append(Property.create(prop_name, prop_raw_value))
        elif tag == DTB_END:
            break
        else:
            raise Exception("Unknown Tag: {}".format(tag))

    return fdt
