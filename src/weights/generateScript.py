attrNames = ['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
print "set term 'pbm'"
for num in range(172):
    string = 'plot '
    for i in range(len(attrNames)):
        string += "'" + str(num) + ".txt' " + "using " + str(i+1) +   " title '" + attrNames[i] +  "' with linespoints"
        if i != len(attrNames)-1:
            string += ','
    print "set output '" + str(num) + ".pbm'"
    print string
