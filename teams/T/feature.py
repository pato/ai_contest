import random

import util
import itertools
import game

"""
These functions are useful for calculating the distances of pacman and ghosts to
food. These can then be used to calculate for example, closest food, closest
ghost, etc.
"""
def getFoodDistances(agent, successor, position):
    food = agent.getFood(successor).asList()
    return [agent.getMazeDistance(position, f) for f in food]

def getOurFoodDistances(agent, successor, position):
    ourFood = agent.getFood(successor).asList()
    return [agent.getMazeDistance(position, f) for f in ourFood]

def getGhostDistances(agent, successor, position):
    ghosts = (g.argMax() for g in agent.tracker.getBeliefIterable())
    ghosts = (g for g in ghosts if agent.otherSide(successor, g))
    return [agent.getMazeDistance(position, g) for g in ghosts]

def getPacmanDistances(agent, successor, position):
    ghosts = (g.argMax() for g in agent.tracker.getBeliefIterable())
    ghosts = (g for g in ghosts if agent.ourSide(successor, g))
    return [agent.getMazeDistance(position, g) for g in ghosts]

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

def foodDownPath(agent, predecessor, successor, features=util.Counter()):
    """
    Number of food pellets down the path of the successor
    up to a given maze distance
    """
    maxSteps = 5
    oldpos = predecessor.getAgentPosition(agent.index)
    newpos = successor.getAgentPosition(agent.index)
    food = agent.getFood(successor).asList()
    walls = successor.getWalls()
    wallList = walls.asList()


    visited = {oldpos}
    queue = util.Queue() 
    queue.push(newpos)
    foodCount = 0

    legalNeighbors = lambda pos: game.Actions.getLegalNeighbors(pos, walls)
    goodNeighbor = lambda pos: pos not in visited and agent.getMazeDistance(newpos, pos) < maxSteps

    while not queue.isEmpty():
        pos = queue.pop()
        if pos not in visited:
            visited.add(pos)
            if pos in food:
                foodCount += 1
            for neighbor in legalNeighbors(pos):
                if goodNeighbor(neighbor):
                    queue.push(neighbor)
    
    features['foodDownPath'] = foodCount

    return features

def foodDistance(agent, successor, features=util.Counter()):
    "Calculates the distance to the closest food"
    position = successor.getAgentPosition(agent.index)
    features['foodDistance'] = min(getFoodDistances(agent, successor, position))
    return features

def ourFoodDistances(agent, successor, features=util.Counter()):
    "The sum of the distances to our food"
    position = successor.getAgentPosition(agent.index)
    features['ourFoodDistances'] = sum(getOurFoodDistances(agent,successor,position))
    return features

def ghostDistance(agent, successor, features=util.Counter()):
    "Calculates the distance to the closest ghost"
    position = successor.getAgentPosition(agent.index)
    dists = getGhostDistances(agent, successor, position)
    closestGhost = min(dists) if dists else 0.0
    closestGhost = 1.0 / closestGhost if closestGhost else 0.0

    features['ghostDistance'] = closestGhost
    return features

def pacmanDistance(agent, successor, features=util.Counter()):
    "Calculates the distance to the closest pacman"
    position = successor.getAgentPosition(agent.index)
    dists = getPacmanDistances(agent, successor, position)
    closestPacman = min(dists) if dists else 0.0

    features['pacmanDistance'] = closestPacman
    return features

def bestFoodDistance(agent, successor, features=util.Counter()):
    """
    Instead of considering the food and and ghost distances in isolation, we
    consider the distance of the pacman to the closest food and the distance of
    the ghost to that food.
    """
    ghosts = (g.argMax() for g in agent.tracker.getBeliefIterable())
    position = successor.getAgentPosition(agent.index)

    # Get the distances to each of the food for the agent and the ghosts
    agentDistances = getFoodDistances(agent, successor, position)
    ghostDistances = [getFoodDistances(agent, successor, g) for g in ghosts]

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
    position = successor.getAgentPosition(agent.index)
    team = (successor.getAgentPosition(a) for a in agent.getTeam(successor))
    features['disperse'] = sum(agent.getMazeDistance(position, p) for p in team)
    return features

def feasts(agent, successor, features=util.Counter()):
    """
    Number of pill groups greater than 2
    O(n^2) but can definitely be faster
    """
    foods = agent.getFood(successor).asList()
    feastsFound = []
    feasts = 0
    for food in foods:
        distances = list(agent.getMazeDistance(food, f) for f in foods)
        feastFoods = [foods[i] for i, dist in enumerate(distances) if dist <= 1]
        if len(feastFoods) > 1:
            feastsFound.extend(feastFoods)
            for f in feastFoods: foods.remove(f)
            feasts += 1 
    features['feasts'] = feasts
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

