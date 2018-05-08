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

from struct import unpack, pack
from string import printable

from .head import Header, DTB_PROP, DTB_BEGIN_NODE, DTB_END_NODE
from .misc import is_string, line_offset


########################################################################################################################
# Helper methods
########################################################################################################################

def new_property(name, raw_value):
    """ Instantiate property with raw value type """
    if is_string(raw_value):
        obj = PropStrings(name)
        # Extract strings from raw value
        for st in raw_value.decode('ascii').split('\0'):
            if st:
                obj.append(st)
        return obj

    elif len(raw_value) and len(raw_value) % 4 == 0:
        obj = PropWords(name)
        # Extract words from raw value
        for i in range(0, len(raw_value), 4):
            obj.append(unpack(">I", raw_value[i:i + 4])[0])
        return obj

    elif len(raw_value) and len(raw_value):
        return PropBytes(name, data=raw_value)

    else:
        return Property(name)


########################################################################################################################
# Base Class
########################################################################################################################

class BaseItem(object):

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        return self._parent

    @property
    def path(self):
        path = []
        node = self.parent
        while node is not None:
            if node.name == '/': break
            path.append(node.name)
            node = node.parent
        return '/' + '/'.join(path[::-1])

    def __init__(self, name, **kwargs):
        """ Init BaseItem
        :param name: Item name
        :param parent: Item parent
        :return Item object
        """
        assert isinstance(name, str), "The value must be a string type !"
        assert all(c in printable for c in name), "The value must contain just printable chars !"
        assert 'parent' not in kwargs or isinstance(kwargs['parent'], Node), "Invalid object type"
        self._name = name
        self._parent = kwargs['parent'] if 'parent' in kwargs else None

    def __str__(self):
        """String representation"""
        return "{}".format(self.name)

    def __ne__(self, node):
        """Check node inequality"""
        return not self.__eq__(node)

    def set_name(self, value):
        assert isinstance(value, str), "The value must be a string type !"
        assert all(c in printable for c in value), "The value must contain just printable chars !"
        self._name = value

    def set_parent(self, value):
        assert isinstance(value, Node), "Invalid object type"
        self._parent = value

    def to_dts(self, tabsize=4, depth=0):
        raise NotImplementedError()

    def to_dtb(self, strings, pos=0, version=Header.MAX_VERSION):
        raise NotImplementedError()


########################################################################################################################
# Property Classes
########################################################################################################################

class Property(BaseItem):

    def __init__(self, name, **kwargs):
        """ Property init.
        :param name: Property name
        :param parent: Property parent
        :return Property object
        """
        super().__init__(name, **kwargs)

    def __str__(self):
        """String representation"""
        return "{}".format(self.name)

    def __getitem__(self, value):
        """Returns No Items"""
        return None

    def __eq__(self, prop):
        """Check properties are the same (same names) """
        if not isinstance(prop, Property):
            return False
        if self.name != prop.name:
            return False
        return True

    def copy(self):
        return Property(self.name)

    def to_dts(self, tabsize=4, depth=0):
        """Get dts string representation"""
        return line_offset(tabsize, depth, '{};\n'.format(self.name))

    def to_dtb(self, strings, pos=0, version=Header.MAX_VERSION):
        """Get blob representation"""
        strpos = strings.find(self.name + '\0')
        if strpos < 0:
            strpos = len(strings)
            strings += self.name + '\0'
        pos += 12
        return pack('>III', DTB_PROP, 0, strpos), strings, pos


