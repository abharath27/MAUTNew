from recommender import *
import random, itertools
class Evaluator:
    def __init__(self):
        self.recommender = Recommender()
        self.target = None
        self.threshold = 0.6            #Min fraction of attributes whose values need to be compatible
                                        #with the target product. 4 out of 6 attributes must overlap here
        self.startAll()
        
    def startAll(self):
        #TODO: Introduce preferences on non-numeric attributes later...
        #Make each product as the target 10 times...
        #numExperiments = len(self.recommender.caseBase)
        numExperiments = 1
        numGlobalIterations = 0; numIterationsList = []
        
        for prod in self.recommender.caseBase[:numExperiments]:
            print '-------------------------------------------\nNew Iteration:\n\n'
            
            self.recommender.setWeights()
            print '==================='
            print 'Weights:'
            for attr in self.recommender.weights:
                print attr,':', (int(self.recommender.weights[attr]*100)/100.0),
            print '==================='
            
            self.recommender.prodList = copy.copy(self.recommender.caseBase)
            numberOfAttributesInQuery = 3
            initialPrefAttributes = random.choice(list(itertools.combinations\
                                   (self.recommender.attrNames, numberOfAttributesInQuery)))  
            #returns ('Price', 'Resolution) in case number of attr = 2
            initialPreferences = {}
            for attr in initialPrefAttributes:
                '''Main Part: Formulating the query'''
                initialPreferences[attr] = prod.attr[attr]
                
                
            self.recommender.prodList = [tempProd for tempProd in self.recommender.prodList if tempProd.id != prod.id]
            #self.target = self.recommender.mostSimilar(prod)
            self.target = prod 
            self.recommender.selectFirstProduct(initialPreferences)
            self.recommender.critiqueStrings('firstTime')
            numLocalIterations = 1
            print 'target ID =', self.target.id
            
            while 1 and self.recommender.currentReference != self.target.id:
                #When the target is selected as the first product (justification of above condition)
                topKIds = [x.id for x in self.recommender.topK]
                print 'topK product IDs = ', topKIds
                if self.target.id in topKIds:    
                    break
                #Two ways to stop the iteration. a. Product is the currentRef b. Product is in compCrit list
                #self.topK i.e. top K products are set in the method self.reco.critiqueStrings
                selection = self.maxCompatible(self.recommender.topK)
                self.recommender.critiqueStrings(selection)
                numLocalIterations += 1
            print 'Number of interaction cycles =', numLocalIterations
            numIterationsList.append(numLocalIterations)
            numGlobalIterations += numLocalIterations
            
            
        print 'Average number of interaction cycles = ', float(numGlobalIterations)/numExperiments
        print 'Iterations List(Unsorted):', numIterationsList
        print 'Iterations List:', sorted(numIterationsList)
        
        
    def maxCompatible(self, products):
        #Return the indices of those products whose critique strings are compatible with target
        #Keep a threshold of atleast 4 out of 6 attributes should be compatible..
        ret = []; l = [];
        for i, prod in enumerate(products):
            reference = [temp for temp in self.recommender.caseBase if temp.id == self.recommender.currentReference][0]
            attrDirections = self.direction(prod, reference)
            targetAttrDirections = self.direction(prod, self.target)
            
            #print 'Compound critique product ID = ', prod.id
            #print 'attrDirections:', attrDirections
            #print 'targetAttrDirections: ', targetAttrDirections
            l.append((i, self.overlappingDegree(attrDirections, targetAttrDirections)))
        
        l = sorted(l, key = lambda x: -x[1])
        #If multiple products have the same overlapping 
        l2 = [(products[i].id, int(j*100)/100.0) for i, j in l]
        print l2
        print 'maxCompatible Product ID =', l2[0][0]
        return l[0][0]
    
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
     
eval = Evaluator()
