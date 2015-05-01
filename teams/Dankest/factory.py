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

        # Currently makes one ghost offensive and one defensive
        self.strategies = itertools.cycle([strategy.Offensive, strategy.Defensive])

        # By default don't debug, learn, or use negamax
        self.debug = ast.literal_eval(args.get('debug', 'False'))
        self.depth = ast.literal_eval(args.get('depth', '0'))
        self.keys = ast.literal_eval(args.get('keys', '[]'))

        # Specify if we should learn and what weights to begin with
        self.learn = ast.literal_eval(args.get('learn', '[]'))
        learnString = re.sub("\|", ",", args.get('learnWeights', '{}'))
        self.learnWeights = ast.literal_eval(learnString)

        # Only use weights if provided
        offString = re.sub("\|", ",", args.get('offensiveWeights', '{}'))
        defString = re.sub("\|", ",", args.get('defensiveWeights', '{}'))
        self.offensiveFeatureWeights = ast.literal_eval(offString)
        self.defensiveFeatureWeights = ast.literal_eval(defString)
        
        if self.offensiveFeatureWeights:
            strategy.Offensive.weights = self.offensiveFeatureWeights
            strategy.BaselineOffensive.weights = self.offensiveFeatureWeights
        
        if self.defensiveFeatureWeights:
            strategy.Defensive.weights = self.defensiveFeatureWeights
            strategy.BaselineDefensive.weights = self.defensiveFeatureWeights

    def getAgent(self, index):
        "Build an agent"
        # Debug if the commandline parameter is set
        if index in self.keys:
            # Do we need more checks?
            print "Keyboard Agent"
            agent = agents.KeyboardAgent(index, self, self.debug)
        else:
            print "Tracking Agent"
            agent = agents.TrackingAgent(index, self, self.debug)
        
        if index in self.learn:
            # If we are to learn, then we wrap the agent in a learning agent
            agent = agents.LearningAgent(agent, self.learnWeights, strategy.Offensive())
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
                #ghost.strategy = strategy.BaselineAdaptive()
                ghost.strategy = strategy.Random()
                ghost.tracker = tracking.GhostTracker(
                        self.particleFilter, gameState, ghost)
                self.opponents.append(ghost)
                self.particleFilter.addGhostAgent(ghost)

        # Create the marginal particle filter for the agent
        agent.tracker = tracking.Tracker(
                self.particleFilter, gameState, agent)

        # Set the agent's strategy.
        if agent.index in map(agents.TrackingAgent.getIndex, self.team):
            current = self.strategies.next()()
            if self.depth:
                # If we want look ahead, then wrap the strategy in a negamax
                current = strategy.Negamax(current, self.depth)
            agent.setStrategy(current)



