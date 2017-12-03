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

from copy import deepcopy, copy
from struct import pack

from .prop import Property
from .misc import *


class Nop(object):
    """Nop child representation"""

    @property
    def name(self):
        return ""

    def __init__(self):
        """Init with nothing"""
        pass

    def __str__(self):
        """String representation"""
        return ''

    def to_dts(self, tabsize=4, depth=0):
        """Get dts string representation"""
        return line_offset(tabsize, depth, '// [NOP]')

    def to_dtb(self, string_store, pos=0, version=17):
        """Get blob representation"""
        pos += 4
        return pack('>I', DTB_NOP), string_store, pos


class Node(object):
    """Node representation"""

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise Exception("The value must be a string type !")
        if not all(c in printable for c in value):
            raise Exception("The value must contain only printable chars !")
        self._name = value

    def __init__(self, name):
        """Init node with name"""
        self.name = name
        self.parent = None
        self.subdata = []

    def __str__(self):
        """String representation"""
        return "Node: {}".format(self.name)

    def __getitem__(self, index):
        """Get subnodes, returns either a Node, a Property or a Nop"""
        return self.subdata[index]

    def __setitem__(self, index, subnode):
        """Set node at index, replacing previous subnode,
           must not be a duplicate name
        """
        if self.subdata[index].name != subnode.name and self.__find_name(subnode.name) is not None:
            raise Exception("{} : {} subnode already exists".format(self, subnode))
        if not isinstance(subnode, (Nop, Node, Property)):
            raise Exception("Invalid object type")
        self.subdata[index] = subnode

    def __len__(self):
        """Get strings count"""
        return len(self.subdata)

    def __ne__(self, node):
        """Check node inequality
           i.e. is subnodes are the same, in either order
           and properties are the same (same values)
           The FdtNop is excluded from the check
        """
        return not self.__eq__(node)

    def __eq__(self, node):
        """Check node equality
           i.e. is subnodes are the same, in either order
           and properties are the same (same values)
           The FdtNop is excluded from the check
        """
        if not isinstance(node, Node):
            raise Exception("Invalid object type")
        if self.name != node.name:
            return False
        curnames = set([subnode.name for subnode in self.subdata if not isinstance(subnode, Nop)])
        cmpnames = set([subnode.name for subnode in node if not isinstance(subnode, Nop)])
        if curnames != cmpnames:
            return False
        for subnode in [subnode for subnode in self.subdata if not isinstance(subnode, Nop)]:
            index = node.index(subnode.name)
            if subnode != node[index]:
                return False
        return True

    def __find_name(self, name):
        """Find name in subnodes"""
        index = 0
        for data in self.subdata:
            if not isinstance(data, Nop) and data.name == name:
                return index
            index += 1
        return None

    def set_parent_node(self, node):
        """Set parent node, None and FdtNode accepted"""
        if node is not None and not isinstance(node, Node):
            raise Exception("Invalid object type")
        self.parent = node

    def get_parent_node(self):
        """Get parent node"""
        return self.parent

    def append(self, subnode):
        """Append subnode, same as add_subnode"""
        if self.__find_name(subnode.name) is not None:
            raise Exception("{} : {} subnode already exists".format(self, subnode))
        if not isinstance(subnode, (Nop, Node, Property)):
            raise Exception("Invalid object type")
        self.subdata.append(subnode)

    def pop(self, index=-1):
        """Remove and returns subnode at index, default the last"""
        return self.subdata.pop(index)

    def insert(self, index, subnode):
        """Insert subnode before index, must not be a duplicate name"""
        if self.__find_name(subnode.name) is not None:
            raise Exception("{} : {} subnode already exists".format(self, subnode))
        if not isinstance(subnode, (Nop, Node, Property)):
            raise Exception("Invalid object type")
        self.subdata.insert(index, subnode)

    def remove(self, name):
        """Remove subnode with the name
           Raises ValueError if not present
        """
        index = self.__find_name(name)
        if index is None:
            raise ValueError("Not present")
        return self.subdata.pop(index)

    def index(self, name):
        """Returns position of subnode with the name
           Raises ValueError if not present
        """
        index = self.__find_name(name)
        if index is None:
            raise ValueError("Not present")
        return index

    def merge(self, node):
        """Merge two nodes and subnodes
           Replace current properties with the given properties
        """
        if not isinstance(node, Node):
            raise Exception("Can only merge with a Node Object !")

        for subnode in [obj for obj in node if isinstance(obj, (Node, Property))]:
            index = self.__find_name(subnode.name)
            if index is None:
                dup = deepcopy(subnode)
                if isinstance(subnode, Node):
                    dup.set_parent_node(self)
                self.append(dup)
            elif isinstance(subnode, Node):
                self.subdata[index].merge(subnode)
            else:
                self.subdata[index] = copy(subnode)

    def walk(self):
        """Walk into subnodes and yield paths and objects
           Returns set with (path string, node object)
        """
        node = self
        hist = []
        index = -1
        start = 0
        curpath = []

        while True:
            for index in range(start, len(node)):
                if isinstance(node[index], (Node, Property)):
                    yield ('/' + '/'.join(curpath + [node[index].name]), node[index])
                if isinstance(node[index], Node):
                    if len(node[index]):
                        hist.append((node, index+1))
                        curpath.append(node[index].name)
                        node = node[index]
                        start = 0
                        index = -1
                        break
            if index >= 0:
                if len(hist):
                    (node, start) = hist.pop()
                    curpath.pop()
                else:
                    break

    def to_dts(self, tabsize=4, depth=0):
        """Get NODE in string representation"""
        content = ('\n').join([sub.to_dts(tabsize, depth + 1) for sub in self.subdata])
        content += '\n' if content else ''
        dts = "\n"
        dts += line_offset(tabsize, depth, self.name + ' {\n')
        dts += content
        dts += line_offset(tabsize, depth, "};")
        return dts

    def to_dtb(self, strings, pos=0, version=17):
        """Get NODE in binary blob representation"""
        #strings = blob_str
        if self.name == '/':
            blob = pack('>II', DTB_BEGIN_NODE, 0)
        else:
            blob = pack('>I', DTB_BEGIN_NODE)
            blob += self.name.encode('ascii') + b'\0'
        if len(blob) % 4:
            blob += pack('b', 0) * (4 - (len(blob) % 4))
        pos += len(blob)
        for sub in self.subdata:
            (data, strings, pos) = sub.to_dtb(strings, pos, version)
            blob += data
        pos += 4
        blob += pack('>I', DTB_END_NODE)
        return (blob, strings, pos)
