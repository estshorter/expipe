import pytest
from lwpipe import TrivialPipeline


def no_op():
    return


def test_trivial_pipeline_basic():
    funcs = [no_op, no_op]
    pipe = TrivialPipeline(funcs)
    pipe.run()
    pipe.run(1, 1)
    pipe.run(0, 1)
    with pytest.raises(ValueError):
        pipe.run(0, 2)
    with pytest.raises(ValueError):
        pipe.run(1, 0)
    with pytest.raises(ValueError):
        pipe.run(2, 2)


def test_trivial_pipeline():
    def no_op2():
        return

    funcs = [no_op, no_op, no_op2]
    pipe = TrivialPipeline(funcs)
    assert pipe.names == ["no_op", "no_op__2__", "no_op2"]


def test_name_uniqueness():
    funcs = [no_op, no_op]
    with pytest.raises(ValueError):
        TrivialPipeline(funcs, names=["a1", "a1"])


def test_string_from_to():
    funcs = [no_op, no_op, no_op]
    pipe = TrivialPipeline(funcs, names=["func1", "func2", "func3"])
    pipe.run("func1", "func2")
    pipe.run("func2", "func3")
    pipe.run("func1", "func3")
    pipe.run("func3", "func3")
    with pytest.raises(ValueError):
        pipe.run("func3", "func1")
    with pytest.raises(ValueError):
        pipe.run("func2", "func1")
