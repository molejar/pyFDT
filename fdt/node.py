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
from string import printable

from .head import DTB_BEGIN_NODE, DTB_END_NODE
from .prop import Property
from .misc import line_offset


def split_path(path):
    xpath = path.split('/')
    return xpath[-1], '/'.join(xpath[:-1]) if len(xpath) > 1 else ""


class Node(object):
    """Node representation"""

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("The value must be a string type !")
        if not all(c in printable for c in value):
            raise ValueError("The value must contain only printable chars !")
        self._name = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, node):
        if node is not None and not isinstance(node, Node):
            raise ValueError("Invalid object type")
        self._parent = node

    @property
    def path(self):
        node = self
        path = []
        while node.parent is not None:
            node = node.parent
            if node.name == '/':
                break
            path.append(node.name)
        return '/'.join(path[::-1])

    @property
    def props(self):
        return self._props

    @property
    def nodes(self):
        return self._nodes

    def __init__(self, name=None, props=None, nodes=None):
        """Init node with name"""
        self._name = ""
        self._props = [] if props is None else props
        self._nodes = [] if nodes is None else nodes
        self._parent = None
        if name is not None:
            self.name = name

    def __str__(self):
        """String representation"""
        return "NODE: {} ({} props, {} sub-nodes)".format(self.name, len(self.props), len(self.nodes))

    def __ne__(self, node):
        """Check node inequality"""
        return not self.__eq__(node)

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

    def get_property_index(self, path):
        """Get index value of existing item by name"""
        prop_name, node_path = split_path(path)
        node = self.get_subnode(node_path)
        if node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))
        for index, item in enumerate(node.props):
            if item.name == prop_name:
                return index
        return None

    def get_subnode_index(self, path):
        """Get index value of existing item by name"""
        node_name, node_path = split_path(path)
        node = self.get_subnode(node_path)
        if node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))
        for index, item in enumerate(node.nodes):
            if item.name == node_name:
                return index
        return None

    def get_property(self, path):
        """Get property obj by path/name"""
        prop_name, node_path = split_path(path)
        node = self.get_subnode(node_path)
        if node is not None:
            for item in node.props:
                if item.name == prop_name:
                    return item
        return None

    def get_subnode(self, path):
        """Get subnode obj by path/name"""
        node = self
        if path:
            for sub_name in path.split('/'):
                found = False
                for sub_node in node.nodes:
                    if sub_node.name == sub_name:
                        node = sub_node
                        found = True
                        break
                if not found:
                    return None
        return node

    def remove_property(self, path):
        """Remove property obj by path/name. Raises ValueError if path/name not exist"""
        prop_name, node_path = split_path(path)
        node = self.get_subnode(node_path)
        if node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))
        item = node.get_property(prop_name)
        if item is None:
            raise Exception("{}: \"{}\" property doesn't exists".format(self, prop_name))
        node.props.remove(item)

    def remove_subnode(self, path):
        """Remove subnode obj by path/name. Raises ValueError if path/name not exist"""
        node_name, node_path = split_path(path)
        node = self.get_subnode(node_path)
        if node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))
        item = node.get_subnode(node_name)
        if item is None:
            raise Exception("{}: \"{}\" subnode doesn't exists".format(self, node_name))
        node.nodes.remove(item)

    def append(self, item, path=""):
        """Append sub-node or property at specified path"""
        node = self.get_subnode(path)
        if node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))

        if isinstance(item, Property):
            if node.get_property(item.name) is not None:
                raise Exception("{}: \"{}\" property already exists".format(self, item.name))
            node.props.append(item)

        elif isinstance(item, Node):
            if node.get_subnode(item.name) is not None:
                raise Exception("{}: \"{}\" node already exists".format(self, item.name))
            if item is self:
                raise Exception("{}: append the same node {}".format(self, item.name))
            item.parent = node
            node.nodes.append(item)

        else:
            raise TypeError("Invalid object type")

    def merge(self, node, replace=True):
        """ Merge two nodes and subnodes.
            Replace current properties with the given properties if replace is True.
        """
        if not isinstance(node, Node):
            raise TypeError("Invalid object type")

        for prop in node.props:
            index = self.get_property_index(prop.name)
            if index is None:
                self._props.append(deepcopy(prop))
            elif prop in self._props:
                continue
            elif replace:
                self._props[index] = copy(prop)
            else:
                pass

        for sub_node in node.nodes:
            index = self.get_subnode_index(sub_node.name)
            if index is None:
                dup_node = deepcopy(sub_node)
                dup_node.parent = self
                self._nodes.append(dup_node)
            elif sub_node in self._nodes:
                continue
            else:
                self._nodes[index].merge(sub_node, replace)

    def walk(self, path=""):
        """ Walk into subnodes and yield paths and objects
            Returns set with (path string, node object)
        """
        root_node = self.get_subnode(path)
        if root_node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))

        node = root_node
        index = 0
        xpath = []

        while True:
            yield ('/'.join(xpath), node)
            if node.nodes:
                xpath.append(node.name)
                node = node.nodes[index]
                index += 1
            else:
                pass

    def to_dts(self, tabsize=4, depth=0):
        """Get NODE in string representation"""
        dts  = line_offset(tabsize, depth, self.name + ' {\n')
        dts += ''.join([prop.to_dts(tabsize, depth + 1) for prop in self._props])
        dts += ''.join([node.to_dts(tabsize, depth + 1) for node in self._nodes])
        dts += line_offset(tabsize, depth, "};\n")
        return dts

    def to_dtb(self, strings, pos=0, version=17):
        """Get NODE in binary blob representation"""
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
