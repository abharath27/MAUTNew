import first, copy, util, inspect, random, collections

class Recommender:
    '''Every class inheriting Recommender should initialize the following variables'''
    '''1. self.initialPreferences; 2. self.target'''
    def __init__(self):
        self.attrNames = ['Manufacturer', 'Price', 'Format', 'Resolution', 'OpticalZoom', 'DigitalZoom',\
                           'Weight', 'StorageType', 'StorageIncluded']
        self.numericAttrNames = ['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
        self.nonNumericAttrNames = ['Manufacturer', 'Format', 'StorageType']
        self.libAttributes = ['Price', 'Weight']
        self.mibAttributes = ['Resolution', 'OpticalZoom', 'DigitalZoom', 'StorageIncluded']
        self.prodList = first.readList()
        #self.prodList = [x for x in self.prodList if x.attr['Price'] < 1000]
        self.caseBase = [copy.copy(x) for x in self.prodList]        #caseBase is unchanging. Items are added
        self.initializeOtherVars()
        
    def initializeOtherVars(self):
        '''This function is common for recommenders of all other domains like PC, cars etc'''
        self.preComputeMaxMinAttrValues()
        self.K = 5                                      
        self.currentReference = -1
        self.topK = [None]*self.K
        self.alpha = 0.5
        self.target = -1                        #set by Evaluator() instance
        self.initialPreferences = {}            #initial preferences of the user. set by Evaluator() instance
        
        #book-keeping attributes
        self.attrDirection = {}
        self.unitAttrPreferences = {}
        self.critiqueStringDirections = {}
        utilitySortedProducts = None
        self.weightIncOrDec = dict([(attr, None) for attr in self.numericAttrNames + self.nonNumericAttrNames])   #To let the interface know
        self.preComputedAttrSigns = {}
        self.nominalAttributesEnabled = True                #In the function 'selectFirstProduct()', self.nonNumericAttrNames = []
        self.neutralDirectionEnabled = True                 #It's set to false during evaluation, neutral direction helps for the proper display of critique strings
        self.selectedProductsList = []                      #It is initialized with the first product selected and every product that is subsequently chosen by user is added.
        self.weightsList = collections.defaultdict(list)
        self.globalSum = 0                                  #globalSum and globalCount are gen book keeping attributes
        self.globalCount = 0                                #They will be used to monitor the average compatibility, average rank and stuff like that
        
        #modifications turn on/off. By default they are turned off. Inheriting class should turn them on.
        self.diversityEnabled = False                       #Diversity should be enabled true
        self.selectiveWtUpdateEnabled = False               #Enable selective weight updation....
        self.similarProdInFirstCycleEnabled = False
        self.targetProductDoesntAppearInFirstCycle = False
        self.highestOverlappingProductsInTopK = False
        self.averageProductEnabled = False
        self.historyEnabled = False
        self.deepHistoryEnabled = False
        self.historyWithSimilarityEnabled = False           #retVal will be added with similarity instead of directional similarity.
        self.additiveUpdatesEnabled = False
        self.adaptiveSelectionEnabled = False
        self.weightedMLT = False
        self.adaptiveSelectionWithNeutralAttributesEnabled = False
        self.fractionalDiversityEnabled = False
        self.marketEquilibriumEnabled = False
        self.attributeLevelDiversityEnabled = False
        
        #weight update strategies. Max one of them should be turned on at any moment.
        self.updateWeightsInTargetsDirection = False         #Weights are always updated in the direction of target. Enabled 'True' only for testing purposes
        self.updateWeightsInLineWithTarget = False           #only weights of attributes that are in-line with target are updated
        #above two are hypothetical and won't be used in real experiments.
        self.updateWeightsWrtInitPreferences = False        #This technique successfully works
        
        
        if self.nominalAttributesEnabled == False:
            self.nonNumericAttrNames = []
        
        self.resetWeights()
        
    def resetWeights(self):
        '''resets weights and value functions of numeric, nominal attributes'''
        self.weights = dict([(attr, 1.0/(len(self.numericAttrNames))) for attr in self.numericAttrNames])
        self.nonNumericValueDict = {}
        self.nonNumericAttrDenominator = {}                 #Non-numeric attribute weights are updated as 1/15,2/16, 3/17 and so on..., this dictionary maintains the current denominator
        for attr in self.nonNumericAttrNames:
            distinctVals = list(set([prod.attr[attr] for prod in self.caseBase]))
            self.nonNumericValueDict[attr] = dict([(val, 1.0/len(distinctVals)) for val in distinctVals])
            if self.marketEquilibriumEnabled == True:
                if len(distinctVals) >= 10:
                    print 'market equilibrium attr:', attr
                    self.nonNumericValueDict[attr] = self.preComputeNominalAttrValues(attr)
                    print self.nonNumericValueDict[attr]
                    
            self.nonNumericAttrDenominator[attr] = len(distinctVals)
        self.selectedProductsList = []
    
    def resetWeightList(self):
        self.weightsList = collections.defaultdict(list)
        
    def preComputeMaxMinAttrValues(self):
        '''precomputes max and min values of numeric attributes into the dictionary self.maxV and self.minV'''
        self.maxV = {}; self.minV = {}
        for attr in self.numericAttrNames:        
            priceList = [prod.attr[attr] for prod in self.caseBase]
            self.maxV[attr], self.minV[attr] = max(priceList), min(priceList)
            print 'range of attr', attr, ':', self.maxV[attr]-self.minV[attr]
    
    def preComputeNominalAttrValues(self, attr):
        mainDict = {}; l = []; sum2 = 0
        dict2 = {}
        for prod in self.caseBase:
            mainDict[prod.attr[attr]] = []
            dict2[prod.attr[attr]] = 0
            
        for prod in self.caseBase:
            mainDict[prod.attr[attr]].append(len(self.dominatingProducts(prod)))
            dict2[prod.attr[attr]] += 1
        
        #l1 = [('Fujitsu', 12.3), ('Apple', 12.4), ('HP', 4.6), ('Compaq', 7.6)]
        #l2 = [('Gateway', 5.7), ('Dell', 4.7), ('Toshiba', 5.5), ('Sony', 7.5)]
        #mainDict = dict(l1 + l2)
        for entry in mainDict:
            temp = float(sum(mainDict[entry]))/len(mainDict[entry])
            #sum2 += mainDict[entry] 
            sum2 += temp*dict2[entry]
            mainDict[entry] = temp*dict2[entry]     #More the frequency, more is the mainDict value...
        
        
        
        for entry in mainDict:
            mainDict[entry] /= sum2
            
        return mainDict
    
    def dominatingProducts(self, p):
        dominators = []
        for prod in self.caseBase:
            if prod.id == p.id: continue
            flag = 0
            for attr in self.libAttributes:
                if prod.attr[attr] > p.attr[attr]:
                    flag = 1
            for attr in self.mibAttributes:
                if prod.attr[attr] < p.attr[attr]:
                    flag = 1
            if flag == 0:
                dominators.append(prod)
        return dominators
    
    def sanityCheck(self):
        #sanity check
        numEnabled = self.updateWeightsInLineWithTarget + self.updateWeightsInTargetsDirection + self.updateWeightsWrtInitPreferences
        if numEnabled > 1: print 'More than one weight update technique enabled; exiting;'; exit()
        numEnabled = self.historyEnabled + self.deepHistoryEnabled + self.historyWithSimilarityEnabled
        if numEnabled > 1: print 'More than one history techniques enabled; exiting;'; exit()
        numEnabled = self.adaptiveSelectionEnabled + self.adaptiveSelectionWithNeutralAttributesEnabled
        if numEnabled > 1: print 'More than one adaptive selections enabled; exiting;'; exit()
        if self.neutralDirectionEnabled == False and self.adaptiveSelectionWithNeutralAttributesEnabled == True:
            print 'Neutral direction not Enabled. But adaptive Selection with neutral attributes enabled, exiting'; exit()
        
        util.printNotes(self)
            
    def utility(self, product, weights):
        '''Input: product and a dict of weights. Output: Utility of the product wrt that weight model'''
        '''Probable for side-effects because it has many callers'''
        '''To work correctly, function should be called just before the variable self.topK is set, and the user selected product has already been added to self.selectedProductsList'''
        '''Caller will be either selectTopK(), unitCritiqueSelectedStrings(), stuffForUtilitesFrame()'''
        retVal = 0; currentProd = product
        if self.historyEnabled == True:
            if len(self.selectedProductsList) > 1:      #If this length was equal to one, then we can't do anything with the history info
                previousReference = self.selectedProductsList[-2]
                previousUserSelectedProduct = self.selectedProductsList[-1]
                targetProd = self.caseBase[self.target]     #dummy, won't be used anyways, since we are calculating only numeric attribute overlaps...
                dir1 = self.direction(previousUserSelectedProduct, previousReference, targetProd)
                dir2 = self.direction(currentProd, previousReference, targetProd)
                overlappingNumericAttr = set(self.overlappingAttributes(dir1, dir2)) & set(self.numericAttrNames)
                retVal += len(overlappingNumericAttr)/float(len(self.numericAttrNames))     #it looks like retVal is quite significant
#                if product.id == self.target:
#                    print 'previous user selected product:', previousUserSelectedProduct.id
#                    print 'previous reference:', previousReference.id
#                    print 'retVal =', retVal

        if self.historyWithSimilarityEnabled == True:
            if len(self.selectedProductsList) > 1:      #If this length was equal to one, then we can't do anything with the history info
                previousUserSelectedProduct = self.selectedProductsList[-1]
                targetProd = self.caseBase[self.target]     #dummy, won't be used anyways, since we are calculating only numeric attribute overlaps...
                similarity = self.sim(currentProd, previousUserSelectedProduct.attr)
                retVal += 0.5*similarity
            
        
        if self.deepHistoryEnabled == True:
            historySize = len(self.selectedProductsList)
            for i in range(1,historySize):
                reference = self.selectedProductsList[i-1]
                selectedProduct = self.selectedProductsList[i]
                targetProd = self.caseBase[self.target]
                dir1 = self.direction(selectedProduct, reference, targetProd)
                dir2 = self.direction(currentProd, reference, targetProd)
                overlappingNumericAttr = set(self.overlappingAttributes(dir1, dir2)) & set(self.numericAttrNames)
                retVal = retVal +  (2**(i-historySize))* (len(overlappingNumericAttr)/float(len(self.numericAttrNames)))     #it looks like retVal is quite significant
                
        for attr in self.numericAttrNames:
            retVal += self.weights[attr] * self.value(attr, product.attr[attr])
        for attr in self.nonNumericAttrNames:
            retVal += self.nonNumericValueDict[attr][product.attr[attr]]
        return retVal
    
    def sim(self, product, preferences):
        '''Input: dictionary of preferences and product. Output: similarity between the product and preferences'''
        retVal = 0
        for attr in preferences:
            if attr in self.numericAttrNames:
                maxV, minV = self.maxV[attr], self.minV[attr]
                retVal += (1-abs((preferences[attr] - product.attr[attr])/(maxV - minV)))
                
            else:   #NOMINAL ATTRIBUTES
                #IDEALLY, there should be a similarity measure defined between different brands...
                if preferences[attr] == product.attr[attr]:
                    retVal += 1
        
        similarity = float(retVal)/len(preferences)
        return similarity
    
    
    def selectFirstProduct(self, preferences, specialArg = None):
        '''Removes the first product from self.prodList and sets the variable self.currentReference'''
        self.sanityCheck()      #Do all kinds of checks if the system is proper to go ahead; before starting the recommendation process
        if self.nominalAttributesEnabled == False:
            self.nonNumericAttrNames = []
        if self.targetProductDoesntAppearInFirstCycle == True:
            self.prodList = [x for x in self.prodList if x.id != self.target]
        newBase = [copy.copy(x) for x in self.prodList]; random.shuffle(newBase)
        similarities = [(prod, self.sim(prod, preferences)) for prod in newBase]
        similarities = sorted(similarities, key = lambda x: -x[1])
        #print similarities[:5]
        topProduct = similarities[0][0]
        self.currentReference = topProduct.id
        #print 'First Product Selected = ', topProduct.id
        if specialArg != None:          #'specialArg'th product is the current reference
            self.currentReference = specialArg
        
        if self.targetProductDoesntAppearInFirstCycle == True:
            self.prodList.append(self.caseBase[self.target])
        self.prodList = [x for x in self.prodList if x.id != self.currentReference]     #remove currentReference from prodlist
        
        
    def preComputeAttributeSigns(self):
        '''Fills in the dictionary preComputedAttributeSigns'''
        reference = self.caseBase[self.currentReference]
        for prod in self.caseBase:
            self.preComputedAttrSigns[prod.id] = self.attributeSignsUtil(prod, reference)
    
    def critiqueSim(self, prod1, prod2):
        '''Input: Two products prod1, prod2. Output: overlap between critique strings of prod1, prod2'''
        #self.precomputedAttrSigns is already set before calling this function
        l1 = self.preComputedAttrSigns[prod1.id]
        l2 = self.preComputedAttrSigns[prod2.id]
        overlap = sum([l1[i] == l2[i] for i in range(len(l1))])
        overlap /= float(len(l1))
        return overlap
    
    def quality(self, c, P):
        alpha = self.alpha
        retVal = alpha*self.utility(c, self.weights)        #TODO: utility score can actually be greater than 1. Best to normalize it if you want best results for alpha = 0.5
        #diversity(c, P) = \sum(1-sim(c, Ci))/n
        dissimilarity = 0
        for prod in P:
            dissimilarity += (1-self.critiqueSim(c, prod))
            #dissimilarity += (1-self.sim(c, prod.attr))
        if len(P) != 0:
            dissimilarity /= len(P)     #Normalizing it to one
        retVal += (1-alpha) * dissimilarity
        return retVal
     
    def quality2(self, c, P, previousTopK):
        alpha = self.alpha
        retVal = alpha*self.utility(c, self.weights)
        #diversity(c, P) = \sum(1-sim(c, Ci))/n
        dissimilarity = 0
        for prod in P:
            #diversity += (1-self.critiqueSim(c, prod))
            dissimilarity += (1-self.sim(c, prod.attr))
        dissimilarity += sum([(1-self.sim(c, prod.attr)) for prod in previousTopK])
        
        dissimilarity /= (len(P) + len(previousTopK))     #Normalizing it to one
        retVal += (1-alpha) * dissimilarity
        return retVal
     
    def boundedGreedy(self, productList, adaptiveSelection = False, previousTopK = None, alreadyExisting = []):
        #Implementing the Barry Smyth and McClave(2001) Algorithm
        #Quality(c,P) = a*utility(c) + (1-a)*(diversity(c,P))
        #alreadyExisting is set by the fractional diversity enabled option. They are already existing in the list
        
        t = [(p, self.utility(p, self.weights)) for p in productList]
        productList = [p[0] for p in sorted(t, key = lambda x:-x[1])][:40]
        tempList = alreadyExisting   #This will hold the topK products found so far
        print 'len(productList) = ', len(productList)
        print 'len(alreadyExisting) =', len(alreadyExisting)
        print 'already Existing = ', [x.id for x in alreadyExisting]
        productList = [x for x in productList if x.id not in [r.id for r in alreadyExisting]]
        print 'len(productList) = ', len(productList)
        self.preComputeAttributeSigns()     #Pre-computing self.attributeSignsUtil; because it's being called 210*5*5 times
        
        while len(tempList) < self.K and len(productList) > 0:      #when len(newList) == 0, you shouldn't enter the loop body
            if adaptiveSelection == True:
                qualities = [(c, self.quality2(c, tempList, previousTopK)) for c in productList]
            else:
                qualities = [(c, self.quality(c, tempList)) for c in productList]
            top = sorted(qualities, key = lambda x: -x[1])[0][0]
            tempList.append(top)
            productList = [p for p in productList if p.id != top.id]    #Removing the 'top' product from newList
        return tempList
           
    def selectTopK(self, unitCritiqueArg = None, firstTime = False, previousSelected = None):
        ''''THIS FUNCTION'S ONLY TASK IS TO SET THE VARIABLE SELF.TOPK'''
        '''Argument firstTime is True if selectTopK is being called for the first time'''
        '''Argument unitCritiqueArg is not None when the caller is unitCritiqueSelectedStrings()'''
        '''previousTopK argument is set when adaptiveSelectionWithNeutralAttributes is called'''
        
        newList = copy.copy(self.prodList); increaseCyclesByOne = 0     #increaseCyclesByOne is for adaptive selection when one cycle is wasted
        if unitCritiqueArg != None: newList = unitCritiqueArg
        #when unitCritique is selected, you need to some filtering; hence the list is changed
        utilitySortedProducts = [(product, self.utility(product, self.weights)) for product in newList]
        utilitySortedProducts = [x[0] for x in sorted(utilitySortedProducts, key = lambda x: -x[1])]
        #print [x .id for x in self.prodList]
        rank = -1    
        try:
            rank = [x.id for x in utilitySortedProducts].index(self.target)
        except:
            rank = 0            #This means that the product was the reference product in first iteration     
        #print "target Product", self.target, "'s rank =", rank
        
        utilitySortedProducts = utilitySortedProducts[:self.K]
        #print 'topK:', [x.id for x in utilitySortedProducts]
        #if both self.targetproductDoesntAppearInFirstCycle and self.similarProdINFirstCycle are set to true,
        #both the if statements are executed.
        if firstTime == True and self.targetProductDoesntAppearInFirstCycle == True:
            newList = [x for x in self.prodList if x.id != self.target]
            utilities = [(product, self.utility(product, self.weights)) for product in newList]
            self.topK = [x[0] for x in sorted(utilities, key = lambda x: -x[1])[:self.K]]
            if self.similarProdInFirstCycleEnabled == False:
                return rank, increaseCyclesByOne
        
        if firstTime == True and self.similarProdInFirstCycleEnabled == True:
            similarities = [(prod, self.sim(prod, self.initialPreferences)) for prod in newList]
            similarities = sorted(similarities, key = lambda x: -x[1])
            self.topK = [x[0] for x in similarities[:self.K]]
            return rank, increaseCyclesByOne
        
        
        #If one of the firstcycle modifications were true, function would return there itself and wouldn't come down
        
        if self.diversityEnabled == True:   #IMPLEMENT THE Smyth and McClave(2001) Algorithm
            self.topK = self.boundedGreedy(newList)
            return rank, increaseCyclesByOne
        
        
        if self.fractionalDiversityEnabled == True:
            if firstTime == True:
                self.topK = self.boundedGreedy(newList, alreadyExisting=[])
                #print 'First Time == True'
                self.numTopUtilityProds = 2
                return rank, increaseCyclesByOne
            else:
                previousTopKIds = [x.id for x in self.topK]         #self.topK here refers to the topK prods in previous iteration
                selectionIndex = previousTopKIds.index(previousSelected.id)
                #print 'selection Index =', selectionIndex
                if selectionIndex < self.numTopUtilityProds:
                    #Top utility product selected
                    if self.numTopUtilityProds < 4: self.numTopUtilityProds += 1
                else:
                    #Diverse product selected
                    if self.numTopUtilityProds > 1: self.numTopUtilityProds -= 1
                    
                tempList = utilitySortedProducts[:self.numTopUtilityProds]
                #print 'before calling the function: numTopUtilityProds = ', self.numTopUtilityProds
                #print 'before calling the function: len(alreadyExisting) = ', len(self.topK)
                self.topK = self.boundedGreedy(newList, alreadyExisting=tempList)
                #print 'len(self.topK) =', len(self.topK)
            return rank, increaseCyclesByOne
        
        if self.adaptiveSelectionEnabled == True:
            if firstTime == True:
                self.topK = utilitySortedProducts
            else:
                #for further iterations, if user pushes the button "I DON'T LIKE ANY OF THESE COMPOUND CRITIQUES"
                if self.maxCompatible(utilitySortedProducts)[1] < 0.4:         #whatever products we are going to propose in the next iteration will be rejected by user
                    #TODO: increaseCyclesByOne can be 2, 3 and so on. Not just one...
                    self.topK = self.boundedGreedy(newList, adaptiveSelection = True, previousTopK = utilitySortedProducts)                 #diversity here...
                    increaseCyclesByOne = 1
                else:
                    self.topK = utilitySortedProducts      #Normal recommendation.
            return rank, increaseCyclesByOne
        
        if self.adaptiveSelectionWithNeutralAttributesEnabled == True:
            if firstTime == True:
                self.topK = utilitySortedProducts
            else:
                #get the directions
                #if it is all neutral/5 neutral/4 neutral; then give top utiltiy products; else give diverse products
                referenceProd = self.caseBase[self.currentReference]
                self.globalCount += 1.0
                p, n, neu = self.attributeSignsUtil(previousSelected, referenceProd)
                print 'Neutral Attributes =', neu
                total = float(len(self.numericAttrNames))
                self.alpha = (total-len(neu))/total          #value of alpha is changed customly according to situation
                self.topK = self.boundedGreedy(newList)
#                if len(neu) >= 4:
#                    print 'coutn of neutral greater than 4'
#                    self.topK = utilitySortedProducts
#                else:
#                    print 'hello neighbor'
#                    self.globalSum += 1
#                    self.topK = self.boundedGreedy(newList)
            return rank, increaseCyclesByOne
        
        
        if self.highestOverlappingProductsInTopK == True:           #This is only for testing purposes where highest overlapping products come in the topK
            #self.target, self.currentReference
            sortedProducts = [x[0] for x in utilitySortedProducts]
            sortedProducts = [x for x in sortedProducts if x.id != self.target]
            referenceProd = self.caseBase[self.currentReference]
            targetProd = self.caseBase[self.target]
            tempList = []
            for prod in sortedProducts:
                attrDirections = self.direction(prod, referenceProd, targetProd)
                targetAttrDirections = self.direction(targetProd, referenceProd, targetProd)
                overlapDegree = self.overlappingDegree(attrDirections, targetAttrDirections)    
                tempList.append((prod, overlapDegree))
            tempList = sorted(tempList, key = lambda x: -x[1])
            self.topK = [x[0] for x in tempList[:self.K]] 
            return rank, increaseCyclesByOne
            
        self.topK = utilitySortedProducts              #This is with standard MAUT
        return rank, increaseCyclesByOne
        
            
    def critiqueStrings(self, selection):
        '''This function updates weights, calls  selectTopK function'''
        '''sets the currentReference and returns critique strings corresponding to the topK products''' 
        selectedProduct = None; specialProduct = None; selectiveAttributes = None; previousIterMaxCompatibility = 0;#book keeping variable
        previousSelectedProduct = None
        if selection == 'firstTime':
            selectedProduct = self.caseBase[self.currentReference]
            self.weightsList[self.target].append(copy.copy(self.weights))
            self.selectedProductsList.append(copy.copy(selectedProduct))
            
        if selection != 'firstTime':
            selectedProduct = copy.copy(self.topK[selection])
            previousSelectedProduct = copy.copy(self.topK[selection])
            self.selectedProductsList.append(copy.copy(selectedProduct))
            if self.updateWeightsWrtInitPreferences == True:
                specialProduct = copy.copy(self.topK[selection])
                for attr in self.initialPreferences:
                    specialProduct.attr[attr] = self.initialPreferences[attr]      #Creating a pseudo product; so weight updates will be in-line with user initial preferences    
            if self.updateWeightsInTargetsDirection == True:                        #none of the topK products will be chosen here. Target product is selected for wt update
                #specialArg = self.target
                specialProduct = self.caseBase[self.target]
            if self.updateWeightsInLineWithTarget == True:
                reference = self.caseBase[self.currentReference]
                target = self.caseBase[self.target]
                dir1 = self.direction(selectedProduct, reference, target)
                dir2 = self.direction(target, reference, target)
                selectiveAttributes = self.overlappingAttributes(dir1, dir2)
                #print 'dir1:', dir1;
                #print 'dir2:', dir2; print 'selectiveAttributes:', selectiveAttributes
                specialProduct = copy.copy(self.topK[selection])
                specialProduct.attr = {}
                for attr in selectiveAttributes:
                    specialProduct.attr[attr] = target.attr[attr]
            
            if self.averageProductEnabled == True:
                specialProduct = copy.copy(self.caseBase[0])
                for attr in self.numericAttrNames:
                    l = len(self.selectedProductsList)
                    normalizingTerm = sum([2**(i-l) for i in range(l)])
                    specialProduct.attr[attr] = sum([2**(i-l) * x.attr[attr] for i,x in enumerate(self.selectedProductsList)])/normalizingTerm
                    #specialProduct.attr[attr] = sum([x.attr[attr] for x in self.selectedProductsList])/l
                for attr in self.nonNumericAttrNames:
                    valuesSeen = [x.attr[attr] for x in self.selectedProductsList]
                    maxFrequent = sorted(valuesSeen, key = valuesSeen.count)[-1]
                    specialProduct.attr[attr] = maxFrequent
#                attr = 'Price'
#                print "Target Product's Price:", self.caseBase[self.target].attr[attr] 
#                print 'Price List:', [x.attr[attr] for x in self.selectedProductsList]
            self.updateWeights(self.topK, selection, specialProduct, selectiveAttributes)
            self.weightsList[self.target].append(copy.copy(self.weights))
            #print 'appended:', self.weights                
                
            #previousIterMaxCompatibility = self.maxCompatible(self.topK)[1]
            for prod in self.topK:  #Removing previous topK items
                self.prodList = [c for c in self.prodList if c.id != prod.id]
        #print 'Product List Size = ', len(self.prodList)
        for attr in self.numericAttrNames:
            self.critiqueStringDirections[attr] = []
            #print attr,':', (int(self.weights[attr]*1000)/1000.0),
        #print
#        for attr in self.nonNumericAttrNames:
#            print attr,':', self.nonNumericValueDict[attr]
#        print
        rank, increaseByOne = self.selectTopK(firstTime = (selection == 'firstTime'), previousSelected = previousSelectedProduct)     #algorithm for selecting the topK is different in the first iteration
        self.currentReference = selectedProduct.id                                      #Changing the reference product...
        
        #TODO: Reject all products that are being fully dominated by the current product
        #print 'topK =', [x.id for x in self.topK]
        critiqueStringList = [self.critiqueStr(prod1, selectedProduct) for prod1 in self.topK]
        return critiqueStringList, rank, increaseByOne
    
    def updateWeights(self, topK, selection, specialProduct = None, selectiveAttributes = None):
        '''If specialArg is a number, that becomes the selected product; not topK[selection]'''
        '''specialProduct is a modified form of topK[selection], selected by user'''
        '''selectiveAttributes is a list of attributes weights of only which have to be updated'''
        selectedProduct = copy.copy(self.topK[selection])
        if specialProduct != None:
            selectedProduct = copy.copy(specialProduct)
        if selectiveAttributes == None:
            selectiveAttributes = self.numericAttrNames + self.nonNumericAttrNames
        
        weightUpdateFactors, numericUpdateFactors = self.updateWeightsUtil(topK, selection)
        referenceProd = self.caseBase[self.currentReference]
        for attr in self.numericAttrNames:
            if attr not in selectiveAttributes: #do not update the weight of attribute if it's not there in selective attributes
                self.weightIncOrDec[attr] = 0; continue;
                
            if self.notCrossingThreshold(attr, referenceProd.attr[attr], selectedProduct.attr[attr]) and self.neutralDirectionEnabled:
                self.weightIncOrDec[attr] = 0; continue;
            
            if self.additiveUpdatesEnabled == True:
                x = selectedProduct.attr[attr] - referenceProd.attr[attr]
                addFactor = 0.1
                val = addFactor*(x > 0) + (-addFactor)*(x < 0)
                val = -val if attr in self.libAttributes else val
                if val >= 0:
                    self.weights[attr] += addFactor;      #do not add the weights if you want to decrease weights. They will be automatically decreased while normalization. 
                continue;
            
            #Normal case, where multiplicative updates are performed.                
            if self.value(attr, referenceProd.attr[attr]) < self.value(attr, selectedProduct.attr[attr]):
                self.weightIncOrDec[attr] = 1 if weightUpdateFactors[attr] > 1 else 0
                self.weights[attr] *= weightUpdateFactors[attr]
            
#            elif self.value(attr, referenceProd.attr[attr]) == self.value(attr, selectedProduct.attr[attr]):
#                self.weightIncOrDec[attr] = 0
#                #DO NOT CHANGE THE WEIGHT OF THE ATTRIBUTE
#                
            else:
                self.weightIncOrDec[attr] = -1 if weightUpdateFactors[attr] > 1 else 0
                if weightUpdateFactors[attr] > 0:
                    self.weights[attr] /= weightUpdateFactors[attr] 
                

        #Normalizing the weights
        weightSum = sum([self.weights[attr] for attr in self.numericAttrNames])
        for attr in self.numericAttrNames:
            self.weights[attr] /= weightSum
            pass
        
        for attr in self.nonNumericAttrNames:
            if attr not in selectiveAttributes: continue
            attrValue = selectedProduct.attr[attr]    
            addFactor = 0.5                                     #This will be the default addFactor
            for val in self.nonNumericValueDict[attr]:
                self.nonNumericValueDict[attr][val] *= self.nonNumericAttrDenominator[attr]
            if self.weightedMLT == True:
                addFactor = numericUpdateFactors[attr]                  #addFactor can be 0,0.5,1,1.5,2
                #self.globalSum += addFactor                             #some book-keeping being done for statistics in evaluation.py
                # self.globalCount+= 1
            self.nonNumericAttrDenominator[attr] += addFactor           #Increasing denominator by 1
            self.nonNumericValueDict[attr][attrValue] += addFactor      #Increasing the selected product's value by 1.
            for val in self.nonNumericValueDict[attr]:                  #Normalizing the weights back again...
                self.nonNumericValueDict[attr][val] /= self.nonNumericAttrDenominator[attr]
            
                
    def updateWeightsUtil(self, topK, selection):
        '''Determines which attribute weights should actually be updated and which should be not'''
        '''Cases like: "Higher Price present in all critique strings"'''
        '''and "Higher Resolution is chosen over lesser resolution(present in 4 critique strings) etc. are handled'''
        
        #The dictionary critiqueStringDirections must have been filled in the previous iteration itself.
        
#        for attr in self.numericAttrNames:
#            if attr == 'StorageIncluded':
#                print 'Reference Product:', self.caseBase[self.currentReference].attr[attr]
#                print 'topK vals:', [x.attr[attr] for x in topK]
#                print 'selected:', [x.attr[attr] for x in topK][selection]
#                #print 'Attr:', attr, 'Direction:', self.critiqueStringDirections[attr]
#        
        weightUpdateFactors = {}; numericUpdateFactors = {}
        if self.weightedMLT == True:
            for attr in self.nonNumericAttrNames:
                #You can do something here also, where weights of nominal attributes are updated properly
                #Actually, only weights of nominal attributes can be update properly using weightedMLT.
                #We can actually process topK here and selection is already available...
                selectedProd = topK[selection]
                otherAttrVals = [x.attr[attr] for x in topK if x.attr[attr] != selectedProd.attr[attr]]
                updateFactor = len(set(otherAttrVals))/float(self.K-1)
                numericUpdateFactors[attr] = updateFactor
            
            for attr in self.numericAttrNames:
#                selectedProd = topK[selection]
#                otherAttrVals = [x.attr[attr] for x in topK if x.attr[attr] != selectedProd.attr[attr]]
#                updateFactor = len(set(otherAttrVals))/float(self.K-1)
#                weightUpdateFactors[attr] = 3*updateFactor
                weightUpdateFactors[attr] = 2
                #print 'numeric attr wt update =', weightUpdateFactors[attr]
            return weightUpdateFactors, numericUpdateFactors 
            
        if self.selectiveWtUpdateEnabled == False:
            for attr in self.numericAttrNames:
                weightUpdateFactors[attr] = 2
            return weightUpdateFactors, {}
        
        #update factors are returned by util.getUpdateFactor()
        if self.selectiveWtUpdateEnabled == True:
            for attr in self.numericAttrNames:
                directions = self.critiqueStringDirections[attr]
                weightUpdateFactors[attr] = util.getUpdateFactor(directions, selection, attr in self.mibAttributes)
                print 'Attr:', attr, 'Direction:', self.critiqueStringDirections[attr]
                #print 'WeightUpdate  Priority of', attr, ":", weightUpdateFactors[attr]
                 
            return weightUpdateFactors, {}
    
    def unitCritiqueSelectedStrings(self, selection, value, type):
        attr = self.numericAttrNames[selection]
        if type == 'low':
            newList = [prod for prod in self.prodList if prod.attr[attr] < value]
            self.weights[attr] = self.weights[attr]*2 if attr in self.libAttributes else self.weights[attr]/2
        else:
            newList = [prod for prod in self.prodList if prod.attr[attr] > value]
            self.weights[attr] = self.weights[attr]*2 if attr in self.mibAttributes else self.weights[attr]/2
        
        utilities = [(product, self.utility(product, self.weights)) for product in newList]
        #print 'Product list size = ', len(self.prodList)
        #print 'newList size = ', len(newList)
        
        topProduct = sorted(utilities, key = lambda x: -x[1])[0][0]    
        newList = [prod for prod in newList if prod.id != topProduct.id]        #removing the topProduct
        self.currentReference = topProduct.id
        #Removing previous topK items
        for prod in self.topK:
            self.prodList = [c for c in self.prodList if c.id != prod.id]
            newList = [c for c in newList if c.id != prod.id]
        #Here is the chance to eliminate all the other products and reduce the number of interaction cycles
        #self.prodList = newList                                
        for attr in self.numericAttrNames:
            self.critiqueStringDirections[attr] = []
        self.selectTopK(newList)

        #TODO: Reject all products that are being fully dominated by the current product
        #prod2 = [prod for prod in self.prodList if prod.id == self.currentReference][0]
        #print 'Product selected with unit critiques ID = ', self.topK[0].id
        return [self.critiqueStr(prod1, topProduct) for prod1 in self.topK]
    
    
        
    def value(self, attr, value):
        #['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
        #TODO: Modify these value functions later and check performance
        #value functions for non-numeric attributes are there in the dictionary self.nonNumericValueDict 
        if attr == 'Price':
            maxV, minV = self.maxV[attr], self.minV[attr]
            if maxV-minV == 0:
                return 0
            return float(maxV - value)/(maxV - minV)
        
        if attr == 'Resolution':
            maxV, minV = self.maxV[attr], self.minV[attr]
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
        if attr == 'OpticalZoom':
            maxV, minV = self.maxV[attr], self.minV[attr]
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
        if attr == 'DigitalZoom':
            maxV, minV = self.maxV[attr], self.minV[attr]
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
        if attr == 'Weight':
            maxV, minV = self.maxV[attr], self.minV[attr]
            if maxV-minV == 0:
                return 0
            return float(maxV - value)/(maxV - minV)
        
        if attr == 'StorageIncluded':
            maxV, minV = self.maxV[attr], self.minV[attr]
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
    
    def notCrossingThreshold(self, attr, v1, v2):
        #['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
        if v1 == v2:
            return True
        if attr == 'Price':
            return abs(v1-v2) < 0.02*(self.maxV[attr]-self.minV[attr])
        if attr == 'Resolution':
            return abs(v1-v2) < 0.04*(self.maxV[attr]-self.minV[attr])
        if attr == 'Weight':
            return abs(v1-v2) < 0.02*(self.maxV[attr]-self.minV[attr])
        if attr == 'StorageIncluded':
            return abs(v1-v2) < 2
        #PC attributes can come here....
        #attributes are ['ProcessorSpeed', 'Monitor', 'Memory', 'HardDrive', 'Price']
        if attr == 'ProcessorSpeed':
            return abs(v1-v2) < 10
        #Price is already taken care of above....Rest all attributes don't need a criteria here.
        return False 
                
    def attributeSignsUtil(self, current, reference):
        '''Deals only with numeric attributes'''
        #This function is called by two functions "CritiqueSim" and "CritiqueStr"....
        #For "CritiqueStr" function, we need to progressively store the attribute directions of all the topK critique strings
        #Classifies all the numeric attributes into positive, negative and neutral attributes
        #if self.neutralDirectionEnabled == False, then all numeric attributes are classified either as positive or negative attributes
        positiveAttributes = []
        negativeAttributes = []
        neutralAttributes = []
        for attr in self.libAttributes:
            if self.notCrossingThreshold(attr, current.attr[attr], reference.attr[attr]) and self.neutralDirectionEnabled:
                neutralAttributes.append(attr)
            elif current.attr[attr] < reference.attr[attr]:
                positiveAttributes.append(attr)
            else:
                negativeAttributes.append(attr)
                
        for attr in self.mibAttributes:
            if self.notCrossingThreshold(attr, current.attr[attr], reference.attr[attr]) and self.neutralDirectionEnabled:
                neutralAttributes.append(attr)
            elif current.attr[attr] > reference.attr[attr]:
                positiveAttributes.append(attr)
            else:
                negativeAttributes.append(attr)
        
        #For each attribute, self.attrDirection notes down the direction in which attribute values are changing
        for attr in self.numericAttrNames:
            self.attrDirection[attr] = []
        for attr in self.numericAttrNames:
            if attr in positiveAttributes:
                self.attrDirection[attr].append('Positive')
            elif attr in negativeAttributes:
                self.attrDirection[attr].append('Negative')
            else:
                self.attrDirection[attr].append('Neutral')
        
        #if the caller is critiqueStr, you need to store the directions of all topK critiqueStrings.
        #critiqueStringDirections will be reset in every iteration; in critiqueStrings() function..
        if inspect.stack()[1][3] == 'critiqueStr':
            for attr in self.numericAttrNames:
                if attr in positiveAttributes:
                    self.critiqueStringDirections[attr].append('Positive')
                elif attr in negativeAttributes:
                    self.critiqueStringDirections[attr].append('Negative')
                else:
                    self.critiqueStringDirections[attr].append('Neutral')
        
        
        if inspect.stack()[1][3] == 'preComputeAttributeSigns':
            list = []
            for attr in self.numericAttrNames:
                if self.notCrossingThreshold(attr, current.attr[attr], reference.attr[attr]) and self.neutralDirectionEnabled:
                    list.append('Neutral')
                elif current.attr[attr] < reference.attr[attr]:
                    list.append('Less')
                else:
                    list.append('Same')
            return list
        
        return positiveAttributes, negativeAttributes, neutralAttributes
    
    def critiqueStr(self, current, reference):
        p, n, neu = self.attributeSignsUtil(current, reference)
        positiveAttributes = p
        negativeAttributes = n
        neutralAttributes = neu
         
        positiveString = ''
        negativeString = 'But '
        
        #['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
        for attr in self.libAttributes:
            if attr in positiveAttributes:
                positiveString += 'Lesser ' + attr + ' '
            if attr in negativeAttributes:
                negativeString += 'Higher ' + attr + ' '
            
#        if 'Weight' in positiveAttributes:
#            positiveString += 'Lesser Weight '
#        if 'Weight' in negativeAttributes:
#            negativeString += 'Higher Weight '
#        
        for attr in self.mibAttributes:
            if attr in positiveAttributes:
                positiveString += 'Higher ' + attr + ' '
            if attr in negativeAttributes:
                negativeString += 'Lower ' + attr + ' '
        
#        if 'OpticalZoom' in positiveAttributes:
#            positiveString += 'Higher Optical Zoom  '
#        if 'OpticalZoom' in negativeAttributes:
#            negativeString += 'Lower Optical Zoom '
        
        
        str2 = ''
        if len(positiveAttributes) != 0:
            str2 += positiveString
        if len(positiveAttributes) == 0:
            negativeString = negativeString[4:]     #Removing the 'but' part...
        str2 += '\n'
        if len(negativeAttributes) != 0:
            str2 += negativeString + '\n'
        
        #str2 = 'Higher Resolution, Lesser Price, Higher Digital Zoom\n But Lower Optical Zoom, Higher Zoom'
        str2 = str2 + 'Product ID:' + str(current.id)
        #str2 = str2 + '\n' + str(current)
        return str2
    
    def mostSimilar(self, baseProduct):
        #Returns the product that is most similar to the 'baseProduct'
        preferences = {}
        for attr in self.attrNames:
            preferences[attr] = baseProduct.attr[attr]
                
        newList = [prod for prod in self.prodList if prod.id != baseProduct.id]         #Removing base Product from the list..
        similarities = [(prod, self.sim(prod, preferences)) for prod in newList]
        similarities = sorted(similarities, key = lambda x: -x[1])
        #print similarities[:5]
        topProduct = similarities[0][0]
        #print 'similarity = ', similarities[0][1]
        return topProduct
    
    def stuffForUtilitiesFrame(self):
        '''Return ID, utility and overlap, all as strings; limit the floating point numbers to only 3 decimal places'''
        #TODO: This wont be correct if critique diversity is enabled.... 
        utilities = [(product, self.utility(product, self.weights)) for product in self.prodList]
        utilities = sorted(utilities, key = lambda x: -x[1])
        newList = [x[0] for x in utilities]
        referenceProd = self.caseBase[self.currentReference]
        targetProd = self.caseBase[self.target]
        overlapDegList = []
        
        for prod in newList:
            attrDirections = self.direction(prod, referenceProd, targetProd)
            targetAttrDirections = self.direction(targetProd, referenceProd, targetProd)
            overlapDegree = self.overlappingDegree(attrDirections, targetAttrDirections)    
            overlapDegList.append(overlapDegree)
        
        for i in range(len(utilities)):
            utilities[i] = [str(utilities[i][0].id), str(int(1000*utilities[i][1])/1000.0), str(int(100*overlapDegList[i])/100.0)]
        #utilities = sorted(utilities, key = lambda x: -float(x[2]))
        return utilities
                
    def direction(self, prod, reference, target):
        #Returns the dicitionary {'Price': 'less', 'Resolution': 'more'} indicating directions
        d = {}
        for attr in self.numericAttrNames:
            if prod.attr[attr] < reference.attr[attr]:
                d[attr] = 'less'
            elif prod.attr[attr] > reference.attr[attr]:
                d[attr] = 'more'
            else:
                d[attr] = 'same'
        for attr in self.nonNumericAttrNames:
            d[attr] = 1 if prod.attr[attr] == target.attr[attr] else 0
        return d
    
    def overlappingAttributes(self, direction1, direction2):
        '''direction1 and direction2 are two dictionaries..'''
        '''Returns a list of overlapping attributes'''
        overlapping = []
        for attr in self.numericAttrNames:
            if direction1[attr] == direction2[attr]:
                overlapping.append(attr)
        for attr in self.nonNumericAttrNames:
            if direction1[attr] == direction2[attr]:
                overlapping.append(attr)
        return overlapping


    def overlappingDegree(self, direction1, direction2, numericOnly = False):
        '''direction1 and direction2 are two dictionaries..'''
        '''Returns the extent of overlap'''
        '''Returns overlap between numeric attributes if 'numericOnly' is true'''
        total = len(direction1)
        overlapping1 = overlapping2 = 0;
        for attr in self.numericAttrNames:
            if direction1[attr] == direction2[attr]:
                overlapping1 += 1
        for attr in self.nonNumericAttrNames:
            if direction1[attr] == direction2[attr]:
                overlapping2 += 1
#        #print 'Overlap Ratio:', float(overlapping)/total
        if numericOnly == True:
            return float(overlapping1)/len(self.numericAttrNames)
        return float(overlapping1 + overlapping2)/total
    
    def maxCompatible(self, products):
        #Return the indices of those products whose critique strings are compatible with target
        #Keep a threshold of atleast 4 out of 6 attributes should be compatible..
        l = [];
        reference = self.caseBase[self.currentReference]
        for i, prod in enumerate(products):
            maxDegree = -1
            self.targets = [self.caseBase[self.target]]
            for target in self.targets:    
                attrDirections = self.direction(prod, reference, target)
                targetAttrDirections = self.direction(target, reference, target)
                overlapDegree = self.overlappingDegree(attrDirections, targetAttrDirections)
                numericAttrOverlapDegree = self.overlappingDegree(attrDirections, targetAttrDirections, numericOnly = True)
                #print 'Compound critique product ID = ', prod.id
                #print 'attrDirections:', attrDirections
                #print 'targetAttrDirections: ', targetAttrDirections
                if overlapDegree > maxDegree:
                    maxDegree = overlapDegree
            l.append((i, maxDegree, numericAttrOverlapDegree))
            
        l = sorted(l, key = lambda x: -x[1])
        #print self.direction(products[l[0][0]], reference, target)     #maxCompatible product's directions
        #print self.direction(target, reference, target)             #target product's directions
        l2 = [(products[i].id, int(j*100)/100.0) for i, j, k in l]
        #print l2
        #print 'maxCompatible Product ID =', l2[0][0]
        if l[0][0] > 4:
            print 'WTF. Index is greater than 4. Exiting'
            exit()
        return l[0]
    
    def predictProducts(self):
        #You shouldn't assume the user's strategy. You should only propose stuff based on what user has actually selected.
        #So you can't narrow down the search space assuming the strategy of max critique overlap
        referenceProd = self.caseBase[self.currentReference]
        
        for targetProd in self.prodList:
            #we can narrow down the search here..????
            #we can narrow down to 20 products
            
            for prod in self.topK:
                attrDirections = self.direction(prod, referenceProd, targetProd)
                targetAttrDirections = self.direction(targetProd, referenceProd, targetProd)
                overlapDegree = self.overlappingDegree(attrDirections, targetAttrDirections)    
            
    
    
Recommender()