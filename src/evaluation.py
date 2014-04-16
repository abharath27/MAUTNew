from recommender import *
from PCRecommender import *
from carRecommender import *
import random, itertools, util, sys, os, collections, time

class Evaluator:
    def __init__(self, domain = "Camera"):
        self.domain = domain
        self.recommender = Recommender()
        if domain == 'PC':
            self.recommender = PCRecommender()
        if domain == 'Cars':
            self.recommender = CarRecommender() 

        #If all params below are false, this becomes the standard MAUT evaluation as in the paper
        #New baseline with the additiveUpdatesEnabled
        self.recommender.additiveUpdatesEnabled = False
        
        self.recommender.neutralDirectionEnabled = False
        self.recommender.selectiveWtUpdateEnabled = False
        self.recommender.targetProductDoesntAppearInFirstCycle = False
        self.recommender.similarProdInFirstCycleEnabled = False
        self.recommender.averageProductEnabled  = False 
        self.recommender.diversityEnabled = False
        self.recommender.updateWeightsWrtInitPreferences = False
        self.recommender.averageProductEnabled = False
        self.recommender.adaptiveSelectionEnabled = False
        self.recommender.historyEnabled = False
        self.recommender.deepHistoryEnabled = False
        self.recommender.historyWithSimilarityEnabled = False
        self.recommender.weightedMLT = False
        self.recommender.adaptiveSelectionWithNeutralAttributesEnabled = False
        self.recommender.fractionalDiversityEnabled = False
        self.recommender.marketEquilibriumEnabled = False
        self.recommender.attributeLevelDiversityEnabled = False
        
        self.targets = None
        self.ranks = collections.defaultdict(list)   #key is the iteration number, list of ranks is the value
        self.startAll()
    
    def startAll(self):
        #Make each product as the target 10 times...
        numExperiments = 5
        numGlobalIterations = 0; numIterationsList = []; totalCompatibility = 0; numWastedCycles = 0;
        averages = []; averageWithoutOnes = [];
        iterationsPerProduct = dict((id, []) for id in range(len(self.recommender.caseBase)))
        iterationsPerManufacturer = dict((man, []) for man in set([x.attr['Manufacturer'] for x in self.recommender.caseBase]))
        queries = iter([x[:-1].split() for x in open('q1.txt').readlines()])
        
        a = time.time()
        for tempVar in range(numExperiments):
            numIterationsList = []
            print 'len(caseBase) = ', len(self.recommender.caseBase)
            #singleId = 147
            #print 'Target:', self.recommender.caseBase[singleId]
            self.recommender.resetWeightList()
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
                print 'Target product price:', self.recommender.caseBase[targets[0]].attr['Price']
                
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
                    print 'Selected Index actually =', selection
                    print 'weight of price attribute:', self.recommender.weights['Price']
                    print self.recommender.topK[selection]
                    if selection > 7:
                        pass
                    totalCompatibility += numericAttrComp
                    strings, rank, incByOne = self.recommender.critiqueStrings(selection)
                    self.ranks[numLocalIterations].append(rank)
                    #print "selection =", topKIds[selection], ", Compatiblity =", int(numericAttrComp*1000)/1000.0
                    
                    
                print 'Number of interaction cycles =', numLocalIterations
                iterationsPerProduct[prod.id].append(numLocalIterations)
                iterationsPerManufacturer[prod.attr['Manufacturer']].append(numLocalIterations)
                numIterationsList.append(numLocalIterations)
            numGlobalIterations += sum(numIterationsList)
            #print 'Iterations List(Unsorted):', numIterationsList
            print 'Iterations List:', sorted(numIterationsList)
            print 'Average iteration for iteration number', tempVar, '=', sum(numIterationsList)/float(len(numIterationsList))
        
            averages.append(sum(numIterationsList)/float(len(numIterationsList)))
            newL = [x for x in numIterationsList if x != 1]
            if len(newL) != 0:
                averageWithoutOnes.append(sum(newL)/float(len(newL)))
                
        b = time.time()
        
        print 'time = ', b - a     
        print 'Average number of interaction cycles = ', float(numGlobalIterations)/(numExperiments*len(self.recommender.caseBase))
        print 'Final average using the previous averages =', sum(averages)/len(averages)
        print 'Average without ones:', sum(averageWithoutOnes)/len(averageWithoutOnes)
        print 'Average numeric attr compatiblity = ', totalCompatibility/(numGlobalIterations)
        print 'Average without wasted cycles = ', (float(numGlobalIterations)-numWastedCycles)/(numExperiments*len(self.recommender.caseBase))
        print 'Percentage times adaptive selection was called:', float(numWastedCycles)/numGlobalIterations
        print 'globalSum =', self.recommender.globalSum
        print 'globalCount =', self.recommender.globalCount
        #print 'Average times diversity was called =', (self.recommender.globalSum)/self.recommender.globalCount
        #print 'Average add Factor', float(self.recommender.globalSum)/self.recommender.globalCount
        self.printStatistics(iterationsPerProduct)
        self.printStatistics2(iterationsPerManufacturer)
        #util.printRanks(self)
        #util.printWeights(self)
    
    
    def printStatistics(self, iterationsPerProduct):
        numDominators = []; avgCycles = []                      #d denotes numDominators, i denotes iterationCycles
        print 'ID, NumDominators, IterationCycles'
        for prod in self.recommender.caseBase:
            l = copy.copy(iterationsPerProduct[prod.id])
            if len(l) == 0: continue
            averageIterations = sum(l)/float(len(l))
            numDominators.append(len(self.recommender.dominatingProducts(prod))); avgCycles.append(averageIterations)
             
        #print util.correlationCoefficient(numDominators, avgCycles)
    
    def printStatistics2(self, iterationsPerManufacturer):
        mainDict = {}; l = []
        for prod in self.recommender.caseBase:
            mainDict[prod.attr['Manufacturer']] = []
        
        for prod in self.recommender.caseBase:
            mainDict[prod.attr['Manufacturer']].append(len(self.recommender.dominatingProducts(prod)))
        
        for entry in mainDict:
            mainDict[entry] = float(sum(mainDict[entry]))/len(mainDict[entry])
            l.append((entry, mainDict[entry]))
        
        l = [t[0] for t in sorted(l, key = lambda x: -x[1])]
        print 'Man; dominators; average cycles'
        for entry in l:
            temp = iterationsPerManufacturer[entry]
            print entry, ',', mainDict[entry], ',', float(sum(temp))/len(temp)
        

eval = Evaluator(domain = "Camera")

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
