class Product:
    def __init__(self, id, line):
        self.id = id
        self.attrNames = ['Manufacturer', 'Model', 'Price', 'Format', \
                          'Resolution', 'OpticalZoom', 'DigitalZoom',\
                           'Weight', 'StorageType', 'StorageIncluded']
        self.attr = {}  #Contains attribute values
        for x,y in zip(line, self.attrNames):
            self.attr[y] = x 
    def __str__(self):
        return str(self.attr)
    
def readList():        
    productList = []
    lines = open('Camera2.csv').read().split('\r')[1:]
    for id, line in enumerate(lines):
        line = line.split(',')[1:]
        for i in range(len(line)):
            try:
                line[i] = float(line[i])
            except:
                pass
        
        #print line
        productList.append(Product(id, line))
    return productList