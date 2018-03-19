
import fdt
import struct
import unittest


class HeaderTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        header = fdt.Header()
        header.version = fdt.Header.MAX_VERSION

        self.assertEqual(header.magic, fdt.Header.MAGIC_NUMBER)
        self.assertEqual(header.version, fdt.Header.MAX_VERSION)
        self.assertEqual(header.size, fdt.Header.MAX_SIZE)

    def test_version(self):
        header = fdt.Header()
        with self.assertRaises(ValueError):
            header.version = fdt.Header.MAX_VERSION + 1

    def test_parse(self):
        blob = struct.pack('>7I', fdt.Header.MAGIC_NUMBER, 0, 0, 0, 0, 1, 1)
        header = fdt.Header.parse(blob)

        self.assertEqual(header.magic, fdt.Header.MAGIC_NUMBER)
        self.assertEqual(header.version, 1)
        self.assertEqual(header.size, 32)


class PropertyTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        prop = fdt.Property('prop')
        self.assertIsInstance(prop, fdt.Property)
        self.assertEqual(prop.name, 'prop')
        with self.assertRaises(AssertionError):
            prop = fdt.Property('prop\0')
        with self.assertRaises(AssertionError):
            prop = fdt.Property(5)

    def test_compare(self):
        prop1 = fdt.Property('prop1')
        prop2 = fdt.Property('prop2')
        self.assertEqual(prop1, prop1)
        self.assertNotEqual(prop1, prop2)

    def test_export(self):
        prop = fdt.Property('prop')
        str_data = prop.to_dts()
        self.assertEqual(str_data, 'prop;\n')
        blob_data, str_data, pos = prop.to_dtb('')
        self.assertEqual(blob_data, struct.pack('>III', 0x03, 0, 0))
        self.assertEqual(str_data, 'prop\0')
        self.assertEqual(pos, 12)


class PropStringsTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        prop = fdt.PropStrings('prop')
        prop.append("test")
        prop.append("test")
        self.assertIsInstance(prop, fdt.PropStrings)
        self.assertEqual(prop.name, 'prop')
        self.assertEqual(len(prop), 2)
        with self.assertRaises(AssertionError):
            prop.append('test\0')
        with self.assertRaises(AssertionError):
            prop.append(5)

    def test_compare(self):
        prop1 = fdt.PropStrings('prop', 'test', 'test')
        prop2 = fdt.PropStrings('prop', 'test', 'test', 'test')
        self.assertEqual(prop1, prop1)
        self.assertNotEqual(prop1, prop2)
        prop1.append("test")
        self.assertEqual(prop1, prop2)
        prop1.append("test")
        self.assertNotEqual(prop1, prop2)

    def test_export(self):
        prop = fdt.PropStrings('prop', 'test', 'test')
        str_data = prop.to_dts()
        self.assertEqual(str_data, 'prop = "test", "test";\n')


class PropWordsTestCase(unittest.TestCase):

    def setUp(self):
        self.prop_a = fdt.PropWords('prop', 0x11111111, 0x55555555)
        self.prop_b = fdt.PropWords('prop', 0x11111111, 0x55555555, 0x00)

    def tearDown(self):
        pass

    def test_init(self):
        self.assertIsInstance(self.prop_a, fdt.Property)
        self.assertEqual(self.prop_a.name, 'prop')
        self.assertEqual(len(self.prop_a), 2)
        self.prop_a.append(0x00)
        self.assertEqual(len(self.prop_a), 3)
        with self.assertRaises(AssertionError):
            self.prop_a.append('test')
        with self.assertRaises(AssertionError):
            self.prop_a.append(0x5555555555)

    def test_compare(self):
        self.assertEqual(self.prop_a, self.prop_a)
        self.assertNotEqual(self.prop_a, self.prop_b)
        self.prop_a.append(0x00)
        self.assertEqual(self.prop_a, self.prop_b)
        self.prop_a.append(0x00)
        self.assertNotEqual(self.prop_a, self.prop_b)

    def test_export(self):
        str_data = self.prop_a.to_dts()
        self.assertEqual(str_data, 'prop = <0x11111111 0x55555555>;\n')


