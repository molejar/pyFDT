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
        assert isinstance(value, str), "The value must be a string type !"
        assert all(c in printable for c in value), "The value must contain only printable chars !"
        self._name = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, node):
        assert node is None or isinstance(node, Node), "Invalid object type"
        self._parent = node

    @property
    def path(self):
        node = self
        root = ''
        path = []
        while node.parent is not None:
            node = node.parent
            if node.name == '/':
                root = '/'
                break
            path.append(node.name)
        return root + '/'.join(path[::-1]) if path else ''

    @property
    def props(self):
        return self._props

    @property
    def nodes(self):
        return self._nodes

    @property
    def empty(self):
        return False if self.nodes or self.props else True

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
        return "< {}: {} props, {} nodes >".format(self.name, len(self.props), len(self.nodes))

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

    def get_property_index(self, name, path=""):
        """ Get index value of existing item by name
        :param name: The property name
        :param path: The path to sub-node
        :return property index
        """
        node = self.get_subnode(path)
        if node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))
        for index, item in enumerate(node.props):
            if item.name == name:
                return index
        return None

    def get_subnode_index(self, path):
        """ Get index value of existing item by name
        :param path: The path to sub-node
        :return node index
        """
        node_name, node_path = split_path(path)
        node = self.get_subnode(node_path)
        if node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))
        for index, item in enumerate(node.nodes):
            if item.name == node_name:
                return index
        return None

    def get_property(self, name, path=""):
        """ Get property obj by path/name
        :param name: The property name
        :param path: The path to sub-node
        :return property object
        """
        node = self.get_subnode(path)
        if node is not None:
            for item in node.props:
                if item.name == name:
                    return item
        return None

    def get_subnode(self, path):
        """ Get subnode obj by path/name
        :param path: The path to sub-node
        :return node object
        """
        node = self
        path = path.lstrip('/')
        if path:
            names = path.split('/')
            found = 0

            for name in names:
                for subnode in node.nodes:
                    if subnode.name == name:
                        found += 1
                        node = subnode
                        break

            if len(names) != found:
                return None

        return node

    def find_property(self, name):
        """ Find property in actual node and all subnodes
        :param name: The property name
        :return: 
        """
        raise NotImplementedError()

    def find_subnode(self, name):
        """ Find node in all subnodes
        :param name: The node name
        :return:
        """
        raise NotImplementedError()

    def remove_property(self, name, path=""):
        """ Remove property obj by path/name. Raises ValueError if path/name not exist
        :param name: The property name
        :param path: The path to sub-node
        """
        node = self.get_subnode(path)
        if node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))
        item = node.get_property(name)
        if item is not None:
            node.props.remove(item)

    def remove_subnode(self, path):
        """ Remove subnode obj by path/name. Raises ValueError if path/name not exist
        :param path: The path to sub-node
        """
        node_name, node_path = split_path(path)
        node = self.get_subnode(node_path)
        if node is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))
        item = node.get_subnode(node_name)
        if item is not None:
            node.nodes.remove(item)

    def append(self, item, path=""):
        """ Append sub-node or property at specified path
        :param item: The node or property object
        :param path: The path to sub-node
        """
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

    def create(self, path):
        """ Create sub-nodes via specified path
        :param path: Relative path
        """
        assert isinstance(path, str), "The path must be a string type !"

        node = self
        path = path.lstrip('/')
        abspath = ''
        for name in path.split('/'):
            abspath += '/' + name
            subnode = self.get_subnode(abspath)
            if subnode is None:
                subnode = Node(name)
                node.append(subnode)
            node = subnode

    def walk(self, path="", relative=False):
        """ Walk trough sub-nodes and return relative/absolute path wih list of properties
        :param path: The path to sub-node
        :param relative: True for relative or False for absolute return path
        :return: [0 - relative/absolute path, 1 - list of properties]
        """
        assert isinstance(path, str), "The path must be a string type !"

        nodes = []
        subnode = self.get_subnode(path)
        if subnode is None:
            raise Exception("{}: Path \"{}\" doesn't exists".format(self, path))
        while True:
            nodes += subnode.nodes
            if subnode.props:
                props_path = "{}/{}".format(subnode.path, subnode.name).replace('//', '/')
                if path and relative:
                    props_path = props_path.replace(path, '').lstrip('/')
                yield (props_path, subnode.props)
            if not nodes:
                break
            subnode = nodes.pop()

    def merge(self, node, replace=True):
        """ Merge two nodes and subnodes.
            Replace current properties with the given properties if replace is True.
        """
        assert isinstance(node, Node), "Invalid object type"

        for prop in node.props:
            index = self.get_property_index(prop.name)
            if index is None:
                self._props.append(deepcopy(prop))
            elif prop in self._props:
                continue
            elif replace:
                self._props[index] = copy(prop)
            else:
                raise Exception("")

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

    @staticmethod
    def diff(node_a, node_b):
        """ Diff two nodes
        :param node_a: The object of node A
        :param node_b: The object of node B
        :return: list of 3 objects (same in A and B, specific for A, specific for B)
        """
        assert isinstance(node_a, Node), "Invalid object type"
        assert isinstance(node_b, Node), "Invalid object type"
        # prepare hash table A
        hash_table_a = {}
        for path, props in node_a.walk():
            hash_table_a[path] = props
        # prepare hash table B
        hash_table_b = {}
        for path, props in node_b.walk():
            hash_table_b[path] = props
        # compare input tables and generate 3 hash tables: same in A and B, specific for A, specific for B
        diff_tables = [{}, {}, {}]
        for path_a, props_a in hash_table_a.items():
            if path_a in hash_table_b:
                props_b = hash_table_b[path_a]
                props_s = [p for p in props_a if p in props_b]
                props_a = [p for p in props_a if p not in props_s]
                props_b = [p for p in props_b if p not in props_s]
                if props_s:
                    diff_tables[0][path_a] = props_s
                if props_a:
                    diff_tables[1][path_a] = props_a
                if props_b:
                    diff_tables[2][path_a] = props_b
            else:
                diff_tables[1][path_a] = props_a
        for path_b, props_b in hash_table_b.items():
            if path_b not in hash_table_a:
                diff_tables[2][path_b] = props_b
        # convert hash tables into 3 nodes: same in A and B, specific for A, specific for B
        diff_nodes = [Node(node_a.name), Node(node_a.name), Node(node_b.name)]
        for i, d in enumerate(diff_tables):
            for path, props in d.items():
                diff_nodes[i].create(path)
                for p in props:
                    diff_nodes[i].append(p, path)

        return diff_nodes