def allSame(list):
    return sum([x == list[0] for x in list]) == len(list)
def directionCount(list):
    return [list.count("Positive"), list.count("Negative"), list.count("Neutral")]

def correlationCoefficient(x, y):
    mux = sum(x)/float(len(x))
    muy = sum(y)/float(len(y))
    covariance = sum([(i-mux)*(j-muy) for i,j in zip(x,y)])/float(len(x)-1)
    sigmax = (sum([(i-mux)**2 for i in x])/float(len(x)-1))**0.5
    sigmay = (sum([(i-muy)**2 for i in y])/float(len(y)-1))**0.5
    return covariance/(sigmax*sigmay)
    
def getUpdateFactor(directions, selection, Mib):
    '''Input - 'directions' list: ['Positive', 'Positive', 'Negative', 'Negative', 'Negative']'''
    '''selection denotes which among the k(=5) above was selected by the user'''
    '''Mib is True if the attriibute which is calling this function is an Mib attribute, false otherwise'''
    '''Refer to the document weightUpdates.xslx for the detailed table on weight updates'''
    if allSame(directions):
        return 1
    if directions[selection] == 'Neutral':
        return 1
    diff = directions.count('Positive') - directions.count('Negative')
    if Mib == True:
        index = 1 if directions[selection] == 'Positive' else 0
    if Mib == False:
        index = 0 if directions[selection] == 'Positive' else 1
    
    if diff == 3:
        temp = (1.0/2, 8)*Mib + (2,1.0/8)*(1-Mib)
    if diff == 1:
        temp = (1.0/2, 3)*Mib + (2,1.0/3)*(1-Mib)
    if diff == -1:
        temp = (1.0/3, 2)*Mib + (3,1.0/2)*(1-Mib)
    if diff == -3:
        temp = (1.0/8, 2)*Mib + (8,1.0/2)*(1-Mib)
    
    return temp[index]