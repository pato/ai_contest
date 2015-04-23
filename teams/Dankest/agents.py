import random
import itertools
import time

import util
import game
import captureAgents

import board
import tracking
import strategy

class TrackingAgent(captureAgents.CaptureAgent):
    """
    This is the 'basic' agent. It implements tracking and intefaces with the
    factory, which supplies shared data structures like the board and other
    agents.
    """
    def __init__(self, index, factory, debug=True):
        captureAgents.CaptureAgent.__init__(self, index)
        self.factory = factory
        self.team = factory.team
        self.opponents = factory.opponents
        self.board = factory.board
        self.debug = debug

    def registerInitialState(self, gameState):
        "Initializes both local and shared data structures"
        captureAgents.CaptureAgent.registerInitialState(self, gameState)
        self.position = gameState.getInitialAgentPosition(self.index)
        self.factory.initializeShared(gameState,self)

    def chooseAction(self, gameState):
        "Updates belief distributions and calls a 'strategy'"
        if self.debug:
            start = time.time()

        # Update the current position and beliefs
        self.position = gameState.getAgentPosition(self.index)
        self.tracker.observe(gameState)

        # Select an action and update position
        action = self.strategy(self, gameState)
        self.position = game.Actions.getSuccessor(self.position,action)

        # Write distributions to board for debugging and time
        if self.debug:
            if not isinstance(self, StrategicGhost):
                print 'eval time for agent %d: %.4f' % (self.index, time.time()-start)
            self.displayBeliefs(gameState)

        return action

    def setStrategy(self, strategy):
        "Changes the current strategy. Allows for an agent to adapt to the game"
        self.strategy = strategy

    def getPosition(self):
        return self.position

    def getIndex(self):
        return self.index

    def ourSide(self, gameState, position=None):
        "Tests if a position is on our side"
        if position is None:
            position = gameState.getAgentPosition(self.index)

        width = self.board.walls.width
        midPoint = width / 2
        side = range(midPoint) if self.red else range(midPoint, width)
        return position[0] in side

    def otherSide(self, gameState, position=None):
        return not self.ourSide(gameState, position)

    def displayBeliefs(self, gameState):
            "Prints the belief distributions to the screen"
            dists = [None] * gameState.getNumAgents()
            for i,a in enumerate(self.getTeam(gameState)):
                # For our team, just lookup the locations
                dists[a] = util.Counter()
                dists[a][self.team[i].position] = 1.0
            for a in self.getOpponents(gameState):
                dists[a] = self.tracker.getBeliefDistribution(a)
            self.displayDistributionsOverPositions(dists)

class StrategicGhost(TrackingAgent):
    """
    In order to simulate opponents, we need to have some idea of how they move.
    Therefore, instead of rewriting AI's, we can use our prebuilt strategies to
    simulate the opponents.
    """
    def __init__(self, index, factory, prob=0.8, debug=True):
        TrackingAgent.__init__(self, index, factory, debug=False)
        self.team = factory.opponents
        self.opponents = factory.team
        self.prob = float(prob)

    def getPosition():
        # So, this is somewhat convoluted, but here is why this works:
        #
        # The only time this is called is inside of a call to a strategy, which
        # must occur inside of a call to self.chooseAction, which must occur
        # inside of self.getDistribution. The getDistribution function is called
        # *only* inside of the tracker, in particular elapseTime. This function
        # sets the agents position first. All other calls to the opponents
        # position are made via the belief distribution provided by the tracker.

        return self.gameState.getPosition(self.index)

    def getDistribution(self, gameState):
        """
        Uses the regular agent to select the movement, and then engages that
        movement with probability self.prob. Other movements are uniformly
        selected from the remaining probability.
        """
        action = self.chooseAction(gameState)
        legal = gameState.getLegalActions(self.index)
        p = (1.0 - self.prob) / (len(legal) - 1.0)

        # Return distribution over legal actions
        return util.Counter({a: p if a != action else self.prob for a in legal})
