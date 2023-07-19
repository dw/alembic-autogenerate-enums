from enum import Enum

from sqlalchemy import Column
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer
from sqlalchemy.orm import (DeclarativeBase, Mapped, declarative_base,
                            mapped_column)

from test_harness.enums import ModifiableEnum

Base = declarative_base()

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

class BaseV2(DeclarativeBase):
    pass

class SimpleModelMapped(BaseV2):
    __tablename__ = "simple_model_mapped"
    id: Mapped[int] = mapped_column(primary_key=True)
    enum_field: Mapped[SimpleEnum] = mapped_column(SqlEnum(SimpleEnum))
