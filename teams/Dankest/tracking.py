from itertools import *
import util
import random
# import busters
import operator

import game
import capture

# Replaces busters
def getEmissionModel(gameState, noisy):
    "Used to calculate P(noisy | true)"
    return lambda true: gameState.getDistanceProb(true, noisy)

class Tracker:
    """
    Used to interact with the actual contest particle filter. Basically
    represents the filter for a single ghost. Useful primarily for calculating
    the marginal distribution.
    """
    def __init__(self, particleFilter, gameState, agent):
        # Set agent and particle filter
        self.agent = agent
        self.index = agent.index
        self.particleFilter = particleFilter
        self.opponents = self.agent.getOpponents(gameState)

        # Calculate the opponent who goes before the agent
        gi = (self.index - 1) % gameState.getNumAgents()
        self.ghostIndex = self.opponents.index(gi)

    def observeState(self, gameState):
        "Gets the noisy distances to ghosts, and updates particle filter"
        noisy = [ d for i,d in enumerate(gameState.getAgentDistances()) if
                i in self.opponents ]
        self.particleFilter.observeState(gameState, self.agent.position, noisy)

    def elapseTime(self, gameState):
        "Elapses time for the previous ghost"
        self.particleFilter.elapseTime(capture.GameState(gameState), self.ghostIndex)

    def observe(self, gameState):
        "Observes, and elapses time for the current pacman"
        self.elapseTime(gameState)
        self.observeState(gameState)

    def getBeliefDistribution(self, ghost):
        "Returns the marginal belief over a particular ghost by summing out the others."
        jointDistribution = self.particleFilter.getBeliefDistribution()
        dist = util.Counter()
        for t, prob in jointDistribution.items():
            dist[t[self.opponents.index(ghost)]] += prob
        return dist

    def getBeliefIterable(self):
        "Returns an iterable of belief distributions for the adversaries"
        return (self.getBeliefDistribution(i) for i in self.opponents)

class GhostTracker(Tracker):
    """
    This is a tracker for use by the ghost agents, *not* for tracking the
    ghosts. This is an important distinction. It does not record observations,
    and is necessary for interfacing with strategies.
    """
    def observe(self, gameState):
        self.gameState = gameState
    
    def getBeliefDistribution(self, ghost):
        "Will only ever be queried for the agents"
        dist = util.Counter()
        dist[self.gameState.getAgentPosition(ghost)] = 1.0
        return dist