class PropStrings(Property):
    """Property with strings as value"""

    def __init__(self, name, *args, **kwargs):
        """ Init property strings
        :param name: Property name
        :param args: str1, str2, ...
        :param parent: Property parent
        :return Property object
        """
        super().__init__(name, **kwargs)
        self.data = []
        for arg in args:
            self.append(arg)

    def __str__(self):
        """String representation"""
        return "{} = {}".format(self.name, self.data)

    def __len__(self):
        """Get strings count"""
        return len(self.data)

    def __getitem__(self, index):
        """Get strings, returns a string"""
        return self.data[index]

    def __eq__(self, prop):
        """Check properties are the same (same values)"""
        if not isinstance(prop, PropStrings):
            return False
        if self.name != prop.name:
            return False
        if len(self) != len(prop):
            return False
        for index in range(len(self)):
            if self.data[index] != prop[index]:
                return False
        return True

    def copy(self):
        return PropStrings(self.name, *self.data)

    def append(self, value):
        assert isinstance(value, str), "Invalid object type"
        assert len(value) > 0, "Invalid strings value"
        assert all(c in printable or c in ('\r', '\n') for c in value), "Invalid chars in strings value"
        self.data.append(value)

    def pop(self, index):
        assert 0 <= index < len(self.data), "Index out of range"
        return self.data.pop(index)

    def clear(self):
        self.data.clear()

    def to_dts(self, tabsize=4, depth=0):
        """Get DTS representation"""
        result  = line_offset(tabsize, depth, self.name)
        result += ' = "'
        result += '", "'.join(self.data)
        result += '";\n'
        return result

    def to_dtb(self, strings, pos=0, version=Header.MAX_VERSION):
        """Get DTB representation"""
        blob = pack('')
        for chars in self.data:
            blob += chars.encode('ascii') + pack('b', 0)
        blob_len = len(blob)
        if version < 16 and (pos + 12) % 8 != 0:
            blob = pack('b', 0) * (8 - ((pos + 12) % 8)) + blob
        if blob_len % 4:
            blob += pack('b', 0) * (4 - (blob_len % 4))
        strpos = strings.find(self.name + '\0')
        if strpos < 0:
            strpos = len(strings)
            strings += self.name + '\0'
        blob = pack('>III', DTB_PROP, blob_len, strpos) + blob
        pos += len(blob)
        return blob, strings, pos


class PropWords(Property):
    """Property with words as value"""

    def __init__(self, name, *args, **kwargs):
        """Init property words
        :param name: Property name
        :param args: word1, word2, ...
        :param kwargs - optional arguments
               data:
               wsize:
        """
        super().__init__(name, **kwargs)
        self.data = []
        self.word_size = kwargs['wsize'] if 'wsize' in kwargs else 32
        for val in args:
            self.append(val)
        if 'data' in kwargs:
            assert isinstance(kwargs['data'], list), "\"data\" argument must be a list type !"
            for val in kwargs['data']:
                self.append(val)

    def __str__(self):
        """String representation"""
        return "{} = {}".format(self.name, self.data)

    def __getitem__(self, index):
        """Get words, returns a word integer"""
        return self.data[index]

    def __len__(self):
        """Get words count"""
        return len(self.data)

    def __eq__(self, prop):
        """Check properties are the same (same values)"""
        if not isinstance(prop, PropWords):
            return False
        if self.name != prop.name:
            return False
        if len(self) != len(prop):
            return False
        for index in range(len(self)):
            if self.data[index] != prop[index]:
                return False
        return True

    def copy(self):
        return PropWords(self.name, *self.data, wsize=self.word_size)

    def append(self, value):
        assert isinstance(value, int), "Invalid object type"
        assert 0 <= value < 2**self.word_size, "Invalid word value {}, use <0x0 - 0x{:X}>".format(
            value, 2**self.word_size - 1)
        self.data.append(value)

    def pop(self, index):
        assert 0 <= index < len(self.data), "Index out of range"
        return self.data.pop(index)

    def clear(self):
        self.data.clear()

    def to_dts(self, tabsize=4, depth=0):
        """Get DTS representation"""
        result  = line_offset(tabsize, depth, self.name)
        result += ' = <'
        result += ' '.join(["0x{:X}".format(word) for word in self.data])
        result += ">;\n"
        return result

    def to_dtb(self, strings, pos=0, version=Header.MAX_VERSION):
        """Get DTB representation"""
        strpos = strings.find(self.name + '\0')
        if strpos < 0:
            strpos = len(strings)
            strings += self.name + '\0'
        blob  = pack('>III', DTB_PROP, len(self.data) * 4, strpos)
        for word in self.data:
            blob += pack('>I', word)
        pos  += len(blob)
        return blob, strings, pos


