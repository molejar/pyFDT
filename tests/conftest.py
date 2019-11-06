import os
import pytest


@pytest.fixture(scope="module")
def data_dir():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        raise Exception(f"Directory doesnt exist: {data_dir}")
    return data_dir


@pytest.fixture(scope="module")
def temp_dir():
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir
