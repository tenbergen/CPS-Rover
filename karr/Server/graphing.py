#Source: David Eppstein, UC Irvine, 2002
#https://www.ics.uci.edu/~eppstein/161/python/dijkstra.py

from priodict import priorityDictionary
from math import sqrt

def Dijkstra(G,start,end=None):
	D = {}
	P = {}
	Q = priorityDictionary()
	Q[start] = 0
	for v in Q:
		D[v] = Q[v]
		if v == end: break
		
		for w in G[v]:
			vwLength = D[v] + G[v][w]
			if w in D:
				if vwLength < D[w]:
					raise ValueError
			elif w not in Q or vwLength < Q[w]:
				Q[w] = vwLength
				P[w] = v
	
	return (D,P)
			
def shortestPath(G,start,end):
	D,P = Dijkstra(G,start,end)
	Path = []
	while 1:
		Path.append(end)
		if end == start: break
		end = P[end]
	Path.reverse()
	return Path

"""
Demo Map:
Map = {"40.7 74.0": {"41.0 73.0": 1, "40.2 75.1": 1},
	"41.0 73.0": {"41.5 73.75": 1, "40.2 75.1": 1},
	"41.5 73.75": {"40.5 74.0": 1},
	"40.2 75.1": {"41.0 73.0": 1, "41.5 73.75": 1, "40.5 74.0": 1},
	"40.5 74.0": {"40.7 74.0": 1, "41.5 73.75": 1}}
"""
