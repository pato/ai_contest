import random
import itertools

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
        # Update the current position and beliefs
        self.position = gameState.getAgentPosition(self.index)
        self.tracker.observe(gameState)

        # Select an action and update position
        action = self.strategy(self, gameState)
        self.position = game.Actions.getSuccessor(self.position,action)

        # Write distributions to board for debugging
        if self.debug:
            self.displayBeliefs(gameState)

        return action

    def setStrategy(self, strat):
        "Changes the current strategy. Allows for an agent to adapt to the game"
        self.strategy = strat

    def ourSide(self, gameState, position=None):
        if position == None:
            position = self.position

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