class PropBytes(Property):
    """Property with bytes as value"""

    def __init__(self, name, data=None):
        """ Init property bytes
        :param name: Property name
        :param data: Data as list, bytes or bytearray
        :param parent: Property parent
        :return Property object
        """
        super().__init__(name)
        self.data = bytearray() if data is None else bytearray(data)

    def __str__(self):
        """String representation"""
        return "{} = {}".format(self.name, self.data)

    def __getitem__(self, index):
        """Get words, returns a word integer"""
        return self.data[index]

    def __len__(self):
        """Get words count"""
        return len(self.data)

    def __eq__(self, prop):
        """ Check properties are the same (same values) """
        if not isinstance(prop, PropBytes):
            return False
        if self.name != prop.name:
            return False
        if len(self) != len(prop):
            return False
        for index in range(len(self)):
            if self.data[index] != prop[index]:
                return False
        return True

    def copy(self):
        """ Create a copy of object """
        return PropBytes(self.name, self.data)

    def append(self, value):
        assert isinstance(value, int), "Invalid object type"
        assert 0 <= value <= 0xFF, "Invalid byte value {}, use <0 - 255>".format(value)
        self.data.append(value)

    def pop(self, index):
        assert 0 <= index < len(self.data), "Index out of range"
        return self.data.pop(index)

    def clear(self):
        self.data = bytearray()

    def to_dts(self, tabsize=4, depth=0):
        """ Get DTS representation """
        result  = line_offset(tabsize, depth, self.name)
        result += ' = ['
        result += ' '.join(["{:02X}".format(byte) for byte in self.data])
        result += '];\n'
        return result

    def to_dtb(self, strings, pos=0, version=Header.MAX_VERSION):
        """ Get DTB representation
        :param strings:
        :param pos:
        :param version:
        :return
        """
        strpos = strings.find(self.name + '\0')
        if strpos < 0:
            strpos = len(strings)
            strings += self.name + '\0'
        blob  = pack('>III', DTB_PROP, len(self.data), strpos)
        blob += bytes(self.data)
        if len(blob) % 4:
            blob += bytes([0] * (4 - (len(blob) % 4)))
        pos += len(blob)
        return blob, strings, pos


class PropIncBin(PropBytes):
    """Property with bytes as value"""

    def __init__(self, name, data=None, file_name=None, rpath=None):
        """ Init property bytes
        :param name: Property name
        :param data: Data as list, bytes or bytearray
        :param parent: Property parent
        :return Property object
        """
        super().__init__(name, data)
        self.file_name = file_name
        self.relative_path = rpath

    def __eq__(self, prop):
        """ Check properties are the same (same values) """
        if not isinstance(prop, PropIncBin):
            return False
        if self.name != prop.name:
            return False
        if self.file_name != prop.file_name:
            return False
        if self.relative_path != prop.relative_path:
            return False
        if self.data != prop.data:
            return False
        return True

    def copy(self):
        """ Create a copy of object """
        return PropIncBin(self.name, self.data, self.file_name, self.relative_path)

    def to_dts(self, tabsize=4, depth=0):
        """ Get DTS representation """
        file_path = self.file_name
        if self.relative_path is not None:
            file_path = "{}/{}".format(self.relative_path, self.file_name)
        result  = line_offset(tabsize, depth, self.name)
        result += " = /incbin/(\"{}\");\n".format(file_path)
        return result


########################################################################################################################
# Node Class
########################################################################################################################

