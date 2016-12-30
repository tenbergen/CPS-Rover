# !/usr/bin/env python
###########################################################################################
#This file is part of the CPS-Rover Project of the State University of New York at Oswego.
#
#The purpose of robot "KAT" is to navigate a labyrinth made up of perpendicular "paths,"
#find the exit, construct a map of the labyrinth featuring a path to the exit, and sending
#the map to another Dexter Industries GoPiGo.
#The algorithm of traversing the labyrinth workd as follows:
#1. Each intersection has four options: turn right, go straight, turn left, or turn around.
#1.1 T-Junctions are intersections where either right, straight, or left isn't available.
#1.2 Dead-ends are intersections where only turn around is available.
#2. Decision priority at intersections is as follows:
#2.1 If at intersection, turn right.
#2.2 Else if right turn isn't available, go straight.
#2.3 Else if straight isn't available, turn left.
#2.4 Else (i.e., if left turn isn't available), turn around.
#3. Whenever an intersection is reached, make a turn, and add it to the map.
#4. If dead-end is reached, turn around, take the next available turn at the previous
#   intersection and mark it correspondingly on the map.
#Exit is identified by the user pressing the space bar.
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

class Node:
    """
    Class Node
    """
    def __init__(self, value):
        self.left = None
        self.data = value
        self.right = None
