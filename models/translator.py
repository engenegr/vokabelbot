#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 14:38:39 2017

@author: sarbot
"""
from sqlalchemy import *
from models.base import Base
from sqlalchemy.orm import relationship


class Translator(Base):
    __tablename__ = 'translator'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    url = Column(String(250))