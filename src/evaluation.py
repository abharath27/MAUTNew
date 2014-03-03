from recommender import *
from PCRecommender import *
from carRecommender import *
import random, itertools, util, sys, os, collections

class Evaluator:
    def __init__(self, config, domain = "Camera"):
        self.domain = domain
        self.recommender = Recommender()
        if domain == 'PC':
            self.recommender = PCRecommender()
        if domain == 'Cars':
            self.recommender = CarRecommender() 
        self.recommender.selectiveWtUpdateEnabled = config[0]
        self.recommender.diversityEnabled = config[1]
        self.recommender.neutralDirectionEnabled = False
        #If both params below are false, this becomes the standard MAUT evaluation.
        self.recommender.targetProductDoesntAppearInFirstCycle = False
        self.recommender.similarProdInFirstCycleEnabled = False
        self.recommender.averageProductEnabled = False 
        self.recommender.diversityEnabled = False
        self.recommender.updateWeightsWrtInitPreferences = False
        self.recommender.averageProductEnabled = False
        self.recommender.additiveUpdatesEnabled = True
        self.recommender.adaptiveSelectionEnabled = False
        self.recommender.historyEnabled = False
        self.recommender.deepHistoryEnabled = False
        self.recommender.weightedMLT = False
        self.targets = None
        self.ranks = collections.defaultdict(list)   #key is the iteration number, list of ranks is the value
        self.startAll(config[2])
    
    def startAll(self, numAttributes):
        #Make each product as the target 10 times...
        numExperiments = 5
        numGlobalIterations = 0; numIterationsList = []; totalCompatibility = 0; numWastedCycles = 0;
        averages = []; averageWithoutOnes = [];
        iterationsPerProduct = dict((id, []) for id in range(len(self.recommender.caseBase)))
        queries = iter([x[:-1].split() for x in open('queries.txt').readlines()])
        
        for tempVar in range(numExperiments):
            numIterationsList = []
            print 'len(caseBase) = ', len(self.recommender.caseBase)
            #singleId = 147
            #print 'Target:', self.recommender.caseBase[singleId]
            for prod in self.recommender.caseBase:
                print 'id = ', prod.id
                numLocalIterations = 1
                self.recommender.resetWeights()
                self.recommender.prodList = [copy.copy(x) for x in self.recommender.caseBase]
                queryAttributes = queries.next()
                initialPreferences = {}
                for attr in queryAttributes:
                    initialPreferences[attr] = prod.attr[attr]
                
                print 'initialPreferences = ', initialPreferences
                self.targets = [prod]           #self.targets = [prod] + self.dominatingProducts(prod)
                self.recommender.initialPreferences = initialPreferences
                self.recommender.target = self.targets[0].id 
                self.recommender.selectFirstProduct(initialPreferences)
                
                strings, rank, incByOne = self.recommender.critiqueStrings('firstTime')
                #print 'append rank =', rank
                self.ranks[numLocalIterations].append(rank)                 #book keeping
                targets = [x.id for x in self.targets]
                print 'First product selected:', self.recommender.currentReference
                
                while 1 and self.recommender.currentReference not in targets:
                    #When cthe target is selected as the first product (justification of above condition)
                    topKIds = [x.id for x in self.recommender.topK]
                    #print 'topK:', topKIds
                    #print 'selected product list:', [x.id for x in self.recommender.selectedProductsList]
                    if len(set(targets) & set(topKIds)) != 0:
                        break
                    numLocalIterations += (1+incByOne)
                    numWastedCycles += incByOne
                    selection, comp, numericAttrComp = self.recommender.maxCompatible(self.recommender.topK)
                    totalCompatibility += numericAttrComp
                    strings, rank, incByOne = self.recommender.critiqueStrings(selection)
                    self.ranks[numLocalIterations].append(rank)
                    #print "selection =", topKIds[selection], ", Compatiblity =", int(numericAttrComp*1000)/1000.0
                    
                    
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
        print 'Final average using the previous averages =', sum(averages)/len(averages)
        print 'Average without ones:', sum(averageWithoutOnes)/len(averageWithoutOnes)
        print 'Average numeric attr compatiblity = ', totalCompatibility/(numGlobalIterations)
        print 'Average without wasted cycles = ', (float(numGlobalIterations)-numWastedCycles)/(numExperiments*len(self.recommender.caseBase))
        print 'Percentage times adaptive selection was called:', float(numWastedCycles)/numGlobalIterations
        
        #self.printStatistics(iterationsPerProduct)
        util.printRanks(self)
        util.printWeights(self)
    
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
        print 'ID, NumDominators, IterationCycles'
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
