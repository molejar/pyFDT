import os
import fdt
import pytest


def test_fdt_constructor():
    fdt_obj = fdt.FDT()

    assert isinstance(fdt_obj, fdt.FDT)
    assert fdt_obj.root == fdt.Node('/')


def test_fdt_object():
    fdt_obj = fdt.FDT()

    assert isinstance(fdt_obj, fdt.FDT)

    fdt_obj.add_item(fdt.Property('prop'))
    fdt_obj.set_property("prop", 10, "/node1")
    fdt_obj.set_property("prop", 10, "/node1/node2")
    fdt_obj.update_phandles()

    assert fdt_obj.exist_node("node1")
    assert fdt_obj.exist_property("prop", "/node1")
    assert fdt_obj.exist_property("prop", "/node1/node2")
    assert len(fdt_obj.search("prop")) == 3

    fdt_obj.remove_property("prop")

    assert len(fdt_obj.search("prop")) == 2

    fdt_obj.remove_node("node1")

    assert len(fdt_obj.search("prop")) == 0
