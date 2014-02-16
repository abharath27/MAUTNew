class Camera:
    def __init__(self, id, line):
        self.id = id
        self.attrNames = ['Manufacturer', 'Price', 'Format', \
                          'Resolution', 'OpticalZoom', 'DigitalZoom',\
                           'Weight', 'StorageType', 'StorageIncluded']
        self.attr = {}  #Contains attribute values
        for x,y in zip(line, self.attrNames):
            self.attr[y] = x 
    def __str__(self):
        string = '\n' + self.attr['Manufacturer'] + ' '
        string = string + 'Configuration: ' + str(self.attr['Resolution']) + 'MP,  ' \
           + str(self.attr['OpticalZoom']) + 'x Optical Zoom,  ' + str(self.attr['Weight']) + 'gm,  ' \
            + str(self.attr['StorageIncluded']) + 'MB Storage\n'
        
        string += 'Price: ' + str(self.attr['Price'])
        return string
    
    
def readList():        
    selfList = []
    lines = open('CameraTrimmed.csv').read().split('\r')[1:]
    for id, line in enumerate(lines):
        line = line.split(',')[1:]
        for i in range(len(line)):
            try:
                line[i] = float(line[i])
            except:
                pass
        
        #print line
        selfList.append(Camera(id, line))
    return selfList

#print readList()[0].attr