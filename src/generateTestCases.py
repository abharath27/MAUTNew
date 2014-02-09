import random, itertools
domain = 'Camera'
if domain == 'Camera':
    attrNames = ['Manufacturer', 'Price', 'Format', 'Resolution', 'OpticalZoom', 'DigitalZoom',\
                 'Weight', 'StorageType', 'StorageIncluded']
if domain == 'PC':
    attrNames = []

if domain == 'Cars':
    attrNames = []

g = open('queries.txt', 'w'); lines = []
for i in range(4000):
    numQueryAttributes = random.choice([1,3,5])
    initialPrefAttributes = random.choice(list(itertools.combinations(attrNames, numQueryAttributes)))
    lines.append(' '.join(initialPrefAttributes) + '\n')
g.writelines(lines)