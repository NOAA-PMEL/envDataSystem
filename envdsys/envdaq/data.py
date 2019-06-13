#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 13:45:16 2018

@author: derek
"""


class Data():

    def __init__(self):
        self.buffer = []

    def append(self, data):
        # print('append')
        self.buffer.append(data)
        # print(self.buffer)

    def get(self):
        # print('get')
        output = self.buffer
        # print(self.buffer)
        self.buffer = []
        # print(self.buffer)
        # print(output)
        return output

    def size(self):
        return len(self.buffer)
