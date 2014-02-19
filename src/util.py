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
    if Mib == True:
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

def printRanks(evaluatorInstance):
    ranks = evaluatorInstance.ranks
    modString = evaluatorInstance.domain
    if evaluatorInstance.recommender.historyEnabled == True:
        modString += 'History'
    if evaluatorInstance.recommender.diversityEnabled == True:
        modString += 'Diversity'
    if evaluatorInstance.recommender.similarProdInFirstCycleEnabled == True:
        modString += 'Similarity'
    #ranks is a dictionary. Key = iteration number, value = list of ranks of various products
    a = open('ranks' + modString + '.txt', 'w')                 #Domain and all modifications are added to the file name.
    b = open('ranksPaddedWithZeros' + modString +'.txt', 'w')
    #print ranks
    try:
        for key in ranks:
            temp1 = sum(ranks[key])/float(len(ranks[key]))
            a.write(str(key) + ' '+ str(temp1) + '\n')
            temp2 = sum(ranks[key])/float(len(ranks[1]))
            b.write(str(key) + ' '+ str(temp2) + '\n')
    except:
        print 'key =', key, 'ranks[key] =', ranks[key]

def printWeights(evaluatorInstance):
    weightList = evaluatorInstance.recommender.weightsList
    attrNames = evaluatorInstance.recommender.numericAttrNames
    for id in weightList:
        a = open('weights/' + str(id) + '.txt', 'w')
        
        a.write(' '.join(attrNames) + '\n')
        for dictionary in weightList[id]:
            values = [str(dictionary[attr]) for attr in attrNames]
            line = ' '.join(values) + '\n'
            a.write(line)
            
        
def printNotes(recommender):
    if recommender.diversityEnabled == True:                       #Diversity should be enabled true
        print 'Diversity Enabled'
    if recommender.selectiveWtUpdateEnabled == True:               #Enable selective weight updation....
        print 'Selective Weight update enabled'
    if recommender.similarProdInFirstCycleEnabled == True:
        print 'Similar Products In First cycle Enabled'
    if recommender.targetProductDoesntAppearInFirstCycle == True:
        print 'Target Product Does not Appear in first cycle'
    if recommender.highestOverlappingProductsInTopK == True:
        print 'Highest Overlapping Products in topK in each cycle'
    
    if recommender.updateWeightsInTargetsDirection == True:         #Weights are always updated in the direction of target. Enabled 'True' only for testing purposes
        print 'Weights are always updated in target direction'
    if recommender.updateWeightsInLineWithTarget == True:           #only weights of attributes that are in-line with target are updated
        print 'Only weights of attributes that are in-line with the target are improved'
    #above two are hypothetical and won't be used in real experiments.
    if recommender.updateWeightsWrtInitPreferences == True:
        print 'Weights are updated wrt init preferences'
