
import fdt
import pytest

DIRECTORY="tests/data/"


def test_01():
    with open(DIRECTORY + "addresses.dts") as f:
        data = f.read()

    fdt_obj = fdt.parse_dts(data)

    with pytest.raises(Exception):
        blob = fdt_obj.to_dtb()

    blob = fdt_obj.to_dtb(17)


def test_02():
    with open(DIRECTORY + "comments.dts") as f:
        data = f.read()

    fdt_obj = fdt.parse_dts(data)
    print(fdt_obj)


def test_03():
    with open(DIRECTORY + "appendprop.dts") as f:
        data = f.read()

    with pytest.raises(AssertionError):
        fdt_obj = fdt.parse_dts(data)


def test_04():
    with open(DIRECTORY + "base.dts") as f:
        data = f.read()

    with pytest.raises(ValueError):
        fdt_obj = fdt.parse_dts(data)

