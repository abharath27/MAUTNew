from recommender import *
from PCRecommender import *
from carRecommender import *
import random, itertools, util, sys, os

class Evaluator:
    def __init__(self, config, domain = "Camera"):
        self.recommender = Recommender()
        if domain == 'PC':
            self.recommender = PCRecommender()
        if domain == 'Cars':
            self.recommender = CarRecommender() 
        self.recommender.selectiveWtUpdateEnabled = config[0]
        self.recommender.diversityEnabled = config[1]
        self.recommender.neutralDirectionEnabled = False
        self.targets = None
        self.startAll(config[2])
        
    def startAll(self, numAttributes):
        #TODO: Introduce preferences on non-numeric attributes later...
        #Make each product as the target 10 times...
        #numExperiments = len(self.recommender.caseBase)
        numExperiments = 5
        numGlobalIterations = 0; numIterationsList = [];averages = []; averageWithoutOnes = [];
        iterationsPerProduct = dict((id, []) for id in range(len(self.recommender.caseBase)))
        for tempVar in range(numExperiments):
            numIterationsList = []
            print 'len(caseBase) = ', len(self.recommender.caseBase)
            #singleId = 147
            #print 'Target:', self.recommender.caseBase[singleId]
            for prod in self.recommender.caseBase:
                #print '-------------------------------------------\nIteration No. ', prod.id, ':\n\n'
                print 'id = ', prod.id
                self.recommender.resetWeights()
                #print '==================='
                #print 'Weights:'
                for attr in self.recommender.weights:
                    #print attr,':', (int(self.recommender.weights[attr]*100)/100.0),
                    pass
                #print '==================='
                
                self.recommender.prodList = [copy.copy(x) for x in self.recommender.caseBase]
                numberOfAttributesInQuery = numAttributes
                initialPrefAttributes = random.choice(list(itertools.combinations\
                                       (self.recommender.attrNames, numberOfAttributesInQuery)))
                #initialPrefAttributes = ['StorageIncluded']
                print initialPrefAttributes
                #returns ('Price', 'Resolution) in case number of attr = 2
                initialPreferences = {}
                for attr in initialPrefAttributes:
                    #'''Main Part: Formulating the query'''
                    initialPreferences[attr] = prod.attr[attr]
            
                #self.target = self.recommender.mostSimilar(prod)
                #self.targets = [prod] + self.dominatingProducts(prod)
                self.recommender.initialPreferences = initialPreferences
                self.targets = [prod]
                self.recommender.target = self.targets[0].id 
                self.recommender.selectFirstProduct(initialPreferences)
                self.recommender.critiqueStrings('firstTime')
                numLocalIterations = 1
                targets = [x.id for x in self.targets]
                #print 'Source ID:', prod.id
                #print 'Targets:', targets
                print 'First product selected:', self.recommender.currentReference
                while 1 and self.recommender.currentReference not in targets:
                    #When cthe target is selected as the first product (justification of above condition)
                    topKIds = [x.id for x in self.recommender.topK]
                    print 'topK:', topKIds
                    if len(set(targets).intersection(set(topKIds))) != 0:
                        break
                    
                    #Two ways to stop the iteration. a. Product is the currentRef b. Product is in compCrit list
                    #self.topK i.e. top K products are set in the method self.reco.critiqueStrings
                    selection, compatibility = self.recommender.maxCompatible(self.recommender.topK)
                    self.recommender.critiqueStrings(selection)
                    print "selection =", topKIds[selection], ", Compatiblity =", int(compatibility*1000)/1000.0
                    numLocalIterations += 1
                    
                print 'Number of interaction cycles =', numLocalIterations
                iterationsPerProduct[prod.id].append(numLocalIterations)
                numIterationsList.append(numLocalIterations)
            numGlobalIterations += sum(numIterationsList)
            #print 'Iterations List(Unsorted):', numIterationsList
            print 'Iterations List:', sorted(numIterationsList)
            print 'Average iteration for iteration number', tempVar, '=', sum(numIterationsList)/float(len(numIterationsList))
            averages.append(sum(numIterationsList)/float(len(numIterationsList)))
            newL = [x for x in numIterationsList if x != 1]
            if len(newL) != 0:
                averageWithoutOnes.append(sum(newL)/float(len(newL)))
                
                
        print 'Average number of interaction cycles = ', float(numGlobalIterations)/(numExperiments*len(self.recommender.caseBase))
        print 'Final average using the previous 10 averages =', sum(averages)/len(averages)
        print 'Average without ones:', sum(averageWithoutOnes)/len(averageWithoutOnes)
        print 'ID, NumDominators, IterationCycles'
        
        self.printStatistics(iterationsPerProduct)
        
    
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
    
    def printStatistics(self, iterationsPerProduct):
        numDominators = []; avgCycles = []                      #d denotes numDominators, i denotes iterationCycles
        for prod in self.recommender.caseBase:
            l = copy.copy(iterationsPerProduct[prod.id])
            if len(l) == 0: continue
            averageIterations = sum(l)/float(len(l))
            numDominators.append(len(self.dominatingProducts(prod))); avgCycles.append(averageIterations)
            print prod.id, ',', len(self.dominatingProducts(prod)), ',', averageIterations
             
        #print util.correlationCoefficient(numDominators, avgCycles)
     

if len(sys.argv) != 2:
    print 'Usage: python eval.py configx'
    exit()
t = [x[:-1] for x in open(sys.argv[1]).readlines()]
args = [t[0] == 'True', t[1] == 'True', int(t[2])]
eval = Evaluator(config = args)

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
