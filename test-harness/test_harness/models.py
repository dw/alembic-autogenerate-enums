from enum import Enum

from sqlalchemy import Column
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer
from sqlalchemy.orm import (DeclarativeBase, Mapped, declarative_base,
                            mapped_column)
from test_harness.columns import EnumCustomType
from test_harness.enums import ModifiableEnum

Base = declarative_base()
BaseV2 = declarative_base()

class BaseV3(DeclarativeBase):
    pass

class SimpleEnum(ModifiableEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"

class SimpleModel(Base):
    __tablename__ = "simple_model"
    id = Column(Integer, primary_key=True)
    enum_field = Column(SqlEnum(SimpleEnum), nullable=False)

class SimpleModelCustomEnum(BaseV2):
    __tablename__ = "simple_model_custom_enum"
    id = Column(Integer, primary_key=True)
    enum_field = Column(EnumCustomType(SimpleEnum), nullable=False)

class SimpleModelMapped(BaseV3):
    __tablename__ = "simple_model_mapped"
    id: Mapped[int] = mapped_column(primary_key=True)
    enum_field: Mapped[SimpleEnum] = mapped_column(SqlEnum(SimpleEnum))
