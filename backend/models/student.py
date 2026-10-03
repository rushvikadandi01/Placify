from sqlalchemy import Column, Float, Integer, String

from ..database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    target_role = Column(String)
    programming_language = Column(String)
    experience_level = Column(String)
    hours_per_day = Column(Float)