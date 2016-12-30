# !/usr/bin/env python
###########################################################################################
#This file is part of the CPS-Rover Project of the State University of New York at Oswego.
#
#The purpose of robot "PLATO" is to navigate a labyrinth made up of perpendicular "paths,"
#according to a map that it received. PLATO shall identify intersections and take the
#corresponding turns outlined in the map.
#
#Copyright (c) 2016 Andres Ramos, Keith Martin, Bastian Tenbergen
#Principle Investigator and Project Lead: Bastian Tenbergen, bastian.tenbergen@oswego.edu
#
#License: Creative Commons BY-NC-SA 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including the rights to use, copy, modify, merge,
#publish, and/or distribute copies of the Software for non-commercial purposes,
#and to permit persons to whom the Software is furnished to do so,
#subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
###########################################################################################

from intersection_enum import *


class Node:
    def __init__(self):
        self.left = None
        self.right = None
        self.forward = None
        self.backward = None
        self.next = None
        self.prev = None


class linked_list:
    leftTurnSkipped = False
    turns = []
    skipCountTurn = 0

    def __init__(self):
        self.head = Node()
        self.currentNode = None
        self.prevNode = None
        self.tail = self.head

    def insert(self, left, right, forward, backward):
        self.setNode(left, right, forward, backward)

    # A utility function to insert a new node with the given key
    def insert(self, left, right, forward, backward):
        self.setNode(left, right, forward, backward)

    def setNode(self, left, right, forward, backward):
        newNode = Node()
        if left == intersection_enum.Left:
            if self.tail.left is None and self.skipCountTurn == 0:
                newNode.prev = self.tail
                self.tail.left = intersection_enum.Chosen
                self.tail.next = newNode
                self.tail.right = right
                self.tail.forward = forward
                self.tail.backward = backward
                self.tail = newNode
            elif self.skipCountTurn > 0:
                self.skipCountTurn -= 1
        elif right == intersection_enum.Right:
            if self.tail.right is None and self.skipCountTurn == 0:
                newNode.prev = self.tail
                self.tail.right = intersection_enum.Chosen
                self.tail.next = newNode
                self.tail.left = left
                self.tail.forward = forward
                self.tail.backward = backward
                self.tail = newNode
            elif self.skipCountTurn > 0:
                self.skipCountTurn -= 1
        elif forward == intersection_enum.Forward:
            if self.tail.forward is None and self.skipCountTurn == 0:
                newNode.prev = self.tail
                self.tail.forward = intersection_enum.Chosen
                self.tail.next = newNode
                self.tail.left = left
                self.tail.right = right
                self.tail.backward = backward
                self.tail = newNode
            elif self.skipCountTurn > 0:
                self.skipCountTurn -= 1
            '''elif self.tail.forward is None and self.skipLeftTurn() == False:
                newNode.prev = self.tail
                self.tail.forward = intersection_enum.Chosen
                self.tail.next = newNode
                self.tail.left = left
                self.tail.right = right
                self.tail.backward = backward
                self.tail = newNode'''
        elif backward == intersection_enum.Backward:
            self.skipCountTurn += 1
            if self.tail.prev.right == intersection_enum.Chosen:
                if self.tail.prev.forward != intersection_enum.Deleted:
                    newNode.prev = self.tail.prev
                    self.tail.prev.next = self.tail.next
                    self.tail.prev.next = newNode
                    self.tail.prev.forward = intersection_enum.Chosen
                    self.tail.prev.right = intersection_enum.Deleted
                    self.tail = newNode
                else:
                    newNode.prev = self.tail.prev
                    self.tail.prev.next = self.tail.next
                    self.tail.prev.next = newNode
                    self.tail.prev.left = intersection_enum.Chosen
                    self.tail.prev.right = intersection_enum.Deleted
                    self.tail = newNode
            elif self.tail.prev.forward == intersection_enum.Chosen:
                if self.tail.prev.left != intersection_enum.Deleted:
                    newNode.prev = self.tail.prev
                    self.tail.prev.next = self.tail.next
                    self.tail.prev.next = newNode
                    self.tail.prev.left = intersection_enum.Chosen
                    self.tail.prev.forward = intersection_enum.Deleted
                    self.tail = newNode
                else:
                    self.tail = self.tail.prev
                    self.tail.next = None
                    self.tail.forward = intersection_enum.Deleted
                    self.setNode(None, None, None, intersection_enum.Backward)
            elif self.tail.prev.left == intersection_enum.Chosen:
                self.tail = self.tail.prev
                self.tail.next = None
                self.tail.left = intersection_enum.Deleted
                self.setNode(None, None, None, intersection_enum.Backward)

    '''def skipLeftTurn(self):
        if (self.tail.prev.left == intersection_enum.Chosen) and (self.tail.prev.right == intersection_enum.Deleted):
            if (self.tail.prev.forward == intersection_enum.Deleted) and (self.leftTurnSkipped == False):
                self.leftTurnSkipped = True
                return True
        self.leftTurnSkipped = False
        return False'''

    def done(self):
        final_map = []
        for turn in self.turns:
            print turn
        self.tail = self.head
        print 'WHILE LOOP'
        while self.tail != None:
            print "NODE:"
            if self.tail.left == intersection_enum.Chosen:
                final_map.append(intersection_enum.Left)
            elif self.tail.right == intersection_enum.Chosen:
                final_map.append(intersection_enum.Right)
            if self.tail.forward == intersection_enum.Chosen:
                final_map.append(intersection_enum.Forward)
            elif self.tail.backward == intersection_enum.Chosen:
                final_map.append(intersection_enum.Backward)
            self.tail = self.tail.next
        return final_map
            
