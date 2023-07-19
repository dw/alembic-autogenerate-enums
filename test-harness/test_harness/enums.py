from enum import Enum, EnumMeta

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import ENUM as PostgresENUM


class ModifiableEnumMeta(EnumMeta):
    def __call__(cls, value, names=None, *, module=None, qualname=None, type=None, start=1):
        """Either returns an existing member, or creates a new enum class."""
        if names is None:  # simple value lookup
            return super().__call__(value)
        # otherwise, create a new enum type
        return cls._create_enum(value, names, module=module, qualname=qualname, type=type, start=start)

    def __getitem__(cls, name):
        """Return the correct member, or raise an appropriate error."""
        try:
            return cls._member_map_[name]
        except KeyError:
            raise ValueError("%r is not a valid member of %s" % (name, cls.__name__))

    def __iter__(cls):
        """Return an iterator over the members, preserving their order."""
        return iter(cls._member_map_.values())

    def __contains__(cls, member):
        """Return True if the given member value exists in the enum class."""
        return member in cls._member_map_

    def add_member(cls, name, value):
        """Add a new member to the enum class."""
        if name not in cls._member_map_:
            # Create a new enum member
            member = object.__new__(cls)
            member._value_ = value
            member._name_ = name
            # Update the internal maps
            cls._member_map_[name] = member
            cls._value2member_map_[value] = member

    def remove_member(cls, name):
        """Remove a member from the enum class."""
        if name in cls._member_map_:
            # Remove the enum member
            member = cls._member_map_.pop(name)
            del cls._value2member_map_[member.value]

class ModifiableEnum(Enum, metaclass=ModifiableEnumMeta):
    """
    Used for testing harnesses that need to modify enum values.
    """


def sync_sqlalchemy(model, enum_class: ModifiableEnum):
    """
    SQLAlchemy "Enum" columns copy over the enum values into an internal structure at runtime. Any time
    the enum values are changed, therefore, we need to to re-sync the value of the SQLAlchemy `enums` list with our
    enum object.

    """
    for column in model.__table__.c:
        if isinstance(column.type, (SQLAlchemyEnum, PostgresENUM)) and column.type.python_type == enum_class:
            # Found a column with the old Enum type
            # Replace it with the new type
            assert column.type.enums
            column.type.enums = [item.value for item in enum_class]
