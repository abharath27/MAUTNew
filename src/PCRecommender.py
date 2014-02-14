from recommender import *
import PCRead

class PCRecommender(Recommender):
    def __init__(self):
        self.attrNames = ['Manufacturer', 'ProcessorType', 'ProcessorSpeed',\
                           'Monitor', 'Type', 'Memory', 'HardDrive', 'Price']
        self.numericAttrNames = ['ProcessorSpeed', 'Monitor', 'Memory', 'HardDrive', 'Price']
        self.nonNumericAttrNames = ['Manufacturer', 'ProcessorType', 'Type']
        self.libAttributes = ['Price']
        self.mibAttributes = ['ProcessorSpeed', 'Monitor', 'Memory', 'HardDrive']
        self.prodList = PCRead.readList()
        self.caseBase = [copy.copy(x) for x in self.prodList]
        self.initializeOtherVars()
    
    def value(self, attr, value):
        #['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
        #TODO: Modify these value functions later and check performance 
        if attr in self.libAttributes:
            maxV, minV = self.maxV[attr], self.minV[attr]
            if maxV-minV == 0:
                return 0
            return float(maxV - value)/(maxV - minV)
        
        if attr in self.mibAttributes:
            maxV, minV = self.maxV[attr], self.minV[attr]
            if maxV-minV == 0:
                return 0
            return float(value - minV)/(maxV - minV)
        
        if attr in self.nonNumericAttrNames:
            return 0

#These three functions need to over-ridden(DONE)
#value(done), notCrossingThreshold(this is only required for interface), critiqueStr(even this is for interface only)

test = PCRecommender()
