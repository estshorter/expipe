import pytest
from lwpipe import TrivialPipeline


def test_trivial_pipeline_basic():
    def no_op():
        return

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
    def no_op():
        return

    def no_op2():
        return

    funcs = [no_op, no_op, no_op2]
    pipe = TrivialPipeline(funcs)
    assert pipe.names == ["no_op", "no_op__2__", "no_op2"]
