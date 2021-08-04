from __future__ import annotations

from functools import partial

import numpy as np
import pytest
from lwpipe import DumpType, Node, Pipeline
from lwpipe.io import (
    dump_dict_pickle,
    dump_npy,
    dump_pickle,
    dump_savez_compressed,
    load_dict_pickle,
    load_npy,
    load_pickle,
    load_savez_compressed,
)


def mean(x):
    return x[:, :4].mean()


def multiply(x, n: int | float):
    return x * n


def add(x, n: int | float):
    return x + n


def divide(x):
    return x[:, : x.shape[1] // 2].mean(), x[:, x.shape[1] // 2].mean()


def multiply_two_inputs(x, y, n: int | float):
    return x * n, y * n


def ten_times_two_inputs(x, y):
    return x * 10, y * 10


def sum(x):
    return x.sum()


@pytest.fixture
def np_array_2d():
    return np.arange(50).reshape((25, 2))


def test_simple(np_array_2d):
    nodes = [
        Node(
            func=add,
            inputs=(np_array_2d, 1),
        ),
        Node(
            func=sum,
        ),
    ]

    pipe = Pipeline(nodes)
    outputs = pipe.run()
    outputs_np = outputs[0].tolist()
    assert outputs_np == 1275


def test_output(np_array_2d, tmp_path):
    nodes = [
        Node(
            func=divide,
            inputs=np_array_2d,
            outputs=("mean1", "mean2"),
            outputs_dumper=dump_pickle,
            outputs_path=(
                tmp_path / "result1.pickle",
                tmp_path / "result2.pickle",
            ),
            outputs_loader=load_pickle,
        ),
        Node(
            func=ten_times_two_inputs,
        ),
    ]

    pipe = Pipeline(nodes)
    pipe.run()


def test_base(np_array_2d, tmp_path):
    nodes = [
        Node(
            func=mean,
            inputs=np_array_2d,
            outputs="mean",
            outputs_dumper=dump_pickle,
            outputs_path=tmp_path / "result1.pickle",
            outputs_loader=load_pickle,
        ),
        Node(
            func=lambda x: multiply(x, 10),
            name=multiply.__name__,
            outputs="ntimes",
            outputs_dumper=dump_npy,
            outputs_path=tmp_path / "result_multiply.pickle",
            outputs_loader=load_npy,
        ),
        Node(
            func=lambda x: add(x, 10),
            name=add.__name__,
            inputs="mean",
        ),
    ]

    pipe = Pipeline(nodes)
    pipe.run()
    pipe.run(1)
    pipe.run(2)


def test_tuple_output(np_array_2d, tmp_path):
    nodes = [
        Node(
            func=divide,
            inputs=np_array_2d,
            outputs=("mean1", "mean2"),
            outputs_dumper=dump_pickle,
            outputs_path=(
                tmp_path / "mean1.pickle",
                tmp_path / "mean2_pickle",
            ),
            outputs_loader=load_pickle,
        ),
        Node(
            func=ten_times_two_inputs,
            inputs=("mean1", "mean2"),
            outputs_dumper=dump_npy,
            outputs_path=(
                tmp_path / "mul1.npy",
                tmp_path / "mul2.npy",
            ),
        ),
    ]

    pipe = Pipeline(nodes)
    pipe.run()
    pipe.run(nodes[1].func.__name__)


def test_in_out(np_array_2d, tmp_path):
    nodes = [
        Node(
            func=divide,
            inputs=np_array_2d,
            outputs=("mean1", "mean2"),
            outputs_dumper=dump_pickle,
            outputs_path=(
                tmp_path / "mean1",
                tmp_path / "mean2",
            ),
            outputs_loader=load_pickle,
        ),
        Node(
            func=partial(multiply_two_inputs, n=10),
            inputs=("mean1", "mean2"),
            name=multiply_two_inputs.__name__,
        ),
    ]

    pipe = Pipeline(nodes)
    pipe.run()


def test_no_input_at_initial_node():
    nodes = [
        Node(func=lambda: 100),
        Node(
            func=lambda x: 10 * x,
            name="multiply",
        ),
    ]

    pipe = Pipeline(nodes)
    outputs, *_ = pipe.run()
    assert outputs == 1000


def test_none_outputs():
    nodes = [
        Node(func=lambda: 100, outputs=[None]),
        Node(
            func=lambda x: 10 * x,
            name="multiply",
            inputs=[None],
        ),
    ]

    pipe = Pipeline(nodes)
    with pytest.raises(KeyError):
        pipe.run()


def test_resume_duplicate_name():
    nodes = [
        Node(
            func=lambda x: x,
            inputs=100,
            outputs_dumper=dump_pickle,
            outputs_path=".result1.pickle",
            outputs_loader=load_pickle,
        ),
        Node(func=lambda x: x ** 2),
    ]

    pipe = Pipeline(nodes)
    outputs = pipe.run()
    assert outputs[0] == 10000
    outputs = pipe.run(1)
    assert outputs[0] == 10000


def test_duplicate_name():
    add_ = partial(add, n=1)
    pipe = Pipeline([Node(func=add_, inputs=10), Node(func=add_)])
    outputs = pipe.run()
    assert outputs[0] == 12
    assert pipe.nodes[0].name == "anonymous"
    assert pipe.nodes[1].name == "anonymous_2"


def test_batch(np_array_2d, tmp_path):
    nodes = [
        Node(
            func=divide,
            inputs=np_array_2d,
            outputs=("mean_a", "mean_b"),
            outputs_dumper=dump_dict_pickle,
            outputs_dumper_type=DumpType.BATCH,
            outputs_path=tmp_path / "1.pickle",
            outputs_loader=load_dict_pickle,
        ),
        Node(
            func=lambda x, y: (x, y),
            name="2",
            outputs=("a", "b"),
            outputs_dumper=dump_dict_pickle,
            outputs_dumper_type=DumpType.BATCH,
            outputs_path=tmp_path / "2.pickle",
            outputs_loader=load_dict_pickle,
        ),
        Node(
            func=ten_times_two_inputs,
            outputs=("c", "d"),
            inputs=("a", "b"),
            outputs_dumper=dump_savez_compressed,
            outputs_dumper_type=DumpType.BATCH,
            outputs_path=tmp_path / "3.npz",
            outputs_loader=load_savez_compressed,
        ),
        Node(
            func=lambda x, y: (x, y),
        ),
    ]

    pipe = Pipeline(nodes)
    pipe.run()
    pipe.run(1)
    pipe.run(2)
    pipe.run(3)
