import random
import itertools

import util
import game

import board
import tracking
import feature

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

class Adaptive(Feature):
    """
    Calculates a linear combination of features, and then based on the output
    chooses which of two strategies to use. This is useful especially for
    modelling the enemy ghosts, but might also be useful for our own agents at
    some point.
    """
    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __call__(self, agent, gameState):
        # TODO using the action stop is a little hacky, but is necessary to get
        # the current state to be evaluated. Fix?
        current = self.evaluate(agent, gameState, 'Stop')
        if current < 0:
            return self.first(agent, gameState)
        else:
            return self.second(agent, gameState)


class Offensive(Feature):
    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)

        # The features that Offensive strategy considers
        feature.score(agent, successor, features)
        feature.ghostDistance(agent, successor, features)
        #feature.
        feature.bestFoodDistance(agent, successor, features)
        feature.disperse(agent, successor, features)

        if action == 'Stop':
            features['dontStop'] = 1.0

        # Return feature dictionary
        #print action, features * self.getWeights(agent, gameState, action), features
        return features

    def getWeights(self, agent, gameState, action):
        "The weights for the agent"

        # TODO can we learn these efficiently somehow? They are kind of arbitrary
        return {'score': 300.0,
                'ghostDistance': 50.0,
                #'pacmanDistance': -10.0,
                'disperse': 4.0,
                'agentFoodDistance': -5.0,
                'ghostFoodDistance': 4.0,
                'dontStop': -10000000.0}

class Defensive(Feature):
    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)

        # The features that Defensive strategy considers
        feature.pacmanDistance(agent, successor, features)
        feature.onDefense(agent, successor, features)
        feature.disperse(agent, successor, features)
        #feature.randomValue(agent, successor, features)

        if action == 'Stop':
            features['dontStop'] = 1.0

        rev = game.Directions.REVERSE[
                gameState.getAgentState(agent.index).configuration.direction]
        if action == rev:
            features['dontReverse'] = 1.0


        # Return feature dictionary
        #print action, features * self.getWeights(agent, gameState, action), features
        return features


    def getWeights(self, agent, gameState, action):
        return {'pacmanDistance': -50.0,
                'onDefense': 100.0,
                'disperse': 4.0,
                'dontReverse': -8.0,
                'dontStop': -100.0}

class BaselineOffensive(Feature):
    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)
        feature.score(agent, successor, features)
        feature.foodDistance(agent, successor, features)
        return features

    def getWeights(self, agent, gameState, action):
        return {'score': 100,
                'foodDistance' : -1}

class BaselineDefensive(Feature):
    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)

        feature.onDefense(agent, gameState, features)
        feature.invaderDistance(agent, gameState, features)

        if action == game.Directions.STOP: features['stop'] = 1
        rev = game.Directions.REVERSE[gameState.getAgentState(agent.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    def getWeights(self, agent, gameState, action):
        return {'numInvaders': -1000,
                'onDefense': 100,
                'invaderDistance': -10,
                'stop': -100,
                'reverse': -2}

class BaselineAdaptive(Adaptive):
    """
    Chooses whether to be offensive or defensive based on features related to
    the agents current position, as well as features that depend on the agents
    previous position. This can be optimized just like the other feature based
    strategies. However, we can also do supervised learning by having it
    classify the play style of one of our agents.
    """
    def __init__(self):
        # If positive, then be offensive. If negative, then be defensive
        self.first = BaselineDefensive()
        self.second = BaselineOffensive()

    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)

        # TODO Right now, we just use the agent's board location. We should probably
        # also use the agent's move history.
        feature.onDefense(agent, successor, features)
        features['bias'] = 1.0

        return features

    def getWeights(self, agent, gameState, action):
        return { 'onDefense': -1 }

