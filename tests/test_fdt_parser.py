import os
import fdt
import pytest


def test_01(data_dir):
    with open(os.path.join(data_dir, "addresses.dts")) as f:
        data = f.read()

    fdt_obj = fdt.parse_dts(data)
    assert fdt_obj.get_property('compatible').value == "test_addresses"
    assert fdt_obj.get_property('#address-cells').value == 2
    assert fdt_obj.get_property('#size-cells').value == 2
    assert fdt_obj.get_node('identity-bus@0') == fdt.Node('identity-bus@0')
    assert fdt_obj.get_node('simple-bus@1000000') == fdt.Node('simple-bus@1000000',
                                                              fdt.PropWords('#address-cells', 2),
                                                              fdt.PropWords('#size-cells', 1))
    with pytest.raises(Exception):
        _ = fdt_obj.to_dtb()

    data = fdt_obj.to_dtb(17)
    assert isinstance(data, bytes)
    assert len(data) == 254


def test_02(data_dir):
    with open(os.path.join(data_dir, "comments.dts")) as f:
        data = f.read()

    fdt_obj = fdt.parse_dts(data)
    assert len(fdt_obj.root.props) == 10
    assert len(fdt_obj.root.nodes) == 1


def test_03(data_dir):
    with open(os.path.join(data_dir, "appendprop.dts")) as f:
        data = f.read()

    with pytest.raises(AssertionError):
        _ = fdt.parse_dts(data)


def test_04(data_dir):
    with open(os.path.join(data_dir, "base.dts")) as f:
        data = f.read()

    with pytest.raises(AssertionError):
        _ = fdt.parse_dts(data)

