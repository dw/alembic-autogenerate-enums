from enum import Enum

from sqlalchemy import Column
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SimpleEnum(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"

class SimpleModel(Base):
    __tablename__ = "simple_model"
    id = Column(Integer, primary_key=True)
    enum_field = Column(SqlEnum(SimpleEnum), nullable=False)
