#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 14:28:26 2017

@author: sarbot
"""
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()  # declare Base before importing models since they inherit from it

from models.translator import Translator
from models.user import User

#declare engine and session (create/modify db if not exists)
engine = create_engine('sqlite:///models/sql.db')
Base.metadata.create_all(engine, checkfirst=True)
print('create_all')
Session = sessionmaker(bind=engine)
session = Session()  # use this session everywhere where its imported