class ContestParticleFilter:
    """
    ContestParticleFilter allows for a single ghost to be updated in elapseTime
    function, while still incorporating the observations of *all* of our agents.
    Therefore, on each turn, we have a larger body of evidence to use. Also
    supports using conditionally dependent ghost distributions like
    JointParticleFilter.
    """

    def __init__(self, isRed, numParticles=600):
        self.isRed = isRed
        self.setNumParticles(numParticles)

    def setNumParticles(self, numParticles):
        self.numParticles = numParticles

    def initialize(self, gameState, legalPositions):
        "Stores information about the game, then initializes particles."
        self.numGhosts = gameState.getNumAgents() / 2
        self.ghostAgents = []
        
        # Sets the ghost indices so that we can initialize the particles
        if not self.isRed:
            self.ghostIndices = gameState.getRedTeamIndices()
        else:
            self.ghostIndices = gameState.getBlueTeamIndices()
        
        self.legalPositions = legalPositions
        self.resetParticles(gameState)

        # Must call initializeParticles *after* all the ghosts are added

    def resetParticles(self, gameState, ghost=None):
        """
        This places the ghost given by ghost into its starting state. This is
        useful, for example, at the start of a match. However, I allow the ghost
        to be specified so that when a ghost is captured, it is set back to the
        starting state.
        """
        # Particle with all ghosts in start state
        if not getattr(self, 'particles', []):
            p = tuple(gameState.getInitialAgentPosition(g) for g in
                    self.ghostIndices)
            self.particles = [p] * self.numGhosts
        else:
            for p in self.particles:
                positions = list(p)
                positions[self.ghostIndices.index(ghost)] = \
                        gameState.getInitialAgentPosition(ghost)
                p = tuple(positions)

    def resampleParticles(self, gameState):
        """
        Initialize particles to be consistent with a uniform prior.

        Each particle is a tuple of ghost positions. Use self.numParticles for
        the number of particles. You may find the `itertools` package helpful.
        Specifically, you will need to think about permutations of legal ghost
        positions, with the additional understanding that ghosts may occupy the
        same space. Look at the `itertools.product` function to get an
        implementation of the Cartesian product.

        Note: If you use itertools, keep in mind that permutations are not
        returned in a random order; you must shuffle the list of permutations in
        order to ensure even placement of particles across the board. Use
        self.legalPositions to obtain a list of positions a ghost may occupy.

        Note: the variable you store your particles in must be a list; a list is
        simply a collection of unweighted variables (positions in this case).
        Storing your particles as a Counter (where there could be an associated
        weight with each position) is incorrect and may produce errors.
        """
        # Cartesian product of positions of all ghosts
        ghosts = list(product(*repeat(self.legalPositions, self.numGhosts)))
        random.shuffle(ghosts)

        # Now take the first numParticles
        self.particles = list(islice(cycle(ghosts), self.numParticles))

    def addGhostAgent(self, agent):
        """
        Each ghost agent is registered separately and stored (in case they are
        different).
        """
        self.ghostAgents.append(agent)
        self.ghostIndices.append(agent.index)

    def observeState(self, gameState, pacmanPosition, noisyDistances):

        """
        Resamples the set of particles using the likelihood of the noisy
        observations.

        To loop over the ghosts, use:

          for i in range(self.numGhosts):
            ...

        A correct implementation will handle two special cases:
          1) When a ghost is captured by Pacman, all particles should be updated
             so that the ghost appears in its prison cell, position
             self.getJailPosition(i) where `i` is the index of the ghost.

             As before, you can check if a ghost has been captured by Pacman by
             checking if it has a noisyDistance of None.

          2) When all particles receive 0 weight, they should be recreated from
             the prior distribution by calling initializeParticles. After all
             particles are generated randomly, any ghosts that are eaten (have
             noisyDistance of None) must be changed to the jail Position. This
             will involve changing each particle if a ghost has been eaten.

        self.getParticleWithGhostInJail is a helper method to edit a specific
        particle. Since we store particles as tuples, they must be converted to
        a list, edited, and then converted back to a tuple. This is a common
        operation when placing a ghost in jail.
        """
        if len(noisyDistances) < self.numGhosts:
            return
        positions = [ gameState.getAgentPosition(i) for i in self.ghostIndices ]
        emissionModels = [ getEmissionModel(gameState, dist) for dist in
                noisyDistances ]
        allPossible = util.Counter()

        for p in self.particles:
            # All ghosts that are visible, we set specifically
            p = tuple(positions[g] if positions[g] is not None else p[g]
                    for g in range(self.numGhosts))
            
            # A generator that returns probabilities for non-jailed ghosts
            gen = (emissionModels[g](util.manhattanDistance(p[g],pacmanPosition))
                    for g in range(self.numGhosts) if positions[g] == None)

            # Take the product of the ghost products and update the distribution
            prod = reduce(operator.mul, gen, 1.0)

            allPossible[p] += prod

        if not any(allPossible.values()):
            self.resampleParticles(gameState)
        else:
            allPossible.normalize()
            self.particles = [ util.sample(allPossible) for p in
                    self.particles ]

    def elapseTime(self, gameState, ghost):
        """
        Samples each particle's next state based on its current state and the
        gameState.

        To loop over the ghosts, use:

          for i in range(self.numGhosts):
            ...

        Then, assuming that `i` refers to the index of the ghost, to obtain the
        distributions over new positions for that single ghost, given the list
        (prevGhostPositions) of previous positions of ALL of the ghosts, use
        this line of code:

          newPosDist = getPositionDistributionForGhost(
             setGhostPositions(gameState, prevGhostPositions), i, self.ghostAgents[i]
          )

        Note that you may need to replace `prevGhostPositions` with the correct
        name of the variable that you have used to refer to the list of the
        previous positions of all of the ghosts, and you may need to replace `i`
        with the variable you have used to refer to the index of the ghost for
        which you are computing the new position distribution.

        As an implementation detail (with which you need not concern yourself),
        the line of code above for obtaining newPosDist makes use of two helper
        functions defined below in this file:

          1) setGhostPositions(gameState, ghostPositions)
              This method alters the gameState by placing the ghosts in the
              supplied positions.

          2) getPositionDistributionForGhost(gameState, ghostIndex, agent)
              This method uses the supplied ghost agent to determine what
              positions a ghost (ghostIndex) controlled by a particular agent
              (ghostAgent) will move to in the supplied gameState.  All ghosts
              must first be placed in the gameState using setGhostPositions
              above.

              The ghost agent you are meant to supply is
              self.ghostAgents[ghostIndex-1], but in this project all ghost
              agents are always the same.
        """
        newParticles = []
        for oldParticle in self.particles:
            # We only update one ghost in this loop now, since only one ghost
            # can move in between our turns. The ghost index is the actual
            # agent.
            newParticle = list(oldParticle)
            newPosDist = getPositionDistributionForGhost(
                    setGhostPositions(gameState, self.ghostIndices, newParticle),
                    self.ghostIndices[ghost], self.ghostAgents[ghost])
            newParticle[ghost] = util.sample(newPosDist)
            newParticles.append(tuple(newParticle))
        self.particles = newParticles

    def getBeliefDistribution(self):
        dist = util.Counter()
        for p in self.particles:
            dist[p] += 1.0
        dist.normalize()
        return dist

# One JointInference module is shared globally across instances of MarginalInference
# jointInference = JointParticleFilter()

def getPositionDistributionForGhost(gameState, ghostIndex, agent):
    """
    Returns the distribution over positions for a ghost, using the supplied
    gameState.
    """
    # index 0 is pacman, but the students think that index 0 is the first ghost.
    ghostPosition = gameState.getAgentPosition(ghostIndex)
    actionDist = agent.getDistribution(gameState)
    dist = util.Counter()
    for action, prob in actionDist.items():
        successorPosition = game.Actions.getSuccessor(ghostPosition, action)
        dist[successorPosition] = prob
    return dist

def setGhostPositions(gameState, ghostIndices, ghostPositions):
    "Sets the position of all ghosts to the values in ghostPositionTuple."
    #for index, pos in enumerate(ghostPositions):
    for index, pos in zip(ghostIndices, ghostPositions):
        conf = game.Configuration(pos, game.Directions.STOP)
        gameState.data.agentStates[index] = game.AgentState(conf, False)
    return gameState

