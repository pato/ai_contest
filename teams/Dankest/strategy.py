import random
import itertools

import util
import game

import board
import tracking

class Strategy:
    """
    A strategy is the brain of an agent. It is initialized with a board, and
    given a game state, it chooses an action. Strategies exist primarily to
    simplify testing out new ideas without duplicating the edge cases.
    """
    def getSuccessor(agent, action):
        return game.Actions.getSuccessor(agent.position, action)
    getSuccessor = staticmethod(getSuccessor)

    def getSuccessor(agent, gameState, action):
        """
        Finds the next successor which is a grid position (location
        tuple).
        """
        successor = gameState.generateSuccessor(agent.index, action)
        pos = successor.getAgentState(agent.index).getPosition()
        if pos != util.nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generateSuccessor(agent.index, action)
        else:
            return successor
    getSuccessor = staticmethod(getSuccessor)

    def getPossibleActions(agent, gameState):
        "Get the possible actions from the current state"
        return gameState.getLegalActions(agent.index)
    getPossibleActions = staticmethod(getPossibleActions)

    def getPossiblePositions(agent, gameState):
        "Get the possible successor states"
        return [ game.Actions.getSuccessor(agent.position, a) for a in
                Strategy.getPossibleActions(agent, gameState) ]
    getPossiblePositions = staticmethod(getPossiblePositions)

    def getTransitions(agent, gameState):
        "Creates pairs of (action, result)"
        return zip(Strategy.getPossibleActions(agent, gameState),
                Strategy.getPossibleSuccessors(agent, gameState))
    getTransitions = staticmethod(getTransitions)

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
        return random.choice(Strategy.getPossibleActions(agent, gameState))

class Feature(Strategy):
    """
    Maximizes a linear combination of features in order to select the best
    action. Chooses randomly among equally weighted actions.
    """

    def getFeatures(self, agent, gameState, action):
        """
        Returns a counter of features for state. Taken from BaselineAgents
        """
        util.raiseNotDefined()

    def getWeights(self, agent, gameState, action):
        """
        Returns the weights for each of the features. These can potentially be
        learned.
        """
        util.raiseNotDefined()

    def evaluate(self, agent, gameState, action):
        features = self.getFeatures(agent, gameState, action)
        weights = self.getWeights(agent, gameState, action)
        return features * weights

    def __call__(self, agent, gameState):
        actions = Strategy.getPossibleActions(agent, gameState)
        values = [self.evaluate(agent, gameState, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
        return random.choice(bestActions)

"""
For many possible features such as food distance, ghost distance, etc. the
feature can be objectively determined from the gameState and agent. Many of
these features are also used in many different agents. Therefore, they are
implemented as functions that can be used inside other strategies.
"""

def score(agent, successor, features=util.Counter()):
    "Calculates the score"
    features['score'] = agent.getScore(successor)
    return features

def foodDistance(agent, successor, features=util.Counter()):
    "Calculates the distance to the closest food"
    food = agent.getFood(successor).asList()
    position = successor.getAgentPosition(agent.index)
    closestFood = min(agent.getMazeDistance(position, f) for f in food)
    features['foodDistance'] = closestFood
    return features

def ghostDistance(agent, successor, features=util.Counter()):
    "Calculates the distance to the closest ghost"
    ghosts = [ g.argMax() for g in agent.tracker.getBeliefIterable() ]
    position = successor.getAgentPosition(agent.index)
    dists = list(agent.getMazeDistance(position, g) for g in
            itertools.ifilter(lambda p: agent.otherSide(successor, p), ghosts))
    closestGhost = min(dists) if dists else 0.0

    # The ghost distance only really makes sense if our agent is on the ghost's
    # side. So, we return 0 if this is not true
    features['ghostDistance'] = closestGhost * agent.otherSide(successor)
    return features

def pacmanDistance(agent, successor, features=util.Counter()):
    "Calculates the distance to the closest pacman"
    ghosts = [ g.argMax() for g in agent.tracker.getBeliefIterable() ]
    position = successor.getAgentPosition(agent.index)
    dists = list(agent.getMazeDistance(position, g) for g in
            itertools.ifilter(lambda p: agent.ourSide(successor, p), ghosts))
    closestPacman = min(dists) if dists else 0.0

    # Similarly only really makes sense if our agent is can capture the pacman.
    features['pacmanDistance'] = closestPacman * agent.ourSide(successor,position)
    return features

class Offensive(Feature):
    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)

        # The features that Offensive strategy considers
        score(agent, successor, features)
        foodDistance(agent, successor, features)
        ghostDistance(agent, successor, features)

        # Return feature dictionary
        print action, features * self.getWeights(agent, gameState, action), features
        return features

    def getWeights(self, agent, gameState, action):
        "foodDistance is the only feature"
        return { 'score': 100.0,
                 'foodDistance': -1.0,
                 'ghostDistance': 1.0 }
