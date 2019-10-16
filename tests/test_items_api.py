import fdt
import struct
import pytest


def test_header():
    header = fdt.Header()
    header.version = fdt.Header.MAX_VERSION

    assert header.magic == fdt.Header.MAGIC_NUMBER
    assert header.version == fdt.Header.MAX_VERSION
    assert header.size == fdt.Header.MAX_SIZE

    with pytest.raises(ValueError):
        header.version = fdt.Header.MAX_VERSION + 1

    blob = struct.pack('>7I', fdt.Header.MAGIC_NUMBER, 0, 0, 0, 0, 1, 1)
    header = fdt.Header.parse(blob)

    assert header.magic == fdt.Header.MAGIC_NUMBER
    assert header.version == 1
    assert header.size == 32


def test_base_property():
    prop = fdt.Property('prop')

    assert isinstance(prop, fdt.Property)
    assert prop.name == 'prop'

    with pytest.raises(AssertionError):
        _ = fdt.Property('prop\0')
    with pytest.raises(AssertionError):
        _ = fdt.Property(5)

    prop1 = fdt.Property('prop1')
    assert prop1 != prop

    prop1 = fdt.Property('prop')
    assert prop1 == prop

    str_data = prop.to_dts()
    assert str_data == 'prop;\n'

    blob_data, str_data, pos = prop.to_dtb('')
    assert blob_data == struct.pack('>III', 0x03, 0, 0)
    assert str_data == 'prop\0'
    assert pos == 12


def test_strings_property():
    prop = fdt.PropStrings('prop', 'test', 'test')

    assert isinstance(prop, fdt.PropStrings)
    assert prop.name == 'prop'
    assert len(prop) == 2
    assert prop.data == ['test', 'test']

    with pytest.raises(AssertionError):
        prop.append('test\0')
    with pytest.raises(AssertionError):
        prop.append(5)

    prop1 = fdt.PropStrings('prop', 'test', 'test', 'test')
    assert prop1 != prop

    prop.append("test")
    assert len(prop) == 3
    assert prop1 == prop

    str_data = prop.to_dts()
    assert str_data == 'prop = "test", "test", "test";\n'


def test_words_property():
    prop = fdt.PropWords('prop', 0x11111111, 0x55555555)

    assert isinstance(prop, fdt.PropWords)
    assert prop.name == 'prop'
    assert len(prop) == 2
    assert prop.data == [0x11111111, 0x55555555]

    with pytest.raises(AssertionError):
        prop.append('test')
    with pytest.raises(AssertionError):
        prop.append(0x5555555555)

    prop1 = fdt.PropWords('prop', 0x11111111, 0x55555555, 0x00)
    assert prop1 != prop

    prop.append(0x00)
    assert len(prop) == 3
    assert prop1 == prop

    str_data = prop.to_dts()
    assert str_data == 'prop = <0x11111111 0x55555555 0x0>;\n'


def test_bytes_property():
    prop = fdt.PropBytes('prop', [0x10, 0x50])

    assert isinstance(prop, fdt.PropBytes)
    assert prop.name == 'prop'
    assert len(prop) == 2
    assert prop.data == b"\x10\x50"

    with pytest.raises(AssertionError):
        prop.append('test')
    with pytest.raises(AssertionError):
        prop.append(256)

    prop1 = fdt.PropBytes('prop', [0x10, 0x50, 0x00])
    assert prop1 != prop

    prop.append(0x00)
    assert len(prop) == 3
    assert prop1 == prop

    str_data = prop.to_dts()
    assert str_data == 'prop = [10 50 00];\n'


def test_node():
    # create node object
    node = fdt.Node('/')
    node.append(fdt.Property('prop'))
    node.append(fdt.PropStrings('prop_str', 'test', 'test'))
    node.append(fdt.PropWords('prop_word', 0x11111111, 0x55555555))
    node.append(fdt.PropBytes('prop_byte', [0x10, 0x50]))
    subnode0 = fdt.Node('subnode0')
    subnode0.append(fdt.Property('prop0'))
    subnode0.append(fdt.PropStrings('prop_str0', 'test'))
    subnode1 = fdt.Node('subnode1')
    subnode1.append(fdt.Property('prop1'))
    subnode1.append(fdt.PropWords('prop_word1', 0x11111111))
    subnode0.append(subnode1)
    node.append(subnode0)

    assert isinstance(node, fdt.Node)
    assert node.name == '/'
    assert len(node.props) == 4
    assert len(node.nodes) == 1

    # Use only node constructor
    new_node = fdt.Node('/',
                        fdt.Property('prop'),
                        fdt.PropStrings('prop_str', 'test', 'test'),
                        fdt.PropWords('prop_word', 0x11111111, 0x55555555),
                        fdt.PropBytes('prop_byte', [0x10, 0x50]),
                        fdt.Node('subnode0',
                                 fdt.Property('prop0'),
                                 fdt.PropStrings('prop_str0', 'test'),
                                 fdt.Node('subnode1',
                                          fdt.Property('prop1'),
                                          fdt.PropWords('prop_word1', 0x11111111)
                                          )
                                 )
                        )

    assert node == new_node

    with pytest.raises(AssertionError):
        node.append('test')
    with pytest.raises(Exception):
        node.append(256)
    with pytest.raises(Exception):
        node.append(fdt.Property('prop'))

    copy_node = node.copy()
    assert copy_node == node

    copy_node.set_property('prop_word', [0x10, 0x50])
    assert copy_node != node

    # export to dts
    str_data = node.to_dts()
    out = "/ {\n"
    out += "    prop;\n"
    out += "    prop_str = \"test\", \"test\";\n"
    out += "    prop_word = <0x11111111 0x55555555>;\n"
    out += "    prop_byte = [10 50];\n"
    out += "    subnode0 {\n"
    out += "        prop0;\n"
    out += "        prop_str0 = \"test\";\n"
    out += "        subnode1 {\n"
    out += "            prop1;\n"
    out += "            prop_word1 = <0x11111111>;\n"
    out += "        };\n"
    out += "    };\n"
    out += "};\n"

    assert str_data == out


def test_node_set_property():
    root_node = fdt.Node('/')

    # add properties into node by set_property method
    root_node.set_property('prop', None)
    root_node.set_property('int_prop', 1000)
    root_node.set_property('list_int_prop', [1, 2])
    root_node.set_property('str_prop', 'value')
    root_node.set_property('list_str_prop', ['value1', 'value2'])
    root_node.set_property('bytes_prop', b'\x00\x55\x66')

    # validate types and values
    assert len(root_node.props) == 6
    assert isinstance(root_node.get_property('prop'), fdt.Property)
    assert isinstance(root_node.get_property('int_prop'), fdt.PropWords)
    assert root_node.get_property('int_prop').value == 1000
    assert isinstance(root_node.get_property('list_int_prop'), fdt.PropWords)
    assert root_node.get_property('list_int_prop').data == [1, 2]
    assert isinstance(root_node.get_property('str_prop'), fdt.PropStrings)
    assert root_node.get_property('str_prop').value == 'value'
    assert isinstance(root_node.get_property('list_str_prop'), fdt.PropStrings)
    assert root_node.get_property('list_str_prop').data == ['value1', 'value2']
    assert isinstance(root_node.get_property('bytes_prop'), fdt.PropBytes)
    assert root_node.get_property('bytes_prop').data == b'\x00\x55\x66'

    # update property in node by set_property method
    root_node.set_property('list_int_prop', [1, 2, 3])

    # validate property value
    assert root_node.get_property('list_int_prop').data == [1, 2, 3]