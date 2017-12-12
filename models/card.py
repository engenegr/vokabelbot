#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 03:07:46 2017

@author: sarbot
"""

from sqlalchemy import *
from models.base import Base
from models.translator import Translator
from models.user import User
from sqlalchemy.orm import relationship
import datetime as dt

class Card(Base):
    __tablename__ = 'card'
    user_id = Column(Integer(), ForeignKey(User))
    user = relationship(User)
    date = Column(DateTime(), default=dt.datetime.now())
    date_active = Column(DateTime(), default=dt.datetime.now())
    lan1 = Column(String(20))
    lan2 = Column(String(20))
    side1 = Column(String(250))
    side2 = Column(String(250))
    correct = Column(Integer(), default=0)
    wrong = Column(Integer(), default=0)
    
    