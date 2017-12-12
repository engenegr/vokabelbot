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
    lan1 = Column(String(10), default='de')
    lan2 = Column(String(10), default='en')
    direction = Column(Integer(), default=3)  # 1 (1->2) 2 (2->1) 3 auto
    direction_train = Column(Integer(), default=3) # as above 3 = mixed
    confirm = Column(Boolean, default=False)  # y/n button to add to dict
    translator_id = Column(Integer, ForeignKey('translator.id'))
    translator = relationship(Translator)

