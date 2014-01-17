from Tkinter import *
from first import *
from recommender import *

#['Manufacturer', 'Model', 'Price', 'Format', 'Resolution', 'OpticalZoom', 'Digital Zoom', 'Weight', 'StorageType', 'StorageIncluded']
class App:
    def __init__ (self, master):
        self.master = master
        self.recommender = Recommender()   
        self.createUnitCritiqueFrame()
        
    def chooseFirstProduct(self):
        '''This function is invoked when the 'Start' button is clicked'''
        #destroy self.unitCritiqueButton as soon as you enter this method...
        #TODO: Remove the cursor from the text boxes as soon as the "start" button is clicked.
        i = 0; preference = {}
        for attr in self.recommender.numericAttrNames:
            if self.textBoxList[i].get() != '':
                preference[attr] = float(self.textBoxList[i].get())
            i += 1
        self.recommender.selectFirstProduct(preference, 43) #pass second argument if you want a particular product to become the reference    
        currentProd = [prod for prod in self.recommender.caseBase if prod.id == self.recommender.currentReference][0]
        self.displayProduct(currentProd)
        self.createCompoundCritiqueFrame()
        
        l = self.recommender.critiqueStrings(selection = 'firstTime')
        for i, k in enumerate(l):
            self.compoundCritiqueL[i].insert(END, k); i+= 1
        self.createUtilitiesFrame()
        self.createWeightBox()
        self.createWeightStatusBox()
        self.updateCompoundCritiqueBoxes()
        self.updateWeightBox()
        
    def createWeightBox(self):
        self.weightBox = Text(self.master, font= 'Helvetica', wrap = WORD, width = 25, height = 7,\
                         borderwidth = 4, relief = GROOVE)
        self.weightBox.grid(row = 0, column = 1)
        
    def updateWeightBox(self):
        self.weightBox.delete(1.0, END)
        tempStr = 'Weights:\n'
        for attr in self.recommender.numericAttrNames + self.recommender.nonNumericAttrNames:
            tempStr += attr + ' : ' + str(int(1000*self.recommender.weights[attr])/1000.0) + '\n'
        self.weightBox.insert(END, tempStr)
    
    def createWeightStatusBox(self):
        self.weightStatusBox = Text(self.master, font= 'Helvetica', wrap = WORD, width = 25, height = 7,\
                         borderwidth = 4, relief = GROOVE)
        self.weightStatusBox.grid(row = 0, column = 2)
    
    def updateWeightStatusBox(self):
        self.weightStatusBox.delete(1.0, END)
        tempStr = "Direction of Weight Change:\n"
        increasedAttr = []; decreasedAttr = []; neutralAttr = [];
        #TODO:Include non-numeric attributes also...
        for attr in self.recommender.numericAttrNames: 
            if self.recommender.weightIncOrDec[attr] == 1:
                increasedAttr.append(attr)
            if self.recommender.weightIncOrDec[attr] == -1:
                decreasedAttr.append(attr)
            if self.recommender.weightIncOrDec[attr] == 0:
                neutralAttr.append(attr)
        if len(increasedAttr) != 0:
            tempStr += "\nWeight Increased For:\n"
        for attr in increasedAttr:
            tempStr += attr + '\n'
            
        if len(decreasedAttr) != 0:
            tempStr += "\nWeight Decreased For:\n"
        for attr in decreasedAttr:
            tempStr += attr + '\n'
            
        if len(neutralAttr) != 0:
            tempStr += "\nWeight Remains Same For:\n"
        for attr in neutralAttr:
            tempStr += attr + '\n'
        
        self.weightStatusBox.insert(END, tempStr)
        
        
    def createUtilitiesFrame(self):
        scrollbar = Scrollbar(self.master)
        scrollbar. grid(row = 1, column = 3, sticky = "NWES")

        self.utilitiesListBox = Listbox(self.master, yscrollcommand = scrollbar.set, height = 34, width = 40)
        #KEEP RELIEF = "GROOVE"
        self.utilitiesListBox.grid(row = 1, column = 2, sticky = "N")
        scrollbar.config(command = self.utilitiesListBox.yview)
        
    def updateUtilitiesFrame(self):
        self.utilitiesListBox.delete(0, END)
        currentRef = self.recommender.currentReference
        weights = self.recommender.weights
        refUtil = self.recommender.utility(self.recommender.caseBase[currentRef], weights)
        tempStr = 'Ref Product ID:' + str(currentRef) + ' Utility:' + str(int(refUtil*1000)/1000.0) 
        self.utilitiesListBox.insert(END, tempStr)
        for util in self.recommender.utilities:
            tempStr = 'ID:' + str(util[0].id) + ' Utility:' + str(int(util[1]*1000)/1000.0)
            self.utilitiesListBox.insert(END, tempStr)
        
        
    def createCompoundCritiqueFrame(self):
        self.compoundCritiqueL = []
        self.compoundCritiqueFrame = Frame(self.master, width = 490, height = 200, borderwidth = 4, \
                                       relief = GROOVE) 
        self.compoundCritiqueFrame.grid(row = 1, column = 1)
        for i in range(5):
            temp = Text(self.compoundCritiqueFrame, font= 'Helvetica', wrap = WORD, width = 40, height = 7,\
                         borderwidth = 4, relief = GROOVE)
            temp.grid(row = i, column = 0)
            self.compoundCritiqueL.append(temp)
            
            '''All the 5 select buttons'''
            temp = Button(self.compoundCritiqueFrame, text = "Select", width = 4, height = 1,\
                           command = lambda i = i: self.userSelect(i))
            temp.grid(row = i, column = 1)
                
    def createUnitCritiqueFrame(self):
        self.unitCritiqueL = []
        self.unitCritiqueFrame = Frame(self.master, width = 490, height = 600, borderwidth = 4, \
                                       relief = GROOVE)
        self.unitCritiqueFrame.grid(row = 1, column = 0) 
        #['Price', 'Resolution', 'OpticalZoom', 'DigitalZoom', 'Weight', 'StorageIncluded']
        self.textBoxList = []
        for i, attrName in enumerate(self.recommender.numericAttrNames):
            Label(self.unitCritiqueFrame, text = attrName).grid(row = 2*i, column = 1, sticky = 'NWES')
            temp = Entry(self.unitCritiqueFrame)
            temp.grid(row = 2*i + 1, column = 1, sticky = 'NWES')
            self.textBoxList.append(temp)
        for i, attrName in enumerate(self.recommender.numericAttrNames):
            '''lowButtons'''
            Button(self.unitCritiqueFrame, text = "L", width = 1, height = 1,\
                    command = lambda i = i: self.unitCritiqueButtonSelect(i, self.textBoxList[i].get(), 'low')).\
                    grid(row = 2*i + 1, column = 0, sticky = 'NWES')
            '''highButtons'''
            Button(self.unitCritiqueFrame, text = "H", width = 1, height = 1,\
                    command = lambda i = i: self.unitCritiqueButtonSelect(i, self.textBoxList[i].get(), 'high')).\
                    grid(row = 2*i + 1, column = 2, sticky = 'NWES')
        
        self.unitCritiqueButton = Button(self.unitCritiqueFrame, text = "Start", width = 4, height = 1, command = self.chooseFirstProduct)
        self.unitCritiqueButton.grid(row = 20, column = 1, sticky = 'NWES')
    
    def displayProduct(self, product):
        t = Text(self.master, font= 'Helvetica', wrap = WORD, width = 60, borderwidth = 4, relief = GROOVE)
        string = product.attr['Manufacturer'] + ' '
        string = string + product.attr['Model'] + '\n'
        string = string + 'Configuration: ' + str(product.attr['Resolution']) + 'MP,  ' \
           + str(product.attr['OpticalZoom']) + 'x Optical Zoom,  ' + str(product.attr['Weight']) + 'gm,  ' \
            + str(product.attr['StorageIncluded']) + 'MB Storage\n'
        
        string += 'Price: ' + str(product.attr['Price'])
        string += '\nProduct ID: ' + str(product.id)
        t.insert(END, string)
        t.config(state = DISABLED, height = 10)
        t.grid(row = 0, column = 0)
    
    def unitCritiqueButtonSelect(self, selection, value, type):
        print 'Low Button Number: ', selection
        
        #Return the highest utility product with a lower value of this particular attribute..
        #NO DELETION HERE.....
        #self.recommender.numericAttrNames
        i = 0
        for k in self.recommender.unitCritiqueSelectedStrings(selection, float(value), type):
            self.compoundCritiqueL[i].delete(1.0, END)
            self.compoundCritiqueL[i].insert(END, k); i += 1
        currentRefProduct = [prod for prod in self.recommender.caseBase if prod.id == self.recommender.currentReference][0]
        self.displayProduct(currentRefProduct)
        self.updateCompoundCritiqueBoxes()
        self.updateWeightBox()
        self.updateWeightStatusBox()
        self.updateUtilitiesFrame()
    
    def userSelect(self, selection):
        i = 0
        for k in self.recommender.critiqueStrings(selection):
            self.compoundCritiqueL[i].delete(1.0, END)
            self.compoundCritiqueL[i].insert(END, k); i+= 1
            
        currentRefProduct = [prod for prod in self.recommender.caseBase if prod.id == self.recommender.currentReference][0]
        self.displayProduct(currentRefProduct)
        self.updateCompoundCritiqueBoxes()
        self.updateWeightBox()
        self.updateWeightStatusBox()
        self.updateUtilitiesFrame()
    
    def updateCompoundCritiqueBoxes(self):
        currentRefProduct = [prod for prod in self.recommender.caseBase if prod.id == self.recommender.currentReference][0]
        i = 0
        for attr in self.recommender.numericAttrNames:
            self.textBoxList[i].delete(0, END)
            self.textBoxList[i].insert(END, str(currentRefProduct.attr[attr])); i+=1
        
        
root = Tk()
app = App(root)
root.wm_title("MAUT Recommender")
RWidth=root.winfo_screenwidth()
RHeight=root.winfo_screenheight()
root.geometry(("%dx%d")%(RWidth,RHeight))
root.mainloop()
