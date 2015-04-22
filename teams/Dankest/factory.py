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
    def __init__(self, isRed, **args):
        captureAgents.AgentFactory.__init__(self,isRed)
        self.board = board.Board()
        self.particleFilter = tracking.ContestParticleFilter(isRed, 300)
        self.team, self.opponents = [], []
        self.init = False

        # Allow for more robust configurations, or configurations that scale
        # better? i.e. Instead of specifying individual agents, specify
        # something like strategy.Balanced, Aggressive, etc.?
        self.strategies = [getattr(strategy, v) for v in args.values()]
        self.ghostStrategies = [ strategy.BaselineAdaptive,
                strategy.BaselineAdaptive ]

    def getAgent(self, index):
        "Currently builds a BasicAgent"
        # Make the agent
        agent = agents.TrackingAgent(index, self)
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
                ghost.strategy = self.ghostStrategies.pop()()
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