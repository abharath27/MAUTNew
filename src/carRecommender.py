from recommender import *
import carRead

class CarRecommender(Recommender):
    def __init__(self):
        self.attrNames = ['Manufacturer', 'Body','Price', 'Miles', \
                          'Power', 'Speed', 'CCM', 'Zip']
        self.numericAttrNames = ['Price','Miles', 'Power', 'Speed', 'CCM', 'Zip']
        self.nonNumericAttrNames = ['Manufacturer', 'Body']
        self.libAttributes = ['Price']
        self.mibAttributes = ['Miles', 'Power', 'Speed', 'CCM', 'Zip']      #Clarify whether 'Zip' is LIB or MIB 
        self.prodList = carRead.readList()
        self.caseBase = [copy.copy(x) for x in self.prodList]
        self.initializeOtherVars()
    
    def value(self, attr, value):
        #['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
        #TODO: Modify these value functions later and check performance 
        if attr in self.libAttributes:
            priceList = [prod.attr[attr] for prod in self.prodList]
            maxV, minV = max(priceList), min(priceList)
            if maxV-minV == 0:
                return 0
            return float(maxV - value)/(maxV - minV)
        
        if attr in self.mibAttributes:
            priceList = [prod.attr[attr] for prod in self.prodList]
            maxV, minV = max(priceList), min(priceList)
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
        if attr in self.nonNumericAttrNames:
            return 0
