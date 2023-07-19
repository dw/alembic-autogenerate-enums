from test_harness.enums import ModifiableEnum


def test_modifiable_enum():
    class Colors(ModifiableEnum):
        RED = "Red"
        GREEN = "Green"

    assert [item.value for item in Colors] == ['Red', 'Green']

    Colors.add_member('Yellow', "Yellow")

    assert [item.value for item in Colors] == ['Red', 'Green', 'Yellow']
