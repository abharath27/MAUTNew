import first, copy, util, inspect


class Recommender:
    def __init__(self):
        self.attrNames = ['Manufacturer', 'Model', 'Price', 'Format', \
                          'Resolution', 'OpticalZoom', 'DigitalZoom',\
                           'Weight', 'StorageType', 'StorageIncluded']
        self.numericAttrNames = ['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
        self.nonNumericAttrNames = ['Manufacturer', 'Format', 'StorageType']
        self.libAttributes = ['Price', 'Weight']
        self.mibAttributes = ['Resolution', 'OpticalZoom', 'DigitalZoom', 'StorageIncluded']
        self.resetWeights()
        self.preferredValues = dict([(attr, None) for attr in self.attrNames])
        self.prodList = first.readList()
        self.caseBase = copy.copy(self.prodList)        #caseBase is unchanging. Items are added
        self.K = 5                                      #and deleted from prodList
        self.currentReference = -1
        self.topK = [None]*self.K
        
        #book-keeping attributes
        self.attrDirection = {}
        self.unitAttrPreferences = {}
        self.critiqueStringDirections = {}
        self.utilities = None
        self.weightIncOrDec = dict([(attr, None) for attr in self.attrNames])   #To let the interface know
        self.preComputedAttrSigns = {}
                                                        #whether an attr weight is decreased or increased
        self.diversityEnabled = False                   #Diversity is enabled 'True' in the evaluator
        self.selectiveWtUpdateEnabled = True            #Enable selective weight updation....
        self.neutralDirectionEnabled = True
        
        
    def resetWeights(self):
        self.weights = dict([(attr, 1.0/(len(self.attrNames)-1)) for attr in self.attrNames])
        #self.weights['Price'] = 10
        #self.weights['Resolution'] = 5
        #self.weights['Weight'] = 5
    
    def printMaxMinValues(self):
        for attr in self.numericAttrNames:
            priceList = sorted([prod.attr[attr] for prod in self.prodList])
            #print attr
            #print priceList[:5], priceList[-5:]
            #print max(priceList), min(priceList), '\n'
            
    #MODIFY THE UTILITY AND THE VALUE FUNCTION FOR THE NOMINAL ATTRIBUTES.....
    def utility(self, product, weights):
        retVal = 0
        for attr in self.attrNames:
            retVal += self.weights[attr] * self.value(attr, product.attr[attr])
        return retVal
    
    def sim(self, product, preferences):
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
        #Return the most similar product...
        #print 'Preferences = ', preferences
        similarities = [(prod, self.sim(prod, preferences)) for prod in self.prodList]
        similarities = sorted(similarities, key = lambda x: -x[1])
        #print similarities[:5]
        topProduct = similarities[0][0]
        self.currentReference = topProduct.id
        #print 'First Product Selected = ', topProduct.id
        if specialArg != None:          #'specialArg'th product is the current reference
            self.currentReference = specialArg
        
        for attr in self.attrNames:
            self.preferredValues[attr] = self.caseBase[self.currentReference].attr[attr]
        
        #NOT REMOVING THE FIRST PRODUCT, SINCE IT IS THE TARGET TO BE REACHED
        #ACCORDING TO THE NEW SCHEME...
        for i in range(len(self.prodList)):
            if self.prodList[i].id == self.currentReference:
                #self.prodList.remove(self.prodList[i])
                break
    
    def preComputeAttributeSigns(self):
        reference = self.caseBase[self.currentReference]
        for prod in self.caseBase:
            self.preComputedAttrSigns[prod.id] = self.attributeSignsUtil(prod, reference)
    
    def critiqueSim(self, prod1, prod2):
        #self.precomputedAttrSigns is already set before calling this function
        p1, n1, ne1 = self.preComputedAttrSigns[prod1.id]
        p2, n2, ne2 = self.preComputedAttrSigns[prod2.id]
        overlap = len(list(set(p1).intersection(set(p2))) + list(set(n1).intersection(set(n2))) + list(set(ne1).intersection(set(ne2))))
        overlap /= float(len(p1 + n1 + ne1))
        
        return overlap
    
    def quality(self, c, P):
        alpha = 0.5
        retVal = alpha*self.utility(c, self.weights)
        #diversity(c, P) = \sum(1-sim(c, Ci))/n
        diversity = 0
        for prod in P:
            diversity += (1-self.critiqueSim(c, prod))
        if len(P) != 0:
            diversity /= len(P)     #Normalizing it to one
        retVal += (1-alpha) * diversity
        return retVal 
        
    def selectTopK(self, unitCritiqueArg = None):
        #THIS FUNCTION SETS THE VARIABLE SELF.TOPK
        newList = copy.copy(self.prodList)
        if unitCritiqueArg != None: newList = unitCritiqueArg
        #when unitCritique is selected, you need to some filtering; hence the list is changed
        self.utilities = [(product, self.utility(product, self.weights)) for product in newList]
        self.utilities = sorted(self.utilities, key = lambda x: -x[1])    
            
        if self.diversityEnabled == False:
            self.topK = [x[0] for x in self.utilities[:self.K]]              #Getting only the products and ignoring utilities
        if self.diversityEnabled == True:
            #IMPLEMENT THE Smyth and McClave(2001) Algorithm
            #Quality(c,P) = a*utility(c) + (1-a)*(diversity(c,P))
            tempList = []   #This will hold the topK products found so far
            #Pre-computing self.attributeSignsUtil; because it's being called 210*5*5 times
            self.preComputeAttributeSigns()
            while len(tempList) < self.K:
                qualities = [(c, self.quality(c, tempList)) for c in newList]
                top = sorted(qualities, key = lambda x: -x[1])[0][0]
                tempList.append(top)
                newList = [p for p in newList if p.id != top.id]    #Removing the 'top' product from newList
            
            self.topK = tempList
    def critiqueStrings(self, selection):
        '''This function updates weights, calls  selectTopK function'''
        '''sets the currentReference and returns critique strings corresponding to the topK products''' 
        #return the current recommendation product also...
        #return critique strings corresponding to the top K products...
        
        selectedProduct = ''
        if selection == 'firstTime':
            selectedProduct = [prod for prod in self.caseBase if prod.id == self.currentReference][0]
            
        if selection != 'firstTime':
            selectedProduct = copy.copy(self.topK[selection])
            self.updateWeights(self.topK, selection)
            self.currentReference = selectedProduct.id  #Changing the reference product...                
            for attr in self.weights:
                #print attr,':', (int(self.weights[attr]*1000)/1000.0),
                pass
            
            for attr in self.numericAttrNames:
                self.preferredValues[attr] = selectedProduct.attr[attr]  #Changing the preferred values for all attr...
            #Removing previous topK items
            for prod in self.topK:
                self.prodList = [c for c in self.prodList if c.id != prod.id]
        #print 'Product List Size = ', len(self.prodList)
        
        for attr in self.numericAttrNames:
            self.critiqueStringDirections[attr] = []
        self.selectTopK()
#        print '==============='
#        print [x.id for x in self.topK]
#        print '==============='

        #TODO: Reject all products that are being fully dominated by the current product
        #prod2 = [prod for prod in self.prodList if prod.id == self.currentReference][0]
        critiqueStringList = [self.critiqueStr(prod1, selectedProduct) for prod1 in self.topK]
        return critiqueStringList
    
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
        for attr in self.numericAttrNames:
            self.preferredValues[attr] = topProduct.attr[attr]  #Changing the preferred values for all attr...
        #Here is the chance to eliminate all the other products and reduce the number of interaction cycles
        #self.prodList = newList                                
        for attr in self.numericAttrNames:
            self.critiqueStringDirections[attr] = []
        self.selectTopK(newList)

        #TODO: Reject all products that are being fully dominated by the current product
        #prod2 = [prod for prod in self.prodList if prod.id == self.currentReference][0]
        #print 'Product selected with unit critiques ID = ', self.topK[0].id
        return [self.critiqueStr(prod1, topProduct) for prod1 in self.topK]
    
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
        
        #TODO: include nominal attributes also for adjusting priorities during weight updation.
        for attr in self.numericAttrNames:
            weightUpdateFactors[attr] = None
            directions = self.critiqueStringDirections[attr]
            if util.allSame(directions):
                weightUpdateFactors[attr] = 1
                continue
            
            if directions[selection] == 'Neutral':
                #TODO: Check this if anything better can be done than just setting the updateFa
                weightUpdateFactors[attr] = 1
                continue
            if abs(directions.count('Positive') - directions.count('Negative')) == 3:
                #if selected product attr's direction is equal to less frequent direction, update it's weight by factor of 4
                #print 'Attr', attr, 'entered here'
                if directions.count(directions[selection]) == min(directions.count('Positive'), directions.count('Negative')):
                    weightUpdateFactors[attr] = 4
                    continue
            #In all other cases, multiply the weight by 2.
            weightUpdateFactors[attr] = 2
            
        
        for attr in self.numericAttrNames:
            #print 'Attr:', attr, 'Direction:', self.critiqueStringDirections[attr]
            #print 'WeightUpdate  Priority of', attr, ":", weightUpdateFactors[attr]
            pass
        return weightUpdateFactors
    
    def updateWeights(self, topK, selection):
        selectedProduct = copy.copy(self.topK[selection])
        weightUpdateFactors = self.updateWeightsUtil(topK, selection)
        #print weightUpdateFactors 
        for attr in self.numericAttrNames:
            if self.notCrossingThreshold(attr, self.preferredValues[attr], selectedProduct.attr[attr]) and self.neutralDirectionEnabled:
                self.weightIncOrDec[attr] = 0
                continue
                                
            if self.value(attr, self.preferredValues[attr]) < self.value(attr, selectedProduct.attr[attr]):
                self.weights[attr] *= weightUpdateFactors[attr]
                if weightUpdateFactors[attr] > 1:
                    #print 'Increasing weight of the attribute:', attr
                    self.weightIncOrDec[attr] = 1
                
            else:
                self.weights[attr] /= weightUpdateFactors[attr]
                if weightUpdateFactors[attr] > 1:
                    #print 'Decreasing weight of the attribute:', attr
                    self.weightIncOrDec[attr] = -1
            
            if weightUpdateFactors[attr] == 1:
                #print 'Weight Remains same for attribute:', attr
                self.weightIncOrDec[attr] = 0
                
        for attr in self.nonNumericAttrNames:
            '''THE WEIGHTS OF NOMINAL ATTR SET TO ZERO. NOT TO BE USED IN THE GUI..THIS IS ONLY FOR OFFLINE EVAL'''
            self.weights[attr] = 0          
            if self.preferredValues[attr] == selectedProduct.attr[attr]:
                self.weightIncOrDec[attr] = 1
                #self.weights[attr] *= 2     #If the selected product has the same attribute value 
                                            #as the preferred value, increasing the weight will 
                                            #more likely give same attr as top products
            else:
                self.weightIncOrDec[attr] = -1
                #self.weights[attr] = 1.0/9  #Resetting the weight to default
        #Normalizing the weights
        weightSum = sum([self.weights[attr] for attr in self.numericAttrNames + self.nonNumericAttrNames])
        for attr in self.numericAttrNames + self.nonNumericAttrNames:
            self.weights[attr] /= weightSum
                
    def value(self, attr, value):
        #['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
        #TODO: Modify these value functions later and check performance 
        if attr == 'Price':
            priceList = [prod.attr['Price'] for prod in self.prodList]
            maxV, minV = max(priceList), min(priceList)
            if maxV-minV == 0:
                return 0
            return float(maxV - value)/(maxV - minV)
        
        if attr == 'Resolution':
            priceList = [prod.attr['Resolution'] for prod in self.prodList]
            maxV, minV = max(priceList), min(priceList)
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
        if attr == 'OpticalZoom':
            priceList = [prod.attr['Price'] for prod in self.prodList]
            maxV, minV = max(priceList), min(priceList)
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
        if attr == 'DigitalZoom':
            priceList = [prod.attr['DigitalZoom'] for prod in self.prodList]
            maxV, minV = max(priceList), min(priceList)
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
        if attr == 'Weight':
            priceList = [prod.attr['Weight'] for prod in self.prodList]
            maxV, minV = max(priceList), min(priceList)
            if maxV-minV == 0:
                return 0
            return float(maxV - value)/(maxV - minV)
        
        if attr == 'StorageIncluded':
            priceList = [prod.attr['StorageIncluded'] for prod in self.prodList]
            maxV, minV = max(priceList), min(priceList)
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
        #TODO: Fill these value functions up...
        if attr == 'Model':
            return 0
        
        if attr == 'Manufacturer':
            return 0
        
        if attr == 'StorageType':
            return 0
        
        if attr == 'Format':
            return 0
    
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
        if 'Price' in positiveAttributes:
            positiveString += 'Lesser Price '
        if 'Price' in negativeAttributes:
            negativeString += 'Higher Price '
        
        if 'Resolution' in positiveAttributes:
            positiveString += 'Higher Resolution '
        if 'Resolution' in negativeAttributes:
            negativeString += 'Lower Resolution '
        
        if 'OpticalZoom' in positiveAttributes:
            positiveString += 'Higher Optical Zoom  '
        if 'OpticalZoom' in negativeAttributes:
            negativeString += 'Lower Optical Zoom '
        
        if 'DigitalZoom' in positiveAttributes:
            positiveString += 'Higher Digital Zoom  '
        if 'DigitalZoom' in negativeAttributes:
            negativeString += 'Lower Digital Zoom '
        
        if 'StorageIncluded' in positiveAttributes:
            positiveString += 'Higher Storage '
        if 'StorageIncluded' in negativeAttributes:
            negativeString += 'Lower Storage '
        
        if 'Weight' in positiveAttributes:
            positiveString += 'Lesser Weight '
        if 'Weight' in negativeAttributes:
            negativeString += 'Higher Weight '
        
        str2 = ''
        if len(positiveAttributes) != 0:
            str2 += positiveString
        if len(positiveAttributes) == 0:
            negativeString = negativeString[4:]     #Removing the 'but' part...
        str2 += '\n'
        if len(negativeAttributes) != 0:
            str2 += negativeString
        
        str2 = str2 + '\n Product ID:' + str(current.id)
        product = current
        string = product.attr['Manufacturer'] + ' '
        string = string + product.attr['Model'] + '\n'
        string = string + 'Configuration: ' + str(product.attr['Resolution']) + 'MP,  ' \
           + str(product.attr['OpticalZoom']) + 'x Optical Zoom,  ' + str(product.attr['Weight']) + 'gm,  ' \
            + str(product.attr['StorageIncluded']) + 'MB Storage\n'
        
        string += 'Price: ' + str(product.attr['Price'])
        str2 = str2 + '\n' + string
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
    
Recommender()