import os
import fdt
import pytest


def test_fdt_constructor():
    fdt_obj = fdt.FDT()

    assert isinstance(fdt_obj, fdt.FDT)
    assert fdt_obj.root == fdt.Node('/')


def test_fdt_methods():
    fdt_obj = fdt.FDT()

    assert isinstance(fdt_obj, fdt.FDT)

    fdt_obj.add_item(fdt.Property('prop'))
    fdt_obj.set_property("prop", 10, path="/node1")
    fdt_obj.set_property("prop", [10, 20], path="/node1/node2")
    fdt_obj.set_property("prop_bytes", b"\x10\x20", path="/node1/node2")

    assert fdt_obj.exist_node("node1")
    assert fdt_obj.exist_property("prop", "/node1")
    assert fdt_obj.exist_property("prop", "/node1/node2")

    items = fdt_obj.search("")
    assert len(items) == 7

    fdt_obj.remove_property("prop")

    items = fdt_obj.search("")
    assert len(items) == 6
    items = fdt_obj.search("", itype=fdt.ItemType.NODE)
    assert len(items) == 3
    items = fdt_obj.search("", itype=fdt.ItemType.PROP)
    assert len(items) == 3
    items = fdt_obj.search("", itype=fdt.ItemType.PROP_BASE)
    assert len(items) == 0
    items = fdt_obj.search("", itype=fdt.ItemType.PROP_WORDS)
    assert len(items) == 2
    items = fdt_obj.search("", itype=fdt.ItemType.PROP_BYTES)
    assert len(items) == 1
    items = fdt_obj.search("", itype=fdt.ItemType.PROP_STRINGS)
    assert len(items) == 0

    fdt_obj.update_phandles()

    items = fdt_obj.search("phandle", itype=fdt.ItemType.PROP, path="node1", recursive=False)
    assert len(items) == 1

    fdt_obj.remove_node("node1")

    assert len(fdt_obj.search("prop")) == 0