class PropBytesTestCase(unittest.TestCase):

    def setUp(self):
        self.prop_a = fdt.PropBytes('prop', [0x10, 0x50])
        self.prop_b = fdt.PropBytes('prop', [0x10, 0x50, 0x00])

    def tearDown(self):
        pass

    def test_init(self):
        self.assertIsInstance(self.prop_a, fdt.Property)
        self.assertEqual(self.prop_a.name, 'prop')
        self.assertEqual(len(self.prop_a), 2)
        self.prop_a.append(0x00)
        self.assertEqual(len(self.prop_a), 3)
        with self.assertRaises(AssertionError):
            self.prop_a.append('test')
        with self.assertRaises(AssertionError):
            self.prop_a.append(256)

    def test_compare(self):
        self.assertEqual(self.prop_a, self.prop_a)
        self.assertNotEqual(self.prop_a, self.prop_b)
        self.prop_a.append(0x00)
        self.assertEqual(self.prop_a, self.prop_b)
        self.prop_a.append(0x00)
        self.assertNotEqual(self.prop_a, self.prop_b)

    def test_export(self):
        str_data = self.prop_a.to_dts()
        self.assertEqual(str_data, 'prop = [10 50];\n')


class NodeTestCase(unittest.TestCase):

    def setUp(self):
        self.node_a = fdt.Node('/')
        self.node_a.append(fdt.Property('prop'))
        self.node_a.append(fdt.PropStrings('prop_str', 'test', 'test'))
        self.node_a.append(fdt.PropWords('prop_word', 0x11111111, 0x55555555))
        self.node_a.append(fdt.PropBytes('prop_byte', [0x10, 0x50]))
        self.node_a.append(fdt.Node('sub_node'))

    def tearDown(self):
        pass

    def test_init(self):
        self.assertIsInstance(self.node_a, fdt.Node)
        self.assertEqual(self.node_a.name, '/')
        self.assertEqual(len(self.node_a.props), 4)
        self.assertEqual(len(self.node_a.nodes), 1)
        with self.assertRaises(TypeError):
            self.node_a.append('test')
        with self.assertRaises(TypeError):
            self.node_a.append(256)
        with self.assertRaises(Exception):
            self.node_a.append(fdt.Property('prop'))

    def test_compare(self):
        self.assertEqual(self.node_a, self.node_a)
        node_b = self.node_a.copy()
        self.assertEqual(self.node_a, node_b)
        node_b.append(fdt.PropBytes('prop_next', [0x10, 0x50]))
        self.assertNotEqual(self.node_a, node_b)

    def test_append(self):
        root_node = self.node_a.copy()
        root_node.append(fdt.Node('node_a', props=[fdt.Property('prop_a')]))
        root_node.append(fdt.Node('node_b', props=[fdt.Property('prop_b')]))
        root_node.append(fdt.Node('node_c', props=[fdt.Property('prop_c')]))
        node = root_node.get_subnode('node_a')
        self.assertIsInstance(node, fdt.Node)
        prop = node.get_property('prop_a')
        self.assertIsInstance(prop, fdt.Property)
        node.remove_property('prop_a')
        prop = node.get_property('prop_a')
        self.assertIsNone(prop, fdt.Property)

    def test_merge(self):
        root_node = self.node_a.copy()
        root_node.append(fdt.Node('node_a', props=[fdt.Property('prop_a')]))
        root_node.append(fdt.Node('node_b', props=[fdt.Property('prop_b')]))
        root_node.append(fdt.Node('node_c', props=[fdt.Property('prop_c')]))
        node = self.node_a.copy()
        node.set_name("test_node")
        root_node.merge(node)
        self.assertNotEqual(root_node, node)

    def test_export(self):
        str_data = self.node_a.to_dts()
        out  = "/ {\n"
        out += "    prop;\n"
        out += "    prop_str = \"test\", \"test\";\n"
        out += "    prop_word = <0x11111111 0x55555555>;\n"
        out += "    prop_byte = [10 50];\n"
        out += "    sub_node {\n"
        out += "    };\n"
        out += "};\n"
        self.assertEqual(str_data, out)


if __name__ == '__main__':
    unittest.main()