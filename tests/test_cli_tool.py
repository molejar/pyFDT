
import pytest

DIRECTORY='tests/data/'


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_todts(script_runner):
    ret = script_runner.run('pydtc', 'todts', DIRECTORY + 'imx7d-sdb.dtb')
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_todtb(script_runner):
    ret = script_runner.run('pydtc', 'todtb', DIRECTORY + 'imx7d-sdb.dts')
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_merge(script_runner):
    ret = script_runner.run('pydtc', 'merge', 'merged.dts', DIRECTORY + 'fdtdump.dts', DIRECTORY + 'addresses.dts')
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_diff(script_runner):
    ret = script_runner.run('pydtc', 'diff', DIRECTORY + 'fdtdump.dts', DIRECTORY + 'addresses.dts')
    assert ret.success
