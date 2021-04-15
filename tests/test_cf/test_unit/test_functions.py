import inspect

import pytest

from cloud_radar.cf.unit import functions
from cloud_radar.cf.unit._template import Template, add_metadata


def test_ref():

    template = {"Parameters": {"foo": {"Value": "bar"}}}

    add_metadata(template, Template.Region)

    template = Template(template)

    for i in inspect.getmembers(Template):
        if not i[0].startswith("_"):
            if isinstance(i[1], str):
                result = functions.ref(template, f"AWS::{i[0]}")
                assert (
                    result == i[1]
                ), "Should be able to reference all pseudo variables."

    result = functions.ref(template, "foo")

    assert result == "bar", "Should reference parameters."

    result = functions.ref(template, "SomeResource")

    assert (
        result == "SomeResource"
    ), "If not a psedo var or parameter it should return the input."

    fake = "AWS::FakeVar"

    with pytest.raises(ValueError) as e:
        functions.ref(template, fake)

    assert f"Unrecognized AWS Pseduo variable: '{fake}'." in str(e.value)


def test_if():

    template = {"Conditions": {"test": False}}

    result = functions.if_(template, ["test", "true_value", "false_value"])

    assert result == "false_value", "Should return the false value."

    template["Conditions"]["test"] = True

    result = functions.if_(template, ["test", "true_value", "false_value"])

    assert result == "true_value", "Should return the true value."

    with pytest.raises((Exception)):
        # First value should the name of the condition to lookup
        functions.if_(template, [True, "True", "False"])


def test_equals():
    # AWS is not very clear on what is valid here?
    # > A value of any type that you want to compare.

    true_lst = [True, "foo", 5, ["test"], {"foo": "foo"}]
    false_lst = [False, "bar", 10, ["bar"], {"bar": "bar"}]

    for idx, true in enumerate(true_lst):
        false = false_lst[idx]

        assert functions.equals([true, true]), f"Should compare {type(true)} as True."

        assert not functions.equals(
            [true, false]
        ), f"Should compare {type(true)} as False."


def test_sub():
    template_dict = {"Parameters": {"Foo": {"Value": "bar"}}}

    template = Template(template_dict)

    assert (
        functions.sub(template, "Foo ${Foo}") == "Foo bar"
    ), "Should subsuite a parameter."

    result = functions.sub(template, "not ${!Test}")

    assert result == "not ${Test}", "Should return a string literal."

    add_metadata(template_dict, "us-east-1")

    template = Template(template_dict)

    result = functions.sub(template, "${AWS::Region} ${Foo} ${!BASH_VAR}")

    assert result == "us-east-1 bar ${BASH_VAR}", "Should render multiple variables."
