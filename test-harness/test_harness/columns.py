from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer, TypeDecorator


class EnumCustomType(TypeDecorator):
    """
    Sample implementation of a custom enum modifier
    """
    impl = SqlEnum

    def __init__(self, *args, **kwargs):
        super().__init__(*args, name="test", **kwargs)
