import util
import game
import random
import itertools

# TODO: recognize board substructures

class Board:
    """
    Represents elaborations to the structure and functions defined over the
    traditional GameState board related functions. For example, rather than use
    the maze distance computation, which runs djikstra's over the board for all
    pairs, O(n^4), this runs Floyd-Warshall to compute shortest paths, O(n^3),
    which will allow for more preprocessing time.
    """
    def __init__(self, gameState=None):
        if gameState is not None:
            self.initialize(gameState)

    def initialize(self, gameState):
        self.walls = gameState.getWalls()
        self.initLegal()
        self.initDeadEnd()
        #self.initAdjacency()
        #self.initFloydWarshall()

    def initLegal(self):
        self.legal = self.walls.asList(False)
        self.legalReverse = dict(map(lambda (x,y): (y,x), enumerate(self.legal)))
        self.legalRange = range(len(self.legal))

    def initAdjacency(self):
        "Create the adjaceny matrix"
        lr = self.legalRange
        self.adj = [ [ self.areAdjacent(self.legal[x],self.legal[y]) for y in lr ]
                for x in lr ]

    def initFloydWarshall(self):
        """
        Given a maze, an orientation of walls, find the shortest path between
        any two vertices. This runs in O(n^3) where n is the number of vertices.
        """
        lr = self.legalRange
        self.dist = [ [0] * len(self.legal) for _ in lr ]
        self.dist = [ [ min(self.dist[i][j], self.dist[i][k] + self.dist[k][j])
            for i in lr ] for k,j in itertools.product(lr,lr) ]

    def initDeadEnd(self):
        """
        Given the walls, we find all the states that have no cross edges. That
        is, all the locations that are part of a dead end cannot be escaped if
        one is being persued by a ghost.

        To do this, we compute tarjan's algorithm and find all the nodes that
        are part of a strongly connected component of size 1. This will reveal
        all the nodes which can only be escaped in one way.
        """
        # Starting values
        self.current = 0
        stack,self.components,self.deadends = [],[],set()
        index,lowlink = {},{}
        identified = set()


        # Used to calculate the strongly connected components
        def strongconnect(v):
            # Init state
            index[v] = self.current
            lowlink[v] = self.current
            self.current += 1
            stack.append(v)

            # For each edge
            for w in self.getLegalNeighbors(v):
                if w not in index:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in identified:
                    lowlink[v] = min(lowlink[v], index[w])

            # Record the connected component if found
            if lowlink[v] == index[v]:
                scc = set(stack[index[v]:])
                del stack[index[v]:]
                identified.update(scc)
                if len(scc) != 0:
                    self.components.append(scc)
                if len(scc) == 1:
                    self.deadends.add(min(scc))

            # Used to thread state (grrr...)
            return self.current

        # For each vertex
        for v in self.legal:
            if v not in index:
                strongconnect(v)
        
#        print self.components
#        print self.deadends
    
    def areAdjacent(self, p, q):
        "Tests if two different points are adjacent"
        a,b = abs(p[0]-q[0]),abs(p[1]-q[1])
        return all((p != q, a <= 1, b <= 1))

    def getLegal(self):
        return self.legal

    def getLegalActions(self, position):
        act = ['North','South','East','West','Stop']
        adj = game.Actions.getLegalNeighbors(position, self.walls)
        return [x for x in act if game.Actions.getSuccessor(position, x) in adj]

    def getLegalNeighbors(self, position):
        return game.Actions.getLegalNeighbors(position, self.walls)

    def isDeadEnd(self, position):
        "Checks if position is dead end"
        return position in self.deadends

    def getDistance(self, p, q):
        "Compute the vertex index, and then distance"
        return self.dist[self.legalReverse[p]][self.legalReverse[q]]
