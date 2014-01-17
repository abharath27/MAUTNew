import first, itertools, copy
caseBase = first.readList()

attrNames = ['Manufacturer', 'Price', 'Format', 'Resolution', 'OpticalZoom',\
              'DigitalZoom', 'Weight', 'StorageType', 'StorageIncluded']
attrPairs = list(itertools.combinations(attrNames, 2))
dictionary = {}

def equivalentExcept(prod1, prod2, pair):
    for attr in attrNames:
        if attr not in pair:
            if prod1.attr[attr] != prod2.attr[attr]:
                return 0
        if attr in pair:
            if prod1.attr[attr] == prod2.attr[attr]:
                return 0
    return 1

for pair in attrPairs:
    dictionary[pair] = []
    for prod1 in caseBase:
        for prod2 in caseBase:
            if equivalentExcept(prod1, prod2, pair) and prod1.id < prod2.id:
                dictionary[pair].append((prod1, prod2))

for key in dictionary:
    print key
    for productPair in dictionary[key]:
        mainStr = str(productPair[0].id) + ',' + str(productPair[1]. id)
        mainStr += ',' + str(productPair[0].attr[key[0]]) + ';' + str(productPair[0].attr[key[1]])
        mainStr += ',' + str(productPair[1].attr[key[0]]) + ';' + str(productPair[1].attr[key[1]])
        if type(productPair[0].attr[key[1]]) == float:
            mainStr +=',' + (str(productPair[1].attr[key[0]] - productPair[0].attr[key[0]]))
            mainStr +=',' + (str(productPair[1].attr[key[1]] - productPair[0].attr[key[1]])) 
                                                                      
        print mainStr
    print '************\n'