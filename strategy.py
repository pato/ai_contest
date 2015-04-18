import random
import itertools
import types

import util
import capture
import captureAgents
import ghostAgents
import pacman
import game

import board
import particleFilter

class Strategy:
    """
    A strategy is the brain of an agent. It is initialized with a board, and
    given a game state, it chooses an action. Strategies exist primarily to
    simplify testing out new ideas without duplicating the edge cases.
    """
    def getActions(self, agent, gameState):
        "Get the possible actions from the current state"
        return gameState.getLegalActions(agent.index)

    def getSuccessors(self, agent, gameState):
        "Get the possible successor states"
        return [ game.Actions.getSuccessor(agent.position, x)
                for x in self.getActions(agent, gameState) ]

    def getPairs(self, agent, gameState):
        "Creates pairs of (action, result)"
        return zip(self.getActions(agent, gameState), self.getSuccessors(agent, gameState))

    def __call__(self, agent, gameState):
        "Selects the action given a gamestate"
        return util.raiseNotDefined()

class Nothing(Strategy):
    def __call__(self, *_):
        "Useful for debugging the tracker"
        return 'Stop'

class Random(Strategy):
    def __call__(self, agent, gameState):
        "Selects a random legal action"
        return random.choice(self.getActions(agent, gameState))

class Offensive(Strategy):
    def __call__(self, agent, gameState):
        "Naively chooses a food to eat"
        food = agent.getFood(gameState).asList()
        
        # Make a distribution of food, so further food is unlikely
        foodProb = util.Counter({f: 1.0/agent.getMazeDistance(agent.position, f) for
            f in food })
        foodProb.normalize()
        dest = foodProb.argMax()
        
        # Get possible successors
        return min(self.getPairs(agent, gameState),
                key=lambda x: agent.getMazeDistance(x[1], dest))[0]
