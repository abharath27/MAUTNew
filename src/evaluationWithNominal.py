from recommender import *
from PCRecommender import *
from carRecommender import *
import random, itertools, util

class Evaluator:
    def __init__(self, domain = 'Camera'):
        self.recommender = Recommender()
        if domain == 'PC':
            self.recommender = PCRecommender()
        if domain == 'Cars':
            self.recommender = CarRecommender() 
        self.recommender.selectiveWtUpdateEnabled = False
        self.recommender.diversityEnabled = False
        self.recommender.neutralDirectionEnabled = False
        self.targets = None
        self.startAll()
        
    def startAll(self):
        #TODO: Introduce preferences on non-numeric attributes later...
        #Make each product as the target 10 times...
        #numExperiments = len(self.recommender.caseBase)
        numExperiments = 1
        numGlobalIterations = 0; numIterationsList = [];averages = []; averageWithoutOnes = [];
        iterationsPerProduct = dict((id, []) for id in range(len(self.recommender.caseBase)))
        for tempVar in range(numExperiments):
            numIterationsList = []
            #print 'len(caseBase) = ', len(self.recommender.caseBase)
            for prod in self.recommender.caseBase:
                #print '-------------------------------------------\nIteration No. ', prod.id, ':\n\n'
                #print 'id = ', prod.id
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
                #initialPrefAttributes = ['Format', 'OpticalZoom', 'Weight']
                #print initialPrefAttributes
                #returns ('Price', 'Resolution) in case number of attr = 2
                initialPreferences = {}
                for attr in initialPrefAttributes:
                    #'''Main Part: Formulating the query'''
                    initialPreferences[attr] = prod.attr[attr]
            
                #self.target = self.recommender.mostSimilar(prod)
                #self.targets = [prod] + self.dominatingProducts(prod)
                self.targets = [prod] 
                self.recommender.selectFirstProduct(initialPreferences)
                self.recommender.critiqueStrings('firstTime')
                numLocalIterations = 1
                targets = [x.id for x in self.targets]
                print 'Source ID:', prod.id
                #print 'Targets:', targets
                #print 'First product selected:', self.recommender.currentReference
                while 1 and self.recommender.currentReference not in targets:
                    #When cthe target is selected as the first product (justification of above condition)
                    topKIds = [x.id for x in self.recommender.topK]
                    #print '\ntopK product IDs = ', topKIds
                    if len(set(targets).intersection(set(topKIds))) != 0:
                        break
                    
                    #Two ways to stop the iteration. a. Product is the currentRef b. Product is in compCrit list
                    #self.topK i.e. top K products are set in the method self.reco.critiqueStrings
                    selection, compatibility = self.maxCompatible(self.recommender.topK)
                    self.recommender.critiqueStrings(selection)
                    #print "selection =", topKIds[selection], ", Compatiblity =", compatibility
                    numLocalIterations += 1
                    
                print 'Number of interaction cycles =', numLocalIterations
                iterationsPerProduct[prod.id].append(numLocalIterations)
                numIterationsList.append(numLocalIterations)
            numGlobalIterations += sum(numIterationsList)
            print 'Iterations List(Unsorted):', numIterationsList
            print 'Iterations List:', sorted(numIterationsList)
            print 'Average iteration for iteration number', tempVar, '=', sum(numIterationsList)/float(len(numIterationsList))
            averages.append(sum(numIterationsList)/float(len(numIterationsList)))
            newL = [x for x in numIterationsList if x != 1]
            averageWithoutOnes.append(sum(newL)/float(len(newL)))
                
                
        print 'Average number of interaction cycles = ', float(numGlobalIterations)/(numExperiments*len(self.recommender.caseBase))
        print 'Final average using the previous 10 averages =', sum(averages)/len(averages)
        print 'Average without ones:', sum(averageWithoutOnes)/len(averageWithoutOnes)
        print 'ID, NumDominators, IterationCycles'
        
        #self.printStatistics(iterationsPerProduct)
        
    
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
                attrDirections = self.direction(prod, reference, target)
                targetAttrDirections = self.direction(target, reference, target)
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
        return l[0]
    
    def direction(self, prod, reference, target):
        #Returns the dicitionary {'Price': 'less', 'Resolution': 'more'} indicating directions
        d = {}
        for attr in self.recommender.numericAttrNames:
            d[attr] = 'less' if prod.attr[attr] < reference.attr[attr] else 'more'
#        for attr in self.recommender.nonNumericAttrNames:
#            d[attr] = 1 if prod.attr[attr] == target.attr[attr] else 0
        return d
    
    def overlappingDegree(self, direction1, direction2):
        '''direction1 and direction2 are two dictionaries..'''
        '''Returns true if the number of 'less' and 'more' values of attributes are sufficiently overlapping'''
        total = len(direction1)
        overlapping = 0
        for attr in self.recommender.numericAttrNames:
            if direction1[attr] == direction2[attr]:
                overlapping += 1
#        for attr in self.recommender.nonNumericAttrNames:
#            if direction1[attr] == direction2[attr]:
#                overlapping += 1
#        #print 'Overlap Ratio:', float(overlapping)/total
        return float(overlapping)/total
    
    def printStatistics(self, iterationsPerProduct):
        numDominators = []; avgCycles = []                      #d denotes numDominators, i denotes iterationCycles
        for prod in self.recommender.caseBase:
            l = copy.copy(iterationsPerProduct[prod.id])
            averageIterations = sum(l)/float(len(l))
            numDominators.append(len(self.dominatingProducts(prod))); avgCycles.append(averageIterations)
            print prod.id, ',', len(self.dominatingProducts(prod)), ',', averageIterations
             
        print util.correlationCoefficient(numDominators, avgCycles)
     
eval = Evaluator()

'''Code with statistics about dominating products. works perfectly fine'''
#Statistics:
#1. Number of products that have at least one dominator (report the percentage)
#2. Average number of dominators per product
#3. Product with highest number of dominators; and the number of dominators it has.
#4. Product which is dominating the highest number of products
#        numProductsWithDominators = 0
#        totalNumberOfDominators = 0
#        maxDominators = -1; maxDominatorsProduct = None
#        dominating = dict([(x.id, 0) for x in self.recommender.caseBase])
#        
#        for prod in self.recommender.caseBase:
#            dominators = [x.id for x in self.dominatingProducts(prod)]
#            if len(dominators) > 0:
#                numProductsWithDominators += 1              #Objective-1
#                totalNumberOfDominators += len(dominators)  #Objective-2
#                if len(dominators) > maxDominators:         #Objective-3
#                    maxDominators = len(dominators)
#                    maxDominatorsProduct = prod.id
#                for temp in dominators:                     #Objective-4
#                    dominating[temp] += 1
#        
#        tempVar = sorted([(x, dominating[x]) for x in dominating], key = lambda t: -t[1])[0]
#        print 'Number of products with atleast one dominator = ', numProductsWithDominators
#        print 'Average number of dominators per product =', totalNumberOfDominators/float(numProductsWithDominators)
#        print 'Product with highest number of dominators:', maxDominatorsProduct
#        print 'Number of dominators it has:', maxDominators
#        print 'Product that dominates the highest number of products:', tempVar[0]
#        print 'Number of products it dominates:', tempVar[1]
#        
#        print 'Average Number of targets per product =', totalNumberOfDominators/float(len(self.recommender.caseBase))
