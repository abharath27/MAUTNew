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
        self.resetWeights()
        self.preComputeMaxMinAttrValues()
        self.preferredValues = dict([(attr, None) for attr in self.attrNames])  #Variable 'attrNames' is used only with preferredValues variable
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
        tempUtilities = None
        self.weightIncOrDec = dict([(attr, None) for attr in self.numericAttrNames + self.nonNumericAttrNames])   #To let the interface know
        self.preComputedAttrSigns = {}
        self.nominalAttributesEnabled = True                #In the function 'selectFirstProduct()', self.nonNumericAttrNames = []
        self.neutralDirectionEnabled = True                 #It's set to false during evaluation, neutral direction helps for the proper display of critique strings
        self.selectedProductsList = []                      #It is initialized with the first product selected and every product that is subsequently chosen by user is added.
        self.weightsList = collections.defaultdict(list)
        
        #modifications turn on/off. By default they are turned off. Inheriting class should turn them on.
        self.diversityEnabled = False                       #Diversity should be enabled true
        self.selectiveWtUpdateEnabled = False               #Enable selective weight updation....
        self.similarProdInFirstCycleEnabled = False
        self.targetProductDoesntAppearInFirstCycle = False
        self.highestOverlappingProductsInTopK = False
        self.averageProductEnabled = False
        self.historyEnabled = False
        self.additiveUpdatesEnabled = False
        
        #weight update strategies. Max one of them should be turned on at any moment.
        self.updateWeightsInTargetsDirection = False         #Weights are always updated in the direction of target. Enabled 'True' only for testing purposes
        self.updateWeightsInLineWithTarget = False           #only weights of attributes that are in-line with target are updated
        #above two are hypothetical and won't be used in real experiments.
        self.updateWeightsWrtInitPreferences = False        #This technique successfully works
        
        #sanity check
        numEnabled = self.updateWeightsInLineWithTarget + self.updateWeightsInTargetsDirection + self.updateWeightsWrtInitPreferences
        if numEnabled > 1: print 'More than one weight update technique enabled; exiting;'; exit()
        util.printNotes(self)
        if self.nominalAttributesEnabled == False:
            self.nonNumericAttrNames = []
        
    def resetWeights(self):
        '''resets weights and value functions of numeric, nominal attributes'''
        realAttributes = self.numericAttrNames
        self.weights = dict([(attr, 1.0/(len(realAttributes))) for attr in self.numericAttrNames])
        self.nonNumericValueDict = {}
        for attr in self.nonNumericAttrNames:
            distinctVals = list(set([prod.attr[attr] for prod in self.caseBase]))
            self.nonNumericValueDict[attr] = dict([(val, 1.0/len(distinctVals)) for val in distinctVals])
        self.selectedProductsList = []
    
    def preComputeMaxMinAttrValues(self):
        '''precomputes max and min values of numeric attributes into the dictionary self.maxV and self.minV'''
        self.maxV = {}; self.minV = {}
        for attr in self.numericAttrNames:        
            priceList = [prod.attr[attr] for prod in self.caseBase]
            self.maxV[attr], self.minV[attr] = max(priceList), min(priceList)
            
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
                
        for attr in self.numericAttrNames:
            retVal += self.weights[attr] * self.value(attr, product.attr[attr])
        for attr in self.nonNumericAttrNames:
            retVal += self.nonNumericValueDict[attr][product.attr[attr]]
        return retVal
    
    def sim(self, product, preferences):
        '''Input: dictionary of preferences and product. Output: similarity between the product and preferences'''
        dist = 0
        for attr in preferences:
            if attr in self.numericAttrNames:
                values = [prod.attr[attr] for prod in self.prodList]
                minV, maxV = min(values), max(values)
                dist += (abs((preferences[attr] - product.attr[attr])/(maxV - minV)))
                
            else:   #NOMINAL ATTRIBUTES
                #IDEALLY, there should be a similarity measure defined between different brands...
                if preferences[attr] != product.attr[attr]:
                    dist += 1
        return 1/(1+dist)
    
    
    def selectFirstProduct(self, preferences, specialArg = None):
        '''Removes the first product from self.prodList and sets the variable self.currentReference'''
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
        p1, n1, ne1 = self.preComputedAttrSigns[prod1.id]
        p2, n2, ne2 = self.preComputedAttrSigns[prod2.id]
        overlap = len(list(set(p1).intersection(set(p2))) + list(set(n1).intersection(set(n2))) + list(set(ne1).intersection(set(ne2))))
        overlap /= float(len(p1 + n1 + ne1))
        return overlap
    
    def quality(self, c, P):
        alpha = self.alpha
        retVal = alpha*self.utility(c, self.weights)
        #diversity(c, P) = \sum(1-sim(c, Ci))/n
        diversity = 0
        for prod in P:
            diversity += (1-self.critiqueSim(c, prod))
        if len(P) != 0:
            diversity /= len(P)     #Normalizing it to one
        retVal += (1-alpha) * diversity
        return retVal 
        
    def selectTopK(self, unitCritiqueArg = None, firstTime = False):
        ''''THIS FUNCTION'S ONLY TASK IS TO SET THE VARIABLE SELF.TOPK'''
        '''Argument firstTime is True if selectTopK is being called for the first time'''
        '''Argument unitCritiqueArg is not None when the caller is unitCritiqueSelectedStrings()'''
        newList = copy.copy(self.prodList)
        if unitCritiqueArg != None: newList = unitCritiqueArg
        #when unitCritique is selected, you need to some filtering; hence the list is changed
        tempUtilities = [(product, self.utility(product, self.weights)) for product in newList]
        tempUtilities = sorted(tempUtilities, key = lambda x: -x[1])
        #print [x .id for x in self.prodList]
        rank = -1    
        try:
            rank = [x[0].id for x in tempUtilities].index(self.target)
        except:
            rank = 0            #This means that the product was the reference product in first iteration     
        print "target Product", self.target, "'s rank =", rank
        #if both self.targetproductDoesntAppearInFirstCycle and self.similarProdINFirstCycle are set to true,
        #both the if statements are executed.
        if firstTime == True and self.targetProductDoesntAppearInFirstCycle == True:
            newList = [x for x in self.prodList if x.id != self.target]
            utilities = [(product, self.utility(product, self.weights)) for product in newList]
            self.topK = [x[0] for x in sorted(utilities, key = lambda x: -x[1])[:self.K]]
            if self.similarProdInFirstCycleEnabled == False:
                return rank
        
        if firstTime == True and self.similarProdInFirstCycleEnabled == True:
            similarities = [(prod, self.sim(prod, self.initialPreferences)) for prod in newList]
            similarities = sorted(similarities, key = lambda x: -x[1])
            self.topK = [x[0] for x in similarities[:self.K]]
            return rank
        
        #If one of the firstcycle modifications were true, function would return there itself and wouldn't come down
        
        if self.diversityEnabled == False:                                  #This is the case with standard MAUT
            self.topK = [x[0] for x in tempUtilities[:self.K]]              #Getting only the products and ignoring utilities
            if self.highestOverlappingProductsInTopK == True:
                #self.target, self.currentReference
                sortedProducts = [x[0] for x in tempUtilities]
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
            return rank
        
        if self.diversityEnabled == True:
            #IMPLEMENT THE Smyth and McClave(2001) Algorithm
            #Quality(c,P) = a*utility(c) + (1-a)*(diversity(c,P))
            tempList = []   #This will hold the topK products found so far
            self.preComputeAttributeSigns()     #Pre-computing self.attributeSignsUtil; because it's being called 210*5*5 times
            while len(tempList) < self.K and len(newList) > 0:      #when len(newList) == 0, you shouldn't enter the loop body 
                qualities = [(c, self.quality(c, tempList)) for c in newList]
                top = sorted(qualities, key = lambda x: -x[1])[0][0]
                tempList.append(top)
                newList = [p for p in newList if p.id != top.id]    #Removing the 'top' product from newList
            
            self.topK = tempList
            return rank
            
    def critiqueStrings(self, selection):
        '''This function updates weights, calls  selectTopK function'''
        '''sets the currentReference and returns critique strings corresponding to the topK products''' 
        selectedProduct = None; specialProduct = None; selectiveAttributes = None;
        if selection == 'firstTime':
            selectedProduct = self.caseBase[self.currentReference]
            self.weightsList[self.target].append(copy.copy(self.weights))
            self.selectedProductsList.append(copy.copy(selectedProduct))
            
        if selection != 'firstTime':
            selectedProduct = copy.copy(self.topK[selection])
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
                    specialProduct.attr[attr] = sum([x.attr[attr] for x in self.selectedProductsList])/len(self.selectedProductsList)
                for attr in self.nonNumericAttrNames:
                    valuesSeen = [x.attr[attr] for x in self.selectedProductsList]
                    maxFrequent = sorted(valuesSeen, key = valuesSeen.count)[-1]
                    specialProduct.attr[attr] = maxFrequent
