from recommender import *
from PCRecommender import *
from carRecommender import *
import random, itertools
class EvaluatorWithUnitCritiques:
    def __init__(self, domain = "Camera"):
        self.recommender = Recommender()
        if domain == 'PC':
            self.recommender = PCRecommender()
        if domain == 'Cars':
            self.recommender = CarRecommender() 
        self.recommender.selectiveWtUpdateEnabled = True
        self.recommender.diversityEnabled = True
        self.recommender.neutralDirectionEnabled = False
        self.threshold = 0.5
        self.targets = None
        self.startAll()
        
    def startAll(self):
        #TODO: Introduce preferences on non-numeric attributes later...
        #Make each product as the target 10 times...
        #numExperiments = len(self.recommender.caseBase)
        numExperiments = 3
        numGlobalIterations = 0; numIterationsList = []; averages = []
        for tempVar in range(numExperiments):
            numIterationsList = []
            for prod in self.recommender.caseBase:
                #print '-------------------------------------------\nIteration No. ', prod.id, ':\n\n'
                self.recommender.resetWeights()
                #print '==================='
                #print 'Weights:'
                for attr in self.recommender.weights:
                    #print attr,':', (int(self.recommender.weights[attr]*100)/100.0),
                    pass
                #print '==================='
                
                self.recommender.prodList = [copy.copy(x) for x in self.recommender.caseBase]
                numberOfAttributesInQuery = 1
                initialPrefAttributes = random.choice(list(itertools.combinations\
                                       (self.recommender.attrNames, numberOfAttributesInQuery)))  
                #returns ('Price', 'Resolution) in case number of attr = 2
                initialPreferences = {}
                #print initialPrefAttributes
                for attr in initialPrefAttributes:
                    '''Main Part: Formulating the query'''
                    initialPreferences[attr] = prod.attr[attr]
            
                #self.target = self.recommender.mostSimilar(prod)
                self.targets = [prod] + self.dominatingProducts(prod) 
                self.recommender.selectFirstProduct(initialPreferences)
                self.recommender.critiqueStrings('firstTime')
                numLocalIterations = 1
                targets = [x.id for x in self.targets]
                #print 'Source ID:', prod.id
                #print 'Targets:', targets
                #print 'First product selected:', self.recommender.currentReference
                while 1 and self.recommender.currentReference not in targets:
                    #When the target is selected as the first product (justification of above condition)
                    topKIds = [x.id for x in self.recommender.topK]
                    #print 'topK product IDs = ', topKIds
                    if len(set(targets).intersection(set(topKIds))) != 0:
                        break
                    #Two ways to stop the iteration. a. Product is the currentRef b. Product is in compCrit list
                    #self.topK i.e. top K products are set in the method self.reco.critiqueStrings
                    selection, degree = self.maxCompatible(self.recommender.topK)
                    if degree > self.threshold:
                        self.recommender.critiqueStrings(selection)
                    else:
                        target = random.choice(self.targets)
                        while 1:
                            #to ensure that applying the unit critique "low" or "high" will be meaningful
                            #We may encounter the case when both the target's and current prod's storage values are same as 32MB.
                            unitAttributeNumber = random.randint(0, len(self.recommender.numericAttrNames)-1)
                            attr = self.recommender.numericAttrNames[unitAttributeNumber]
                            value = self.recommender.caseBase[self.recommender.currentReference].attr[attr]
                        
                            if value != target.attr[attr]:
                                break
                        
                        type = 'low' if target.attr[attr] < value else 'high'
                        try:
                            self.recommender.unitCritiqueSelectedStrings(unitAttributeNumber, value, type)
                        except:
                            print 'attr =', attr
                            print 'current Reference =', self.recommender.currentReference
                            print 'value of current ref attr =', value
                            print 'target =', target.id, "target's value = ", target.attr[attr]
                            print 'type =', type
                            print 'True or false:', target.id in [x.id for x in self.recommender.prodList]
                            print '!!!!!!!!!!!!!!!!!!EXITING!!!!!!!!!!!'
                            exit()
                    numLocalIterations += 1
                    
                #print 'Number of interaction cycles =', numLocalIterations
                numIterationsList.append(numLocalIterations)
            numGlobalIterations += sum(numIterationsList)
            print 'Iterations List(Unsorted):', numIterationsList
            print 'Iterations List:', sorted(numIterationsList)
            print 'Average iteration for iteration number', tempVar, '=', sum(numIterationsList)/float(len(numIterationsList))
            averages.append(sum(numIterationsList)/float(len(numIterationsList)))
                
                
        print 'Average number of interaction cycles = ', float(numGlobalIterations)/(numExperiments*len(self.recommender.caseBase))
        print 'Final average using the previous 10 averages =', sum(averages)/len(averages)
        
    def dominatingProducts(self, p):
        dominators = []
        for prod in self.recommender.caseBase:
            if prod.id == p.id: continue
            flag = 0
            for attr in self.recommender.libAttributes:
                if prod.attr[attr] > p.attr[attr]:
                    flag = 1
            for attr in self.recommender.mibAttributes:
                if prod.attr[attr] < p.attr[attr]:
                    flag = 1
            if flag == 0:
                dominators.append(prod)
        return dominators
    
    def maxCompatible(self, products):
        #Return the indices of those products whose critique strings are compatible with target
        #Keep a threshold of atleast 4 out of 6 attributes should be compatible..
        l = [];
        reference = self.recommender.caseBase[self.recommender.currentReference]
        for i, prod in enumerate(products):
            maxDegree = -1
            for target in self.targets:    
                attrDirections = self.direction(prod, reference)
                targetAttrDirections = self.direction(prod, target)
                overlapDegree = self.overlappingDegree(attrDirections, targetAttrDirections)    
                #print 'Compound critique product ID = ', prod.id
                #print 'attrDirections:', attrDirections
                #print 'targetAttrDirections: ', targetAttrDirections
                if overlapDegree > maxDegree:
                    maxDegree = overlapDegree
            l.append((i, maxDegree))
        
        l = sorted(l, key = lambda x: -x[1])
        #If multiple products have the same overlapping 
        l2 = [(products[i].id, int(j*100)/100.0) for i, j in l]
        #print l2
        #print 'maxCompatible Product ID =', l2[0][0]
        return l[0] #Returning the max compatible product along with it's overlapping degree.
    
    def direction(self, prod, reference):
        #Returns the dicitionary {'Price': 'less', 'Resolution': 'more'} indicating directions
        d = {}
        for attr in self.recommender.numericAttrNames:
            d[attr] = 'less' if prod.attr[attr] < reference.attr[attr] else 'more'
        for attr in self.recommender.nonNumericAttrNames:
            d[attr] = 1 if prod.attr[attr] == reference.attr[attr] else 0
        return d
    
    
    def overlappingDegree(self, direction1, direction2):
        '''direction1 and direction2 are two dictionaries..'''
        '''Returns true if the number of 'less' and 'more' values of attributes are sufficiently overlapping'''
        total = len(direction1)
        overlapping = 0
        for attr in self.recommender.numericAttrNames + self.recommender.nonNumericAttrNames:
            if direction1[attr] == direction2[attr]:
                overlapping += 1
        #print 'Overlap Ratio:', float(overlapping)/total
        return float(overlapping)/total
     
eval = EvaluatorWithUnitCritiques('PC')
