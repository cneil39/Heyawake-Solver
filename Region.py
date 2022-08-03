from settings import *



class Region:
    def __init__(self, gridInputs, number = -1):
        self.gridInputs = gridInputs
        self.number = number
        self.isSelected = 0
      
        
    def getPos(self):
        return [(gridInput.xPos, gridInput.yPos) for gridInput in self.gridInputs]
    
    def groupGridInputs(self):
        cells = self.getPos()
        for gridInput in self.gridInputs:
            gridInput.isLocked = False
            gridInput.isGrouped = 0
            gridInput.inRegion = True
            
            x,y = gridInput.getPos()
            if (x-1,y) not in cells:
                gridInput.west = True
            if (x,y+1) not in cells:
                gridInput.south = True
            if (x+1,y) not in cells:
                gridInput.east = True
            if (x,y-1) not in cells:
                gridInput.north = True        
        
    def resetGridInputs(self):   # Reset grid inputs to default state
        for gridInput in self.gridInputs:    
            gridInput.reset()
            
    def lockGridInputs(self, number):
        self.number = int(number)
        for gridInput in self.gridInputs:
            gridInput.isLocked = True      
            
    def unlockGridInputs(self):
        self.number = -1
        for gridInput in self.gridInputs:
            gridInput.isLocked = False      
            
    def highlightGridInputs(self):
        for gridInput in self.gridInputs:
            if self.isSelected:
                gridInput.regionColour = LIGHTRED
            else:
                gridInput.regionColour = GREEN
            