class PC:
    def __init__(self, id, line):
        self.id = id
        self.attrNames = ['Manufacturer', 'ProcessorType', 'ProcessorSpeed',\
                           'Monitor', 'Type', 'Memory', 'HardDrive', 'Price']
        self.attr = {}  #Contains attribute values
        for x,y in zip(line, self.attrNames):
            self.attr[y] = x 
    def __str__(self):
        string = self.attr['Manufacturer'] + '\n'
        string += 'Configuration: ' + 'Processor: ' + self.attr['ProcessorType']
        string += 'Speed: ' + str(self.attr['ProcessorSpeed']) + 'MHz'
        string += 'Screen Size: ' + str(self.attr['Monitor']) + 'Inches'
        string += 'Main Memory: ' + str(self.attr['Memory']) + 'MB'
        string += 'Hard Drive: ' + str(self.attr['HardDrive']) + 'GB'
        string += 'Price:$ ' + str(self.attr['Price'])
        return string
    
def readList():        
    productList = []
    lines = open('PC.csv').read().split('\r')[1:]
    for id, line in enumerate(lines):
        line = line.split(',')[1:]
        for i in range(len(line)):
            try:
                line[i] = float(line[i])
            except:
                pass
        
        #print line
        productList.append(PC(id, line))
    return productList
