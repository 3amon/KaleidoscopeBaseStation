# This is so we get the same sqlalchemy.ext.declarative.declarative_base in all of our files
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()