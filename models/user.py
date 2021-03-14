#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 14:39:33 2017

@author: sarbot
"""

from sqlalchemy import *
from models.base import Base
from models.translator import Translator
from sqlalchemy.orm import relationship
import datetime as dt

class User(Base):
    
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)  # unique
    chat_id = Column(Integer, nullable=False)  # required
    name = Column(String(250), nullable=False)  # required
    date_join = Column(DateTime(), default=dt.datetime.now())
    date_active = Column(DateTime(), default=dt.datetime.now())
    lan1 = Column(String(10), default='de')  # also interface language or 'en'
    lan2 = Column(String(10), default='en')
    translator_id = Column(Integer, ForeignKey('translator.id'))
    translator = relationship(Translator)
    count = Column(Integer(), default=0)

