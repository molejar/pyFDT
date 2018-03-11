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

from .node import Node
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
    'Node',
    'Header',
    'PropBytes',
    'PropWords',
    'PropStrings',
    # core methods
    'parse_dts',
    'parse_dtb',
    'diff'
]


class FDT(object):
    """ Flattened Device Tree Class """

    @property
    def empty(self):
        return True if not self.entries and (self.rootnode is None or self.rootnode.empty) else False

    def __init__(self):
        self.header = Header()
        self.entries = []
        self.rootnode = None

    def info(self):
        for path, props in self.rootnode.walk():
            print("{} - {} props".format(path, len(props)))

    def get_node(self, name, path=""):
        assert self.rootnode is not None, "Root node not defined"
        if name == '/' and path == "":
            return self.rootnode
        else:
            return self.rootnode.get_subnode(name, path)

    def get_property(self, name, path=""):
        assert self.rootnode is not None, "Root node not defined"
        return self.rootnode.get_property(name, path)

    def walk(self):
        return self.rootnode.walk()

    def merge(self, fdt):
        assert isinstance(fdt, FDT), "Invalid object type"
        if self.header.version is None:
            self.header = fdt.header
        else:
            if fdt.header.version is not None and \
               fdt.header.version > self.header.version:
                self.header.version = fdt.header.version
        if fdt.entries:
            for in_entry in fdt.entries:
                exist = False
                for index in range(len(self.entries)):
                    if self.entries[index]['address'] == in_entry['address']:
                        self.entries[index]['address'] = in_entry['size']
                        exist = True
                        break
                if not exist:
                    self.entries.append(in_entry)
        self.rootnode.merge(fdt.rootnode)

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
        if self.rootnode is not None:
            result += self.rootnode.to_dts(tabsize)
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
        blob_data += pack('>I', DTB_END)
        self.header.size_dt_strings = len(blob_strings)
        self.header.size_dt_struct = len(blob_data)
        self.header.off_mem_rsvmap = self.header.size
        self.header.off_dt_struct = blob_data_start
        self.header.off_dt_strings = blob_data_start + len(blob_data)
        self.header.total_size = blob_data_start + len(blob_data) + len(blob_strings)
        blob_header = self.header.export()
        return blob_header + blob_entries + blob_data + blob_strings.encode('ascii')


def parse_dts(text, root_dir=''):
    """Parse DTS text file and create FDT Object"""
    ver = get_version_info(text)
    text = strip_comments(text)
    dts_lines = split_to_lines(text)
    fdt_obj = FDT()
    if 'version' in ver:
        fdt_obj.header.version = ver['version']
    if 'last_comp_version' in ver:
        fdt_obj.header.last_comp_version = ver['last_comp_version']
    if 'boot_cpuid_phys' in ver:
        fdt_obj.header.boot_cpuid_phys = ver['boot_cpuid_phys']
    # parse entries
    fdt_obj.entries = []
    for line in dts_lines:
        if line.endswith('{'):
            break
        if line.startswith('/memreserve/'):
            line = line.strip(';')
            line = line.split()
            if len(line) != 3 :
                raise Exception()
            fdt_obj.entries.append({'address': int(line[1], 0), 'size': int(line[2], 0)})
    # parse nodes
    curnode = None
    fdt_obj.rootnode = None
    for line in dts_lines:
        if line.endswith('{'):
            # start node
            node_name = line.split()[0]
            new_node = Node(node_name)
            if fdt_obj.rootnode is None:
                fdt_obj.rootnode = new_node
            if curnode is not None:
                curnode.append(new_node)
                new_node.parent = curnode
            curnode = new_node
        elif line.endswith('}'):
            # end node
            if curnode is not None:
                curnode = curnode.parent
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
                elif prop_value.startswith('/incbin/'):
                    prop_value = prop_value.replace('/incbin/("', '').replace('")', '')
                    prop_value = prop_value.split(',')
                    file_path  = os.path.join(root_dir, prop_value[0].strip())
                    file_offset = int(prop_value.strip(), 0) if len(prop_value) > 1 else 0
                    file_size = int(prop_value.strip(), 0) if len(prop_value) > 2 else 0
                    if file_path is None or not os.path.exists(file_path):
                        raise Exception("File path doesn't exist: {}".format(file_path))
                    with open(file_path, "rb") as f:
                        f.seek(file_offset)
                        data = f.read(file_size) if file_size > 0 else f.read()
                    prop_obj = PropBytes(prop_name, data)
                elif prop_value.startswith('/plugin/'):
                    raise NotImplementedError("Not implemented property value: /plugin/")
                elif prop_value.startswith('/bits/'):
                    raise NotImplementedError("Not implemented property value: /bits/")
                else:
                    prop_obj = PropStrings(prop_name)
                    for prop in prop_value.split('",'):
                        prop = prop.replace('"', "")
                        prop = prop.strip()
                        prop_obj.append(prop)
            if curnode is not None:
                curnode.append(prop_obj)

    return fdt_obj


