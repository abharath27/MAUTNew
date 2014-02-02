def allSame(list):
    return sum([x == list[0] for x in list]) == len(list)
def directionCount(list):
    return [list.count("Positive"), list.count("Negative"), list.count("Neutral")]

def correlationCoefficient(self, x, y):
        mux = sum(x)/float(len(x))
        muy = sum(y)/float(len(y))
        covariance = sum([(i-mux)*(j-muy) for i,j in zip(x,y)])/float(len(x)-1)
        sigmax = (sum([(i-mux)**2 for i in x])/float(len(x)-1))**0.5
        sigmay = (sum([(i-muy)**2 for i in y])/float(len(y)-1))**0.5
        return covariance/(sigmax*sigmay)