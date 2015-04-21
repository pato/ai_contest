import random

import util
import itertools

"""
These functions are useful for calculating the distances of pacman and ghosts to
food. These can then be used to calculate for example, closest food, closest
ghost, etc.
"""
def getFoodDistances(agent, successor, position):
    food = agent.getFood(successor).asList()
    #position = successor.getAgentPosition(agent.index)
    return list(agent.getMazeDistance(position, f) for f in food)

def getGhostDistances(agent, successor):
    ghosts = [ g.argMax() for g in agent.tracker.getBeliefIterable() ]
    position = successor.getAgentPosition(agent.index)
    return list(agent.getMazeDistance(position, g) for g in
            itertools.ifilter(lambda p: agent.otherSide(successor, p), ghosts))

def getPacmanDistances(agent, successor):
    ghosts = [ g.argMax() for g in agent.tracker.getBeliefIterable() ]
    position = successor.getAgentPosition(agent.index)
    return list(agent.getMazeDistance(position, g) for g in
            itertools.ifilter(lambda p: agent.ourSide(successor, p), ghosts))

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
    features['foodDistance'] = min(getFoodDistances(agent,
        successor, successor.getAgentPosition(agent.index)))
    return features

def ghostDistance(agent, successor, features=util.Counter()):
    "Calculates the distance to the closest ghost"
    dists = getGhostDistances(agent, successor)
    closestGhost = min(dists) if dists else 0.0
    closestGhost = 1.0 / closestGhost if closestGhost else 0.0

    # The ghost distance only really makes sense if our agent is on the ghost's
    # side. So, we return 0 if this is not true
    features['ghostDistance'] = closestGhost
    return features

def pacmanDistance(agent, successor, features=util.Counter()):
    "Calculates the distance to the closest pacman"
    dists = getPacmanDistances(agent, successor)
    closestPacman = min(dists) if dists else 0.0
    #closestPacman = 1.0 / closestPacman if closestPacman else 0.0

    # Similarly only really makes sense if our agent is can capture the pacman.
    features['pacmanDistance'] = closestPacman
    return features

def bestFoodDistance(agent, successor, features=util.Counter()):
    """
    Instead of considering the food and and ghost distances in isolation, we
    consider the distance of the pacman to the closest food and the distance of
    the ghost to that food.
    """
    ghosts = [ g.argMax() for g in agent.tracker.getBeliefIterable() ]

    # Get the distances to each of the food for the agent and the ghosts
    agentDistances = getFoodDistances(agent, successor,
            successor.getAgentPosition(agent.index))
    ghostDistances = [ getFoodDistances(agent, successor, g) for g in ghosts ]

    # Find the ghost that is closest
    closestGhostDistances = map(min, zip(*ghostDistances))

    # We now want to find the food that
    bestFood = min(zip(agentDistances, closestGhostDistances),
            key=lambda (a,g): a-g)

    # Return the best food
    features['agentFoodDistance'] = bestFood[0]
    features['ghostFoodDistance'] = bestFood[1]
    return features

def disperse(agent, successor, features=util.Counter()):
    """
    We want the agents to disperse. This way it is more difficult to capture
    them. However, this should not prevent them, for example, from eating food.
    """
    myPos = successor.getAgentPosition(agent.index)
    positions = (successor.getAgentPosition(a) for a in agent.getTeam(successor))
    features['disperse'] = sum(agent.getMazeDistance(myPos, p) for p in positions)
    return features

def onDefense(agent, successor, features=util.Counter()):
    """
    For defensive agents we want to remain on our side. If the agent is on our
    side, return 1.0 otherwise -1.0
    """
    features['onDefense'] = 2*agent.ourSide(successor) - 1.0
    return features

def randomValue(agent, successor, features=util.Counter()):
    """
    Returns a random value. Used to make the agent move randomly. Not sure if
    this is actually a good idea.
    """
    features['random'] = random.random()
    return features

def invaderDistance(agent, successor, features=util.Counter()):
    """
    Computes the number of invaders, as well as the distance to the closest
    invader. This is useful for simulating the baseline defensive agent. Note,
    it does not use estimated distances.
    """
    enemies = [successor.getAgentState(i) for i in agent.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = [agent.getMazeDistance(successor.getAgentPosition(agent.index),
          a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
    return features

