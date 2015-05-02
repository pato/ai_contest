# Standard Library
import itertools
import ast
import re

# Game
import game
import pacman
import captureAgents
import ghostAgents
import keyboardAgents

# Team
import board
import agents
import tracking
import strategy

class Factory(captureAgents.AgentFactory):
    """
    Factory is used to create agents. At the moment, it initializes a global
    particle filter for tracking the other team, as well an array of agents
    which is used for our agents to communicate amoungst themselves.
    """
    
    """
    This variable is se by the training environment. If it is None, then we
    are not currently training.
    """
    def __init__(self, isRed, **args):
        captureAgents.AgentFactory.__init__(self,isRed)
        self.board = board.Board()
        self.particleFilter = tracking.ContestParticleFilter(isRed, 100)
        self.team, self.opponents = [], []
        self.init = False

        # By default don't debug, learn, or use negamax
        self.debug = ast.literal_eval(args.get('debug', 'False'))
        self.depth = ast.literal_eval(args.get('depth', '0'))
        
        # Get the options for the first and second agents
        fst = ast.literal_eval(re.sub("\|", ",", args.get('first','{}')))
        snd = ast.literal_eval(re.sub("\|", ",", args.get('second','{}')))
        
        fst['index'] = 0
        snd['index'] = 1
        self.options = itertools.cycle([fst, snd])
        self.defaults = ['ContestOffensive', 'ContestDefensive']
        self.strategies = []

        # Only use weights if provided
        offString = re.sub("\|", ",", args.get('offensiveWeights', '{}'))
        defString = re.sub("\|", ",", args.get('defensiveWeights', '{}'))
        print defString
        
        self.offensiveFeatureWeights = ast.literal_eval(offString)
        self.defensiveFeatureWeights = ast.literal_eval(defString)
        
        if self.offensiveFeatureWeights:
            strategy.ContestOffensive.weights = self.offensiveFeatureWeights
            strategy.BaselineOffensive.weights = self.offensiveFeatureWeights
        
        if self.defensiveFeatureWeights:
            strategy.ContestDefensive.weights = self.defensiveFeatureWeights
            strategy.BaselineDefensive.weights = self.defensiveFeatureWeights

    def getAgent(self, index):
        print index
        "Build an agent"
        opt = self.options.next()
        idx = opt['index']
        lrn = getattr(strategy, opt.get('learn', ''), None)
        stt = opt.get('strategy', self.defaults[idx % 2])
        self.strategies.append(stt)
        
        # Build the agent
        if stt in ['keys', 'Keys', 'keyboard', 'Keyboard']:
            agent = agents.KeyboardAgent(index, self, self.debug)
        else:
            agent = agents.TrackingAgent(index, self, self.debug)
        
        # Wrap in a learning agent otherwise
        if lrn:
            agent = agents.LearningAgent(agent, lrn())
        
        # Record agent
        self.team.append(agent)
        return agent

    def initializeShared(self, gameState, agent):
        "Initializes the shared data structured for the agents"
        if not self.init:
            # Build the board and main particle filter
            self.init = True
            self.board.initialize(gameState)
            self.particleFilter.initialize(gameState, self.board.getLegal())

            # Build the ghosts and add to particle filter
            oppIndex = agent.getOpponents(gameState)
            for g in oppIndex:
                ghost = agents.StrategicGhost(g, self, 0.5)
                ghost.registerInitialState(gameState)
                ghost.strategy = strategy.Random()
                ghost.tracker = tracking.GhostTracker(
                        self.particleFilter, gameState, ghost)
                self.opponents.append(ghost)
                self.particleFilter.addGhostAgent(ghost)

        # Create the marginal particle filter for the agent
        agent.tracker = tracking.Tracker(
                self.particleFilter, gameState, agent)

        # Set the agent's strategy.
        if agent.index in map(lambda x: x.index, self.team):
            # Build strategy
            current = getattr(strategy, self.strategies.pop(), strategy.ContestOffensive)
            current = current()
            
            # If we want look ahead, then wrap the strategy in a negamax
            if self.depth:
                current = strategy.Negamax(current, self.depth)
            
            # Set the agent's strategy
            agent.strategy = current



