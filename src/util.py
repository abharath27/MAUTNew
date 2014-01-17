def allSame(list):
    return sum([x == list[0] for x in list]) == len(list)
def directionCount(list):
    return [list.count("Positive"), list.count("Negative"), list.count("Neutral")]