def parse_dtb(data):
    """ Parse FDT Binary Blob and create FDT Object
    :param data: FDT Binary Blob as bytes or bytearray
    :return FDT object
    """
    assert isinstance(data, (bytes, bytearray)), "Invalid argument type"

    from struct import unpack_from

    fdt_obj = FDT()
    # parse header
    fdt_obj.header = Header.parse(data)
    # parse entries
    offset = fdt_obj.header.off_mem_rsvmap
    aa = data[offset:]
    while True:
        entrie = dict(zip(('address', 'size'), unpack_from(">QQ", data, offset)))
        offset += 16
        if entrie['address'] == 0 and entrie['size'] == 0:
            break
        fdt_obj.entries.append(entrie)
    # parse nodes
    curnode = None
    offset = fdt_obj.header.off_dt_struct
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
            if fdt_obj.rootnode is None:
                fdt_obj.rootnode = new_node
            if curnode is not None:
                curnode.append(new_node)
                new_node.parent = curnode
            curnode = new_node
        elif tag == DTB_END_NODE:
            if curnode is not None:
                curnode = curnode.parent
        elif tag == DTB_PROP:
            prop_size, prop_string_pos, = unpack_from(">II", data, offset)
            prop_start = offset + 8
            if fdt_obj.header.version < 16 and prop_size >= 8:
                prop_start = ((prop_start + 7) & ~0x7)
            prop_name = extract_string(data, fdt_obj.header.off_dt_strings + prop_string_pos)
            prop_raw_value = data[prop_start: prop_start + prop_size]
            offset = prop_start + prop_size
            offset = ((offset + 3) & ~0x3)
            if curnode is not None:
                curnode.append(Property.create(prop_name, prop_raw_value))
        elif tag == DTB_END:
            break
        else:
            raise Exception("Unknown Tag: {}".format(tag))

    return fdt_obj


def diff(fdt1, fdt2):
    """ Diff two flattened device tree objects
    :param fdt1: The object 1 of FDT
    :param fdt2: The object 2 of FDT
    :return: list of 3 objects (same in 1 and 2, specific for 1, specific for 2)
    """
    assert isinstance(fdt1, FDT), "Invalid argument type"
    assert isinstance(fdt2, FDT), "Invalid argument type"

    fdt_same = FDT()
    fdt_same.header = fdt1.header if fdt1.header.version > fdt2.header.version else fdt2.header
    fdt_a = FDT()
    fdt_a.header = fdt1.header
    fdt_b = FDT()
    fdt_b.header = fdt2.header

    if fdt1.entries and fdt2.entries:
        for entry_a in fdt1.entries:
            for entry_b in fdt2.entries:
                if entry_a['address'] == entry_b['address'] and entry_a['size'] == entry_b['size']:
                    fdt_same.entries.append(entry_a)
                    break

    for entry_a in fdt1.entries:
        found = False
        for entry_s in fdt_same.entries:
            if entry_a['address'] == entry_s['address'] and entry_a['size'] == entry_s['size']:
                found = True
                break
        if not found:
            fdt_a.entries.append(entry_a)

    for entry_b in fdt2.entries:
        found = False
        for entry_s in fdt_same.entries:
            if entry_b['address'] == entry_s['address'] and entry_b['size'] == entry_s['size']:
                found = True
                break
        if not found:
            fdt_b.entries.append(entry_b)

    fdt_same.rootnode, fdt_a.rootnode, fdt_b.rootnode = Node.diff(fdt1.rootnode, fdt2.rootnode)

    return fdt_same, fdt_a, fdt_b
