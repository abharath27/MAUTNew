import random, itertools
domain = 'PC'
domain = 'Camera'
if domain == 'Camera':
    attrNames = ['Manufacturer', 'Price', 'Format', 'Resolution', 'OpticalZoom', 'DigitalZoom',\
                 'Weight', 'StorageType', 'StorageIncluded']
if domain == 'PC':
    attrNames = ['Manufacturer', 'ProcessorSpeed',\
                'Monitor', 'Type', 'Memory', 'HardDrive', 'Price']

if domain == 'Cars':
    attrNames = []

g = open('q1.txt', 'w'); lines = []
for i in range(10000):
    #numQueryAttributes = random.choice([1,3,5])
    numQueryAttributes = 1
    initialPrefAttributes = random.choice(list(itertools.combinations(attrNames, numQueryAttributes)))
    lines.append(' '.join(initialPrefAttributes) + '\n')
g.writelines(lines)
