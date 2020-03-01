import os
import pytest


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_pack(script_runner, data_dir, temp_dir):
    src_file = os.path.join(data_dir, 'imx7d-sdb.dts')
    out_file = os.path.join(temp_dir, 'imx7d-sdb.dtb')

    ret = script_runner.run('pydtc', 'pack', '-p', '-o ' + out_file, src_file)
    assert ret.success
    assert ret.stderr == ''

    ret = script_runner.run('pydtc', 'pack', '-p', '-o ' + out_file)
    assert not ret.success
    assert 'error' in ret.stderr

    ret = script_runner.run('pydtc', 'pack', '-p', '-o ' + out_file, 'not_valid.dts')
    assert not ret.success
    assert ret.stderr == 'File doesnt exist: not_valid.dts\n'


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_unpack(script_runner, data_dir, temp_dir):
    src_file = os.path.join(data_dir, 'imx7d-sdb.dtb')
    out_file = os.path.join(temp_dir, 'imx7d-sdb.dts')

    ret = script_runner.run('pydtc', 'unpack', '-o ' + out_file, src_file)
    assert ret.success
    assert ret.stderr == ''


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_merge(script_runner, data_dir, temp_dir):
    in1_file = os.path.join(data_dir, 'fdtdump.dts')
    in2_file = os.path.join(data_dir, 'addresses.dts')
    out_file = os.path.join(temp_dir, 'merged.dts')

    ret = script_runner.run('pydtc', 'merge', out_file, in1_file, in2_file)
    assert ret.success
    assert ret.stderr == ''


@pytest.mark.script_launch_mode('subprocess')
def test_pydtc_diff(script_runner, data_dir, temp_dir):
    in1_file = os.path.join(data_dir, 'fdtdump.dts')
    in2_file = os.path.join(data_dir, 'addresses.dts')
    out_dir = os.path.join(temp_dir, 'diff_out')

    ret = script_runner.run('pydtc', 'diff', '-o ' + out_dir, in1_file, in2_file)
    assert ret.success
    assert ret.stderr == ''
