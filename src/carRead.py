class Car:
    def __init__(self, id, line):
        self.id = id
        self.attrNames = ['Manufacturer', 'Model', 'Body',\
                           'Price', 'Miles', 'Power', 'Speed', 'CCM', 'Zip']
        self.attr = {}  #Contains attribute values
        for x,y in zip(line, self.attrNames):
            self.attr[y] = x 
    def __str__(self):
        string = self.attr['Manufacturer'] + self.attr['Model'] + '\n'
        string += 'Body:' + self.attr['Body']
        string += 'Price: $' + str(self.attr['Price'])
        string += 'Miles:' + str(self.attr['Miles'])
        string += 'Power:' + str(self.attr['Power']) + "HP "
        string += 'CCM:' + str(self.attr['CCM'])
        string += 'ZIP: ' + str(self.attr['Zip'])
        return string
    
def readList():        
    productList = []
    lines = open('cars.csv').read().split('\r')[1:]
    for id, line in enumerate(lines):
        line = line.split(',')[1:]
        for i in range(len(line)):
            try:
                line[i] = float(line[i])
            except:
                pass
        
        #print line
        productList.append(Car(id, line))
    return productList

#readList()