#                attr = 'Price'
#                print "Target Product's Price:", self.caseBase[self.target].attr[attr] 
#                print 'Price List:', [x.attr[attr] for x in self.selectedProductsList]
            self.updateWeights(self.topK, selection, specialProduct, selectiveAttributes)
            self.weightsList[self.target].append(copy.copy(self.weights))
            self.currentReference = selectedProduct.id  #Changing the reference product...                
                
            
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
        rank = self.selectTopK(firstTime = (selection == 'firstTime'))     #algorithm for selecting the topK is different in the first iteration
        #TODO: Reject all products that are being fully dominated by the current product
        critiqueStringList = [self.critiqueStr(prod1, selectedProduct) for prod1 in self.topK]
        return critiqueStringList, rank
    
    def updateWeights(self, topK, selection, specialProduct = None, selectiveAttributes = None):
        '''If specialArg is a number, that becomes the selected product; not topK[selection]'''
        '''specialProduct is a modified form of topK[selection], selected by user'''
        '''selectiveAttributes is a list of attributes weights of only which have to be updated'''
        #TODO:updateWeightsUtil() function should be changed for selective weight updationn with target directions
        selectedProduct = copy.copy(self.topK[selection])
        if specialProduct != None:
            selectedProduct = copy.copy(specialProduct)
        if selectiveAttributes == None:
            selectiveAttributes = self.numericAttrNames + self.nonNumericAttrNames
        
        weightUpdateFactors = self.updateWeightsUtil(topK, selection)
        referenceProd = self.caseBase[self.currentReference]
        for attr in self.numericAttrNames:
            if attr not in selectiveAttributes: #do not update the weight of attribute if it's not there in selective attributes
                self.weightIncOrDec[attr] = 0; continue;
                
            if self.notCrossingThreshold(attr, referenceProd.attr[attr], selectedProduct.attr[attr]) and self.neutralDirectionEnabled:
                self.weightIncOrDec[attr] = 0; continue;
            
            val = (selectedProduct.attr[attr] - referenceProd.attr[attr])/(self.maxV[attr] - self.minV[attr])
            if attr in self.libAttributes:
                val = -val
            if self.additiveUpdatesEnabled == True:
                self.weights[attr] += val; continue;
                            
            if self.value(attr, referenceProd.attr[attr]) < self.value(attr, selectedProduct.attr[attr]):
                self.weightIncOrDec[attr] = 1 if weightUpdateFactors[attr] > 1 else 0
                self.weights[attr] *= weightUpdateFactors[attr]
                
            else:
                self.weightIncOrDec[attr] = -1 if weightUpdateFactors[attr] > 1 else 0
                self.weights[attr] /= weightUpdateFactors[attr]
                

        #Normalizing the weights
        weightSum = sum([self.weights[attr] for attr in self.numericAttrNames])
        for attr in self.numericAttrNames:
            self.weights[attr] /= weightSum
                
        for attr in self.nonNumericAttrNames:
            #selective weight update is not for nominal attributes. It's a little complicated to model this 
            #for nominal attributes          
            if attr not in selectiveAttributes: continue
            attrValue = selectedProduct.attr[attr]
            distinctVals = list(set([prod.attr[attr] for prod in self.caseBase]))
            meanValue = 1.0/len(distinctVals)
            
            #Resetting all other non-numeric attribute values to the mean value, in case the preference 
            #has been changed.
            if self.nonNumericValueDict[attr][attrValue] < meanValue:
                for val in self.nonNumericValueDict[attr]:
                    self.nonNumericValueDict[attr][val] = meanValue
            
            self.nonNumericValueDict[attr][attrValue] *= 2
            normalizingFactor = sum(self.nonNumericValueDict[attr].values())
            for temp in self.nonNumericValueDict[attr]:
                self.nonNumericValueDict[attr][temp] /= normalizingFactor
                
    def updateWeightsUtil(self, topK, selection):
        '''Determines which attribute weights should actually be updated and which should be not'''
        '''Cases like: "Higher Price present in all critique strings"'''
        '''and "Higher Resolution is chosen over lesser resolution(present in 4 critique strings) etc. are handled'''
        
        #The dictionary critiqueStringDirections must have been filled in the previous iteration itself.
        weightUpdateFactors = {}
        if self.selectiveWtUpdateEnabled == False:
            for attr in self.numericAttrNames:
                weightUpdateFactors[attr] = 2
            return weightUpdateFactors
        
        #update factors are returned by util.getUpdateFactor()
        for attr in self.numericAttrNames:
            directions = self.critiqueStringDirections[attr]
            weightUpdateFactors[attr] = util.getUpdateFactor(directions, selection, attr in self.mibAttributes)
            #print 'Attr:', attr, 'Direction:', self.critiqueStringDirections[attr]
            #print 'WeightUpdate  Priority of', attr, ":", weightUpdateFactors[attr]
            
        return weightUpdateFactors
    
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
            return abs(v1-v2) < 10
        if attr == 'Resolution':
            return abs(v1-v2) < 0.2
        if attr == 'Weight':
            return abs(v1-v2) < 10
        if attr == 'StorageIncluded':
            return abs(v1-v2) < 2
        #PC attributes can come here....
        #attributes are ['ProcessorSpeed', 'Monitor', 'Memory', 'HardDrive', 'Price']
        if attr == 'ProcessorSpeed':
            return abs(v1-v2) < 10
        #Price is already taken care of above....Rest all attributes don't need a criteria here.
        return False 
                
    def attributeSignsUtil(self, current, reference):
        #This function is called by two functions "CritiqueSim" and "CritiqueStr"....
        #For "CritiqueStr" function, we need to progressively store the attribute directions of all the topK critique strings
        #Classifies all the numeric attributes into positive, negative and neutral attributes
        #if self.neutralDirectionEnabled == False, then all numeric attributes are classified either as positive or negative attributes
        positiveAttributes = []
        negativeAttributes = []
        neutralAttributes = []
        for attr in self.libAttributes:
            #print 'current = ', current
            if self.notCrossingThreshold(attr, current.attr[attr], reference.attr[attr]) and self.neutralDirectionEnabled:
                neutralAttributes.append(attr)
                continue 
            if current.attr[attr] < reference.attr[attr]:
                positiveAttributes.append(attr)
            else:
                negativeAttributes.append(attr)
                
        for attr in self.mibAttributes:
            if self.notCrossingThreshold(attr, current.attr[attr], reference.attr[attr]) and self.neutralDirectionEnabled:
                neutralAttributes.append(attr)
                continue
            if current.attr[attr] > reference.attr[attr]:
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
            str2 += negativeString
        
        str2 = str2 + '\n Product ID:' + str(current.id)
        str2 = str2 + '\n' + str(current)
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
        t = self.maxCompatible(self.topK)
        print 'topKIds =', [x.id for x in self.topK]
        print 'MaxCompatible:', self.topK[t[0]].id, t[1]
        print 'target =', self.target, 'reference =', self.currentReference
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
        return l[0]
        
Recommender()