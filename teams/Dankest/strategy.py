import random
import itertools

import util
import game
import capture
import pacman

import agents
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

class Negamax(Strategy):
    """
    Computes the move by traversing the tree of states using negamax. This
    algorithm is equivalent to minimax, but it is easier to implement and also
    has a cool name. It uses the internal strategy to compute the heuristic.
    """
    def __init__(self, nested, depth=3):
        self.nested = nested
        self.depth = depth
        print self.depth
        print nested.weights

    def __call__(self, agent, gameState):
        state = capture.GameState(gameState)
        value, action = self.negamax(agent, state, self.depth)
        return action

    def negamax(self, agent, gameState, depth):
        """
        Computes minimax strategy of depth using the negamax algorithm. Note
        that the strategy used as a heuristic (self.nested) is applied to the
        agent with index (agent.index + depth) % numAgents. This is an adversary
        if depth % 2 = 1.
        """
        # Select the next agent
        nextIndex = (agent.index + 1) % gameState.getNumAgents()
        nextAgent = agent.opponents[agent.getOpponents(gameState).index(nextIndex)]
        color = 1 - 2 * (depth % 2)

        # Get the current position, as well as the estimated position if
        # the current is null. Update state for future recursions
        previous = gameState.getAgentState(agent.index).copy()
        if previous.getPosition() is None:
            estimated = agent.tracker.getBeliefDistribution(agent.index).argMax()
            conf = game.Configuration(estimated, game.Directions.STOP)
            gameState.data.agentStates[agent.index] = game.AgentState(conf, previous.isPacman)

        # Instead of performing negamax here, we perform a probablistic
        # computation. We know the move distribution that we will make here, and
        # as a result, we calculate the weighted average of the moves
        moves = util.Counter()
        for a in gameState.getLegalActions(agent.index):
            if depth == 0 or gameState.isOver():
                val = self.nested.evaluate(agent, gameState, a)
                moves[a] = val * color
            else:
                # TODO we can use alphabeta pruning to speed this up
                nextState = self.getSuccessor(agent, gameState, a)
                val, _ = self.negamax(nextAgent, nextState, depth-1)
                moves[a] = -val
 
        # Now we compute the maximum scoring move as well as its score and
        # return. We could attempt to enrich this process using some sort of
        # expectimax.
        if depth == self.depth:
            print moves

        gameState.data.agentStates[agent.index] = previous
        return max((y, x) for x, y in moves.items())

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
        return getattr(self, 'weights', {})

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
    # TODO Put contest weights here
    #weights = { 'score': 1.0 }
    #weights = {'foodDownPath': 10.0, 'agentFoodDistance':-5.015006944353908,'disperse':0.5162611055588896,'dontStop':-5145.807103151626,'feasts':-55.047115581965,'ghostDistance':44.353568516626716,'ghostFoodDistance':2.078121539302075,'pacmanDistance':-3.637956876253101,'score':494.8849755629843}
    #weights = {'agentFoodDistance':-6.13169281403951,'disperse':0.1240816945605375,'dontStop':-6174.556841352691,'feasts':-111.18597121422329,'ghostDistance':30.351904504468266,'ghostFoodDistance':1.9795279153381418,'pacmanDistance':-3.645269951232489,'score':675.9370914804919}
    #weights = {'agentFoodDistance':-8.756799781566395,'disperse':0.9092189572995799,'dontStop':-4290.845244111005,'feasts':-125.37448448921515,'ghostDistance':50.23547135970318,'ghostFoodDistance':2.2988748771699736,'pacmanDistance':-3.7381303735807796,'score':783.0366308982319}
    #weights = {'agentFoodDistance':-8.904444886696977,'disperse':1.0414696906450795,'dontStop':-12127.277953518435,'feasts':-1034.1865040893524,'ghostDistance':50.97918744737279,'ghostFoodDistance':1.651378442379878,'pacmanDistance':-29.26105612777171,'score':279.96989732367535}
    weights = {'agentFoodDistance':-8.651098674855401,'disperse':3.8585068188055973,'dontStop':-10408.254388542864,'feasts':-779.536674122668,'foodDownPath':20.046386707133124,'ghostDistance':53.837701018501875,'ghostFoodDistance':2.5451881318320226,'pacmanDistance':-7.876099711872573,'score':217.31636026497412}
    

    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)

        # The features that Offensive strategy considers
        feature.score(agent, successor, features)
        feature.ghostDistance(agent, successor, features)
        #feature.
        feature.bestFoodDistance(agent, successor, features)
        feature.disperse(agent, successor, features)
        feature.feasts(agent, successor, features)
        feature.foodDownPath(agent, gameState, successor, features)

        if action == 'Stop':
            features['dontStop'] = 1.0

        # Return feature dictionary
        return features

class Defensive(Feature):
    # TODO Put contest weights here
    #weights = { 'score': 1.0 }
    weights = {'pacmanDistance': -50.0, 'onDefense': 100.0, 'disperse': 0.0, 'dontReverse': -8.0, 'dontStop': -100, 'feasts': 0.0}

    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)

        # The features that Defensive strategy considers
        feature.pacmanDistance(agent, successor, features)
        feature.ourFoodDistances(agent, successor, features)
        feature.onDefense(agent, successor, features)
        feature.disperse(agent, successor, features)
        feature.feasts(agent, successor, features)
        feature.invaderDistance(agent, successor, features)

        # Features specifically concerning moves
        state = gameState.getAgentState(agent.index)
        rev = game.Directions.REVERSE[state.configuration.direction]
        if action == game.Directions.STOP: features['stop'] = 1.0
        if action == rev: features['reverse'] = 1.0

        # Return feature dictionary
        return features


class BaselineOffensive(Feature):
    # Similarly, these are just defaults
    weights = {'successorScore': 100, 'distanceToFood': -1}
    
    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)
        feature.score(agent, successor, features)
        feature.foodDistance(agent, successor, features)
        return features

class BaselineDefensive(Feature):
    # These too
    weights = {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}

    def getFeatures(self, agent, gameState, action):
        features = util.Counter()
        successor = Strategy.getSuccessor(agent, gameState, action)

        feature.onDefense(agent, gameState, features)
        feature.invaderDistance(agent, gameState, features)

        # Features specifically concerning moves
        state = gameState.getAgentState(agent.index)
        rev = game.Directions.REVERSE[state.configuration.direction]
        if action == game.Directions.STOP: features['stop'] = 1.0
        if action == rev: features['reverse'] = 1.0

        return features

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