class Node(BaseItem):
    """Node representation"""

    @property
    def props(self):
        return self._props

    @property
    def nodes(self):
        return self._nodes

    @property
    def empty(self):
        return False if self.nodes or self.props else True

    def __init__(self, name, **kwargs):
        """ Create Node item
        :param name: Node name
        :param props: List of properties
        :param nodes: List of sub-nodes
        """
        assert 'props' not in kwargs or isinstance(kwargs['props'], list), "Invalid object type"
        assert 'nodes' not in kwargs or isinstance(kwargs['nodes'], list), "Invalid object type"
        super().__init__(name, **kwargs)
        self._props = kwargs['props'] if 'props' in kwargs else []
        self._nodes = kwargs['nodes'] if 'nodes' in kwargs else []

    def __str__(self):
        """String representation"""
        return "< {}: {} props, {} nodes >".format(self.name, len(self.props), len(self.nodes))

    def __eq__(self, node):
        """Check node equality"""
        if not isinstance(node, Node):
            raise ValueError("Invalid object type")
        if self.name != node.name:
            return False
        if len(self.props) != len(node.props) or \
           len(self.nodes) != len(node.nodes):
            return False
        for p in self.props:
            if p not in node.props:
                return False
        for n in self.nodes:
            if n not in node.nodes:
                return False
        return True

    def copy(self):
        """ Create a copy of Node object """
        node = Node(self.name)

        for p in self.props:
            node.append(p.copy())
        for n in self.nodes:
            node.append(n.copy())

        return node

    def get_property(self, name):
        """ Get property obj by name
        :param name: Property name
        :return property object
        """
        for p in self.props:
            if p.name == name:
                return p
        return None

    def get_subnode(self, name):
        """ Get sub-node obj by name
        :param name: Sub-node name
        :return node object
        """
        for n in self.nodes:
            if n.name == name:
                return n
        return None

    def exist_property(self, name):
        """ Check if property exist
        :param name: Property name
        :return True if property exist else False
        """
        return False if self.get_property(name) is None else True

    def exist_subnode(self, name):
        """ Check if sub-node exist
        :param name: Sub-node name
        :return True if sub-node exist else False
        """
        return False if self.get_subnode(name) is None else True

    def remove_property(self, name):
        """ Remove property obj by its name.
        :param name: Property name
        """
        item = self.get_property(name)
        if item is not None:
            self.props.remove(item)

    def remove_subnode(self, name):
        """ Remove sub-node obj by its name.
        :param name: Sub-node name
        """
        item = self.get_subnode(name)
        if item is not None:
            self.nodes.remove(item)

    def append(self, item):
        """ Append sub-node or property
        :param item: The node or property object
        """
        assert isinstance(item, (Node, Property)), "Invalid object type, use \"Node\" or \"Property\""

        if isinstance(item, Property):
            if self.get_property(item.name) is not None:
                raise Exception("{}: \"{}\" property already exists".format(self, item.name))
            item.set_parent(self)
            self.props.append(item)

        else:
            if self.get_subnode(item.name) is not None:
                raise Exception("{}: \"{}\" node already exists".format(self, item.name))
            if item is self:
                raise Exception("{}: append the same node {}".format(self, item.name))
            item.set_parent(self)
            self.nodes.append(item)

    def merge(self, node_obj, replace=True):
        """ Merge two nodes and sub-nodes.
        :param node_obj: Node object
        :param replace: If True, replace current properties with the given properties
        """
        assert isinstance(node_obj, Node), "Invalid object type"

        def get_property_index(name):
            for i, p in enumerate(self.props):
                if p.name == name:
                    return i
            return None

        def get_subnode_index(name):
            for i, n in enumerate(self.nodes):
                if n.name == name:
                    return i
            return None

        for prop in node_obj.props:
            index = get_property_index(prop.name)
            if index is None:
                self.append(prop.copy())
            elif prop in self._props:
                continue
            elif replace:
                new_prop = prop.copy()
                new_prop.set_parent(self)
                self._props[index] = new_prop
            else:
                pass

        for sub_node in node_obj.nodes:
            index = get_subnode_index(sub_node.name)
            if index is None:
                self.append(sub_node.copy())
            elif sub_node in self._nodes:
                continue
            else:
                self._nodes[index].merge(sub_node, replace)

    def to_dts(self, tabsize=4, depth=0):
        """ Get NODE in string representation
        :param tabsize:
        :param depth:
        :return string
        """
        dts  = line_offset(tabsize, depth, self.name + ' {\n')
        dts += ''.join([prop.to_dts(tabsize, depth + 1) for prop in self._props])
        dts += ''.join([node.to_dts(tabsize, depth + 1) for node in self._nodes])
        dts += line_offset(tabsize, depth, "};\n")
        return dts

    def to_dtb(self, strings, pos=0, version=Header.MAX_VERSION):
        """ Get NODE in binary blob representation
        :param strings:
        :param pos:
        :param version:
        :return
        """
        if self.name == '/':
            blob = pack('>II', DTB_BEGIN_NODE, 0)
        else:
            blob = pack('>I', DTB_BEGIN_NODE)
            blob += self.name.encode('ascii') + b'\0'
        if len(blob) % 4:
            blob += pack('b', 0) * (4 - (len(blob) % 4))
        pos += len(blob)
        for prop in self._props:
            (data, strings, pos) = prop.to_dtb(strings, pos, version)
            blob += data
        for node in self._nodes:
            (data, strings, pos) = node.to_dtb(strings, pos, version)
            blob += data
        pos += 4
        blob += pack('>I', DTB_END_NODE)
        return blob, strings, pos
