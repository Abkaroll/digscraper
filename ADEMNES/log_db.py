import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

engine = create_engine('sqlite:///ademnes.sqlite3')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base = declarative_base()
Base.metadata.bind = engine


class Attempt(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, nullable=False)
    url = Column(String(250), nullable=False)
    status_code = Column(Integer, nullable=False)
    saved = Column(Boolean, default=False)


# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
