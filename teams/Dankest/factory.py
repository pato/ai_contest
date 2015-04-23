# Game
import game
import captureAgents
import ghostAgents

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
    weights = None

    def __init__(self, isRed, **args):
        captureAgents.AgentFactory.__init__(self,isRed)
        self.board = board.Board()
        self.particleFilter = tracking.ContestParticleFilter(isRed, 300)
        self.team, self.opponents = [], []
        self.init = False

        # Currently makes one ghost offensive and one defensive
        self.strategies = [getattr(strategy, v) for v in args.values()]

        # Only use weights if provided
        if Factory.weights is not None:
            self.offensiveFeatureWeights = Factory.weights
            self.defensiveFeatureWeights = Factory.weights
            strategy.Offensive.weights = self.offensiveFeatureWeights
            strategy.Defensive.weights = self.defensiveFeatureWeights
            strategy.BaselineOffensive.weights = self.offensiveFeatureWeights
            strategy.BaselineDefensive.weights = self.defensiveFeatureWeights

    def getAgent(self, index):
        "Build an agent"
        # If the weights are None, then don't display belief clouds
        agent = agents.TrackingAgent(index, self, Factory.weights is not None)
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
            current = self.strategies.pop()
            agent.setStrategy(current())



