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
        numExperiments = 10
        numGlobalIterations = 0; numIterationsList = []
        
        for prod in self.recommender.caseBase[:numExperiments]:
            print 'next Iteration!!'
            self.recommender.prodList = copy.copy(self.recommender.caseBase)
            numberOfAttributesInQuery = 3                                   #TODO: Consider non-numeric attributes also..
            initialPrefAttributes = random.choice(list(itertools.combinations\
                                   (self.recommender.numericAttrNames, numberOfAttributesInQuery)))  
            #returns ('Price', 'Resolution) in case number of attr = 2
            initialPreferences = {}
            for attr in initialPrefAttributes:
                '''Main Part: Formulating the query'''
                #values = [prod2.attr[attr] for prod2 in self.recommender.prodList]
                #initialPreferences[attr] = random.choice(values)
                initialPreferences[attr] = prod.attr[attr]
            
            self.target = self.recommender.mostSimilar(prod) 
            self.recommender.selectFirstProduct(initialPreferences)
            self.recommender.critiqueStrings('firstTime')
            flag = 1
            numLocalIterations = 0
            print 'source ID =', prod.id
            print 'target ID =', self.target.id
            while flag == 1:
                for product in self.recommender.topK:
                    if self.target.id == product.id:    
                        flag = 0
                #Two ways to stop the iteration. a. Product is the currentRef b. Product is in compCrit list
                #self.topK i.e. top K products are set in the method self.reco.critiqueStrings
                selection = self.maxCompatible(self.recommender.topK)
                self.recommender.critiqueStrings(selection)
                print 'topK product IDs = ', [x.id for x in self.recommender.topK]
                numLocalIterations += 1
            numIterationsList.append(numLocalIterations)
            numGlobalIterations += numLocalIterations
            
            
        print 'Average number of interaction cycles = ', float(numGlobalIterations)/numExperiments
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
        print l
        return l[0][0]
    
    def direction(self, prod, reference):
        #Returns the dicitionary {'Price': 'less', 'Resolution': 'more'} indicating directions
        d = {}
        for attr in self.recommender.numericAttrNames:
            d[attr] = 'less' if prod.attr[attr] < reference.attr[attr] else 'more'
        return d
    
    def overlappingDegree(self, direction1, direction2):
        '''direction1 and direction2 are two dictionaries..'''
        '''Returns true if the number of 'less' and 'more' values of attributes are sufficiently overlapping'''
        total = len(direction1)
        overlapping = 0
        for attr in direction1:
            if direction1[attr] == direction2[attr]:
                overlapping += 1
        #print 'Overlap Ratio:', float(overlapping)/total
        return float(overlapping)/total
     
eval = Evaluator()
