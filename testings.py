#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 14:29:41 2017

@author: sarbot
"""

from models.base import Base
from models.user import User
from models.base import engine
from models.base import session


user = User()
user.name = 'Frank'
session.add(user)
session.commit()