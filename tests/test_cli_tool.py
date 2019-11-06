import os
import pytest


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_pack(script_runner, data_dir, temp_dir):
    ret = script_runner.run('pydtc', 'pack', '-p', '-o ' +
                            os.path.join(temp_dir, 'imx7d-sdb.dtb'),
                            os.path.join(data_dir, 'imx7d-sdb.dts'))
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_unpack(script_runner, data_dir, temp_dir):
    ret = script_runner.run('pydtc', 'unpack', '-o ' +
                            os.path.join(temp_dir, 'imx7d-sdb.dts'),
                            os.path.join(data_dir, 'imx7d-sdb.dtb'))
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_merge(script_runner, data_dir, temp_dir):
    ret = script_runner.run('pydtc', 'merge',
                            os.path.join(temp_dir, 'merged.dts'),
                            os.path.join(data_dir, 'fdtdump.dts'),
                            os.path.join(data_dir, 'addresses.dts'))
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_diff(script_runner, data_dir, temp_dir):
    out_dir = os.path.join(temp_dir, 'diff_out')
    ret = script_runner.run('pydtc', 'diff', '-o ' + out_dir,
                            os.path.join(data_dir, 'fdtdump.dts'),
                            os.path.join(data_dir, 'addresses.dts'))
    assert ret.success
