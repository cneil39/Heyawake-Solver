import pygame, sys, time, pickle
from settings import *
from Button import Button
from NumberInput import NumberInput
from Textbox import Textbox
from Region import Region
from gurobipy import *


class App:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        self.running = True         # Program running?
        
        self.length = None          # Grid dimension
        self.boardSize = None       # Grid size in pixels
        self.xPos = None            # Position of grid
        self.yPos = None
        self.isGenerated = False    # Is the grid generated?
        self.visualise = False      # Visualise lazy constraints?
        self.overlay = False        # Display puzzle png overlay?
        
        self.defaultMessage = "Please input data..."    # Default message to display
        self.tempMessageTime = None     # Keep track of how long temporary message has been displayed for
        
        self.mousePos = None    # Cursor position
        
        self.buttons = []       # List of Button objects
        self.gridInputs = {}    # Dictionary of gridInput objects
        self.regions = []       # List of Region objects
        

        
        self.gridInputsSelected = []    # gridInputs currently selected

        self.load()     # Load in all initial objects 
        
        
    def run(self):              # Main loop
        while self.running:
            self.events()
            self.update()
            self.draw()
        pygame.quit()
        sys.exit()
        
###### PLAYING STATE FUNCTIONS ######        
    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
                
            # User left clicks
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    if button.isHighlighted:
                        button.click()
                        
                if self.lengthInput.isHighlighted:
                    self.lengthInput.isSelected = True
                else:
                    self.lengthInput.isSelected = False
                    
                if self.savedSelectionInput.isHighlighted:
                    self.savedSelectionInput.isSelected = True
                else:
                    self.savedSelectionInput.isSelected = False              
                        
                for gridInput in self.gridInputs.values():
                    if gridInput.isHighlighted:
                        gridInput.isSelected = True
                    else:
                        gridInput.isSelected = False
                        
                        
            # User right clicks            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                for gridInput in self.gridInputs.values():
                    if gridInput.isHighlighted and not gridInput.inRegion and not gridInput.isGrouped:
                        if len(self.gridInputsSelected) == 0:
                            self.gridInputsSelected.append(gridInput)
                            gridInput.isGrouped = 1
                            gridInput.isSelected = False
                        else:
                            coordsSelected = {gridInput_.getPos() for gridInput_ in self.gridInputsSelected}
                            if not coordsSelected.isdisjoint(self.cellNeigh(gridInput.getPos())):
                                self.gridInputsSelected.append(gridInput)
                                gridInput.isGrouped = 1
                                gridInput.isSelected = False
                                
                                
                    elif gridInput.isHighlighted and gridInput.inRegion:  # if right clicking a region, highlight it
                        for region in self.regions:
                            if gridInput in region.gridInputs:
                                region.isSelected = 1 - region.isSelected
                                region.highlightGridInputs()
                                


                
            # User enters a number
            elif event.type == pygame.TEXTINPUT:
                if self.isInt(event.text):
                    # Length input - Input grid dimensions and allow for double digit inputs
                    if self.lengthInput.isSelected:
                        if not self.lengthInput.num:
                            self.lengthInput.num = event.text
                        elif int(self.lengthInput.num) <= 9:
                            self.lengthInput.num += event.text
                        self.lengthInput.updateFont()
                        
                    if self.savedSelectionInput.isSelected:
                        self.savedSelectionInput.num = event.text
                        self.savedSelectionInput.updateFont()                        
                        
                    
                    # Grid input - Input region number if one hasn't already been entered
                    for gridInput in self.gridInputs.values():
                        if gridInput.isSelected and not gridInput.isLocked:
                            gridInput.num = event.text
                            gridInput.updateFont()
                            for region in self.regions:
                                if gridInput in region.gridInputs:
                                    region.lockGridInputs(event.text)
                                    
                                                   
            
            # User presses a key             
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:   # Backspace for removing inputs
                    if self.lengthInput.isSelected:
                        self.isGenerated = False
                        self.gridInputs = {}
                        self.regions = []
                        self.lengthInput.num = None
                        self.length = None
                        self.defaultMessage = "Please input data..."
                        self.informationTextbox.text = self.defaultMessage
                        self.informationTextbox.updateFont()
                    if self.savedSelectionInput.isSelected:
                        self.savedSelectionInput.num = None
                        


                    for gridInput in self.gridInputs.values():
                        if gridInput.isSelected and gridInput.num:
                            gridInput.num = None
                            for region in self.regions:
                                if gridInput in region.gridInputs:
                                    region.unlockGridInputs()
                            
                elif event.key == pygame.K_SPACE:    # Space bar for add group shortcut
                    self.addGroup()
                    
                    
                    
                    
                    
    
    def update(self):
        self.mousePos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(self.mousePos)
            
        self.lengthInput.update(self.mousePos)
        self.savedSelectionInput.update(self.mousePos)
        
        for gridInput in self.gridInputs.values():
            gridInput.update(self.mousePos)
            
        # If a temporary message is being shown, revert to the original message after 3 seconds
        if self.tempMessageTime:
            if time.perf_counter() - self.tempMessageTime > 3:
                self.tempMessageTimer = None
                self.informationTextbox.text = self.defaultMessage
                self.informationTextbox.colour = BLUE
                self.informationTextbox.updateFont()
            

            
    
    def draw(self):
        self.window.fill(BACKGROUNDGREY)
        
        for button in self.buttons:
            button.draw(self.window)
        
        self.lengthInput.draw(self.window)
        self.savedSelectionInput.draw(self.window)
            
        for gridInput in self.gridInputs.values():
            gridInput.draw(self.window)
            
        self.informationTextbox.draw(self.window)
            
        if self.length and self.isGenerated:  # If board exists, display it
            self.updateBoard()
            
        if self.overlay:    # If overlay toggled on, display the screenshot
            self.window.blit(self.puzzle_img, (self.xPos, self.yPos))
        

        pygame.display.update()
        
        
    
###### HELPER FUNCTIONS ######

    # Load in all buttons, inputs and textboxes
    def load(self):
        self.buttons.append(Button(20, 20, 120, 40,  function=self.generateBoard,   text="Generate"))
        self.buttons.append(Button(20, 80, 120, 40,  function=self.addGroup,        text="Add region"))   
        self.buttons.append(Button(20, 140, 120, 40,  function=self.removeGroup,    text="Del region"))   
        self.buttons.append(Button(20, 200, 120, 40, function=self.undoGroup,       text="Undo"))               
        self.buttons.append(Button(20, 260, 120, 40, function=self.saveSelection,   text="Save")) 
        self.buttons.append(Button(20, 320, 120, 40, function=self.loadSelection,   text="Load"))         
        self.buttons.append(Button(20, 380, 120, 40, function=self.solve,           text="Solve")) 
        self.buttons.append(Button(20, 440, 120, 40, function=self.toggleVisualise, text="Visualise")) 
        self.buttons.append(Button(20, 500, 120, 40, function=self.toggleOverlay,   text="Overlay")) 
        self.buttons.append(Button(20, 840, 120, 40, function=self.closeProgram,    text="Exit"))
        
        
        self.lengthInput =         NumberInput(160, 20, 40, 40,  defaultColour=LIGHTBLUE)
        self.savedSelectionInput = NumberInput(160, 290, 40, 40, defaultColour=LIGHTBLUE)  
        
        
        self.informationTextbox = Textbox((WIDTH-WIDTH//2)//2, HEIGHT-(40+20), WIDTH//2, 40, text=self.defaultMessage)
        
        
        
        
    
            
    # Generate the puzzle grid from the length input by the user. This initialises all the gridInput objects in the grid
    def generateBoard(self):
        if self.isInt(self.lengthInput.num):
            if int(self.lengthInput.num) <= 35 and int(self.lengthInput.num) >= 4:
                self.defaultMessage = "Please input data..."
                self.informationTextbox.text = self.defaultMessage
                self.informationTextbox.updateFont()   
                self.length = int(self.lengthInput.num)   
                self.boardSize = self.length*cellSize              
                self.xPos = (WIDTH - self.boardSize)//2
                self.yPos = (HEIGHT - self.boardSize)//2 
                self.gridInputs = {}
                self.regions = []
                for i in range(self.length):
                    for j in range(self.length):
                        obj = NumberInput(self.xPos+i*cellSize, self.yPos+j*cellSize,
                                                           cellSize, cellSize, xPos=i, yPos=j, defaultColour=LIGHTGREY)
                        self.gridInputs[(i,j)] = obj
    
                        
                self.isGenerated = True       
                self.displayTempMessage(f"Successfully generated a {self.lengthInput.num}x{self.lengthInput.num} grid!", LIGHTBLUE)
            else:
                self.displayTempMessage("Length must be between 4 and 35!", LIGHTRED)


             



                   
    def updateBoard(self):
        for gridInput in self.gridInputs.values():

            self.drawLine(self.xPos+gridInput.xPos*cellSize, self.yPos+gridInput.yPos*cellSize,
                              self.xPos+(gridInput.xPos+1)*cellSize, self.yPos+gridInput.yPos*cellSize,
                              thickness=3 if gridInput.north else 1)

            self.drawLine(self.xPos+(gridInput.xPos+1)*cellSize, self.yPos+gridInput.yPos*cellSize,
                              self.xPos+(gridInput.xPos+1)*cellSize, self.yPos+(gridInput.yPos+1)*cellSize,
                              thickness=3 if gridInput.east else 1)

            self.drawLine(self.xPos+gridInput.xPos*cellSize, self.yPos+(gridInput.yPos+1)*cellSize,
                              self.xPos+(gridInput.xPos+1)*cellSize, self.yPos+(gridInput.yPos+1)*cellSize,
                              thickness=3 if gridInput.south else 1)

            self.drawLine(self.xPos+gridInput.xPos*cellSize, self.yPos+gridInput.yPos*cellSize,
                              self.xPos+gridInput.xPos*cellSize, self.yPos+(gridInput.yPos+1)*cellSize,
                              thickness=3 if gridInput.west else 1) 
      
                
    def drawLine(self, x, y, xx, yy, thickness=1):
        pygame.draw.line(self.window, BLACK, (x,y), (xx,yy), thickness)
        
        
    # Checks if a string is a number
    def isInt(self, string):
        try:
            int(string)
            return True
        except:
            return False  
        
    # Display a 3 second message at the bottom of the screen
    def displayTempMessage(self, text, colour):
        self.informationTextbox.text = text
        self.informationTextbox.colour = colour
        self.informationTextbox.updateFont()      
        self.tempMessageTime = time.perf_counter()        
        

###### BUTTON FUNCTIONS ######
    def addGroup(self):
        if self.gridInputsSelected:                      # If there are gridInputs selected
            region = Region(self.gridInputsSelected)     # Create a new region object with the current gridInputs selected
            self.regions.append(region)                  # Add new region to list of regions
            region.groupGridInputs()                     # Group all gridInputs within region
            self.gridInputsSelected = []                 # Reset list of selected gridInputs

            
        for gridInput in self.gridInputs.values():       # Check if all gridInputs are in a region, if so, the puzzle is ready to be solved
            if not gridInput.inRegion:
                return
            
        self.defaultMessage = "Ready to solve..."
        self.informationTextbox.text = self.defaultMessage
        self.displayTempMessage("Ready to solve...", LIGHTBLUE)
            
        
    def removeGroup(self):
        toRemove = []                       # Create a list of regions to be removed
        for region in self.regions:         # Search for regions that are selected and reset their gridInputs to their default state
            if region.isSelected:
                toRemove.append(region)
                region.resetGridInputs()
        if toRemove:                        # Remove the selected regions
            self.defaultMessage = "Please input data..."
            self.informationTextbox.text = self.defaultMessage
            self.displayTempMessage(f"Regions removed", LIGHTBLUE)
            for region in toRemove:
                self.regions.remove(region)
            
            


    def undoGroup(self):
        # If gridInputs are currently being selected for grouping, remove the last selected gridInput
        if self.gridInputsSelected:
            self.gridInputsSelected[-1].isGrouped = 0                  # gridInput no longer grouped
            self.gridInputsSelected = self.gridInputsSelected[:-1]     # Remove from selected gridInputs
            
        # Otherwise, remove the last region if any
        elif self.regions:
            region = self.regions[-1]          # Get previous region
            region.resetGridInputs()           # Reset every gridInput to its default state
            self.regions = self.regions[:-1]   # Remove the region from regions
            self.defaultMessage = "Please input data..."
            self.informationTextbox.text = self.defaultMessage
            self.displayTempMessage(f"Region removed", LIGHTBLUE)




    # Toggle visualisation of lazy constraints being added
    def toggleVisualise(self):
        if self.visualise:
            self.visualise = False
            self.buttons[7].colour = BLUE
            self.displayTempMessage("Lazy constraints will no longer be visualised", LIGHTBLUE)
        else:
            self.visualise = True
            self.buttons[7].colour = DARKBLUE
            self.displayTempMessage("Lazy constraints will now be visualised", LIGHTBLUE)

    # Toggle overlay of puzzle screenshot. Automatically positions and resizes the screenshot
    def toggleOverlay(self):
        if self.overlay:  # Disable overlay
            self.overlay = False
            self.buttons[8].colour = BLUE
            self.displayTempMessage("Overlay toggled OFF", LIGHTBLUE)
        else:             # Enable overlay
            try:              
                self.puzzle_img = pygame.image.load("puzzle.png")  # Load puzzle screenshot
                self.puzzle_img = pygame.transform.scale(self.puzzle_img, (self.boardSize+3,self.boardSize+3))   # Resize screenshot to grid
                self.puzzle_img.set_alpha(150)
                self.overlay = True
                self.buttons[8].colour = DARKBLUE
                self.displayTempMessage("Overlay toggled ON", LIGHTBLUE)
            except:
                self.displayTempMessage("Failed to load puzzle png", LIGHTRED)
            

    # Close the program. The solver reaches termination quicker when visualisation is disabled
    def closeProgram(self):
        self.visualise = False
        self.running = False



    # Save current puzzle template to file    
    def saveSelection(self):      
        if self.defaultMessage == "Ready to solve...":
            save_number = int(self.savedSelectionInput.num)
            with open(f"puzzle{save_number}.txt", "wb") as filehandle:
                information = {"length": self.length, "regions": [{gridInput.getPos(): gridInput.num for gridInput in region.gridInputs} for region in self.regions]}
                pickle.dump(information, filehandle) 
            self.displayTempMessage(f"Puzzle saved as puzzle {save_number}", LIGHTBLUE)
        else:
            self.displayTempMessage(f"Enter all puzzle data before saving!", LIGHTRED)

            
    # Load puzzle template from file
    def loadSelection(self):
        if self.savedSelectionInput.num:
            save_number = int(self.savedSelectionInput.num)
            try:     
                with open(f"puzzle{save_number}.txt", "rb") as filehandle:
                    information = pickle.load(filehandle)
                self.lengthInput.num = str(information["length"])
                self.lengthInput.updateFont()
                self.length = int(self.lengthInput.num)
                self.boardSize = self.length*cellSize
                self.xPos = (WIDTH - self.boardSize)//2
                self.yPos = (HEIGHT - self.boardSize)//2
                self.gridInputs = {}
                self.regions = []
                
                for region in information["regions"]:
                    region_number = -1
                    gridInputs = []
                    for (i,j), number in region.items():
                        gridInput_obj = NumberInput(self.xPos + i*cellSize, self.yPos + j*cellSize, cellSize, cellSize, xPos=i, yPos=j, defaultColour=LIGHTGREY)
                        self.gridInputs[(i,j)] = gridInput_obj
                        gridInputs.append(gridInput_obj)
                        if number:
                            gridInput_obj.num = number
                            region_number = number
                            gridInput_obj.updateFont()
                    region_obj = Region(gridInputs=gridInputs, number=region_number)
                    self.regions.append(region_obj)
                    region_obj.groupGridInputs()
                            
                self.isGenerated = True
                self.defaultMessage = "Ready to solve..."
                self.displayTempMessage(f"Successfully loaded puzzle {save_number}!", LIGHTBLUE)
                

                
            except:
                self.displayTempMessage(f"Puzzle {save_number} not found!", LIGHTRED)
        else:
            self.displayTempMessage(f"Enter a puzzle number between 0-9!", LIGHTRED)
                
            

                
    # Return all orthogonal neighbours of a cell
    def cellNeigh(self, cell):
        neighbours = []
        i,j = cell
        if i>0:
            neighbours.append((i-1,j))
        if j<self.length-1:
            neighbours.append((i,j+1))
        if i<self.length-1:
            neighbours.append((i+1,j))
        if j>0:
            neighbours.append((i,j-1))
        return neighbours
    
    # Return all diagonal neighbours of a cell
    def diagonalNeighbours(self, cell):
        neighbours = []
        i,j = cell
        if i-1>=0 and j-1>=0:
            neighbours.append((i-1, j-1))
        if i-1>=0 and j+1<=self.length-1:
            neighbours.append((i-1, j+1))
        if i+1<=self.length-1 and j+1<=self.length-1:
            neighbours.append((i+1, j+1))
        if i+1<=self.length-1 and j-1>=0:
            neighbours.append((i+1, j-1))
        return neighbours       
    
    
    # Iterate south until a string of cells has been collected that spans exactly 3 regions. 
    # Otherwise, return False
    def vertNeigh(self, cell):    
        neighbours = []
        regions = []
        for i in range(cell[1], self.length):
            neighbours.append((cell[0], i))
            for region in self.regions:
                if (cell[0], i) in region.getPos():
                    if region not in regions:
                        regions.append(region)
                    if len(regions) >= 3:
                        return neighbours
        return False
        
    # Iterate east until a string of cells has been collected that spans exactly 3 regions. 
    # Otherwise, return False        
    def horNeigh(self, cell):       
        neighbours = []
        regions = []
        for i in range(cell[0], self.length):
            neighbours.append((i, cell[1]))
            for region in self.regions:
                if (i, cell[1]) in region.getPos():
                    if region not in regions:
                        regions.append(region)
                    if len(regions) >= 3:
                        return neighbours
        return False      
    
    
               
###### SOLVER HELPER FUNCTIONS ######                


    # Iterate through all diagonally connected black cells. If two distinct boundary points have been found,
    # then an impenetrable black wall has been found.
    def followBlackCells(self, cell, XV):
        if cell in self.visitedCells:
            return
        if cell[0] == 0 or cell[0] == self.length-1 or cell[1] == 0 or cell[1] == self.length-1: # If cell on boundary
            self.boundaryCells += 1
        self.visitedCells.append(cell)
        self.visitedBlackCells.append(cell)
        if self.boundaryCells > 1:
            return
        for (i,j) in self.diagonalNeighbours(cell):
            if XV[(i,j,1)] > 0.9:
                self.followBlackCells((i,j), XV)      
              
                
                
                
                
    # Iterate through all diagonally connected black cells. If we revisit a cell which is NOT the previous cell,
    # then a loop of black cells has been found.                
    def followBlackCells_Loop(self, prevCell, cell, XV):
        if cell in self.visitedCells:
            return
        self.visitedCells.append(cell)
        self.visitedBlackCells.append(cell)
        for (i,j) in self.diagonalNeighbours(cell):
            if XV[(i,j,1)] > 0.9:    # if the neighbouring cell is black
                if (i,j) != prevCell and (i,j) in self.visitedCells:    # If the neighbouring cell is NOT the previous cell but it has been visited, then we have found a loop
                    self.loopFound = True
                    return
                if not self.loopFound:
                    self.followBlackCells_Loop(cell, (i,j), XV)   
                    
                    
    # "Chop off" any tails on an impenetrable wall (loopMode=False) or on a loop (loopMode=True).
    # This makes the lazy constraint tighter and improves runtime.
    def purgeTrails(self, loopMode):
        trailExists = True
        while trailExists:
            trailExists = False
            for cell in self.visitedCells:
                if not loopMode:
                    if cell[0] == 0 or cell[0] == self.length-1 or cell[1] == 0 or cell[1] == self.length-1: # If on boundary, don't count as endpoint
                        continue
                neighbours = self.diagonalNeighbours(cell)
                if len(set(self.visitedCells).intersection(neighbours)) == 1: # Found an endpoint
                    trailExists = True
                    self.visitedCells.remove(cell)
                    
                    
               
                
 
                
###### SOLVER ######
    def solve(self):
        if self.defaultMessage == "Ready to solve...":
            self.lazyConstraintsAdded = 0
            for gridInput in self.gridInputs.values():
                gridInput.inSolver = True
                gridInput.defaultColour = LIGHTGREY
            self.defaultMessage = "Solving"
            self.informationTextbox.text = self.defaultMessage
            self.informationTextbox.updateFont()
            
            m = Model("Heyawake Solver")
            
            X = {(i,j,col):
                m.addVar(vtype=GRB.BINARY)
                for (i,j) in self.gridInputs.keys() for col in [0,1]}
                
          
                
                 
            SelectOne = {(i,j):
                m.addConstr(X[i,j,0] + X[i,j,1] == 1)
                for (i,j) in self.gridInputs.keys()}
                
       
            RegionNumber = []
            for region in self.regions:
                if int(region.number) >= 0:
                    cells = region.getPos()
                    RegionNumber.append(m.addConstr(quicksum(X[cell[0], cell[1], 1] for cell in cells) == int(region.number)))
                    
       
            AdjacentBlack = {(i,j):
                m.addConstr(quicksum(X[ii,jj,1] for (ii,jj) in self.cellNeigh((i,j))) <= len(self.cellNeigh((i,j)))*(1 - X[i,j,1]))
                for (i,j) in self.gridInputs.keys()}
                
        
            VertOrth = {}
            for (i,j), gridInput in self.gridInputs.items():
                if gridInput.south:
                    neighbours = self.vertNeigh(gridInput.getPos())
                    if neighbours:
                        VertOrth[(i,j)] = m.addConstr(quicksum(X[ii,jj,1] for (ii,jj) in neighbours) >= 1)
    

            HorOrth = {}
            for (i,j), gridInput in self.gridInputs.items():
                if gridInput.east:
                    neighbours = self.horNeigh(gridInput.getPos())
                    if neighbours:
                        HorOrth[(i,j)] = m.addConstr(quicksum(X[ii,jj,1] for (ii,jj) in neighbours) >= 1)     
                        
        

            ConnectedAtLeast = {(i,j):
                m.addConstr(quicksum(X[ii,jj,0] for (ii,jj) in self.cellNeigh((i,j))) >= X[i,j,0])
                for (i,j) in self.gridInputs.keys()}
            
            
                
                
    
            def Callback(model, where):
                if where==GRB.Callback.MIPSOL:
              
            
                    XV = {k: v for (k,v) in zip(X.keys(), model.cbGetSolution(list(X.values())))}
                        
                    """ Update current solution on the grid"""
                    for (i,j), gridInput in self.gridInputs.items():
                        if XV[(i,j,1)] > 0.9:
                            gridInput.defaultColour = DARKGREY
                            if gridInput.num:
                                gridInput.updateFont(textColour=WHITE)
                        else:
                            gridInput.defaultColour = WHITE  
                            if gridInput.num:
                                gridInput.updateFont(textColour=BLACK)
                        
                    self.events()
                    self.update()
                    self.draw()      
                    

                    
                    """ Check if any string of black cells forms a wall with endpoints
                    on the boundary. In any connected string, if there are 2 or more 
                    black cells on the boundary, then this must contain an impenetrable wall.
                    We then run a second function purgeTrails, which 'chops off' the tails
                    on this connected string of black cells.
                    A lazy constraint prevents this wall from happening again.
                    """                
                    self.visitedBlackCells = []
                    for k in XV: 
                        if k[0] in [0, self.length-1] or k[1] in [0, self.length-1]:                    # If cell on boundary
                            if XV[(k[0],k[1],1)] > 0.9 and (k[0], k[1]) not in self.visitedBlackCells:  # If cell is black and hasn't been checked yet
                                self.boundaryCells = 0
                                self.visitedCells = []
                                self.followBlackCells((k[0],k[1]), XV)
                                if self.boundaryCells > 1:
                                
                                    if self.visualise:
                                        for cell in self.visitedCells:
                                            self.gridInputs[cell].defaultColour = GREEN
                                        self.events()
                                        self.update()
                                        self.draw()                                        
                                        time.sleep(2)
                                        for cell in self.visitedCells:
                                            self.gridInputs[cell].defaultColour = DARKGREY
                                        self.events()
                                        self.update()
                                        self.draw()
                               
                                    # PURGE TRAILING POINTS:
                                    self.purgeTrails(loopMode=False)
                                    
                                    if self.visualise:
                                        for cell in self.visitedCells:
                                            self.gridInputs[cell].defaultColour = DARKGREEN
                                        self.events()
                                        self.update()
                                        self.draw()
                                        time.sleep(2)                                       
                                        
                                        for cell in self.visitedCells:
                                            self.gridInputs[cell].defaultColour = DARKGREY
                                        self.events()
                                        self.update()
                                        self.draw()  
                                        
                                    
                                    self.lazyConstraintsAdded += 1
                                    model.cbLazy(quicksum(X[(i,j,1)] for (i,j) in self.visitedCells) <= len(self.visitedCells) - 1)
                                    break
                                                                     
                         
                        
                                
                    """ Check if any string of black cells forms a closed loop. If we iterate through
                    all connected cells and find a cell which we have already visited but is NOT the previous cell,
                    then we have found a connected string of black cells which contains a loop.
                    We then run a second function purgeTrails, which 'chops off' the tails
                    on this loop of black cells.
                    If such a loop exists, a lazy constraint is added to prevent it.
                    """                    
                    self.visitedBlackCells = []
                    for k in XV:
                        if XV[(k[0],k[1],1)] > 0.9 and (k[0],k[1]) not in self.visitedBlackCells:  # If cell is black and hasn't been checked yet
                            self.loopFound = False
                            self.visitedCells = []
                            self.followBlackCells_Loop(0,(k[0],k[1]), XV)
                            if self.loopFound:
                                
                                if self.visualise:
                                    for cell in self.visitedCells:
                                        self.gridInputs[cell].defaultColour = BLUE
                                    self.events()
                                    self.update()
                                    self.draw()
                                    time.sleep(2)
                                    
                                    
                                    
                                    for cell in self.visitedCells:
                                        self.gridInputs[cell].defaultColour = DARKGREY
                                    self.events()
                                    self.update()
                                    self.draw()                           
                                
                                # PURGE TRAILING POINTS:
                                self.purgeTrails(loopMode = True)
                                
                                if self.visualise:
                                    for cell in self.visitedCells:
                                        self.gridInputs[cell].defaultColour = DARKBLUE
                                    self.events()
                                    self.update()
                                    self.draw()
                                    time.sleep(2)
                                    
                                                                       
                                    for cell in self.visitedCells:
                                        self.gridInputs[cell].defaultColour = DARKGREY
                                    self.events()
                                    self.update()
                                    self.draw()   
                                    
                                
                                self.lazyConstraintsAdded += 1
                                model.cbLazy(quicksum(X[(i,j,1)] for (i,j) in self.visitedCells) <= len(self.visitedCells) - 1)
                                break
                            
                    if not self.running:
                        print("Terminating")
                        self.visualise = False
                        model.terminate()

   
                                          
            m.setParam('LazyConstraints', 1)            
            m.optimize(Callback)
            
            
            if m.status == 2:
                self.defaultMessage = f"Solved in {round(m.runtime,2)} seconds! {self.lazyConstraintsAdded} walls/loops were found before solution reached"
                self.displayTempMessage(f"Solved in {round(m.runtime,2)} seconds! {self.lazyConstraintsAdded} walls/loops were found before solution reached", GREEN)  
            else:
                self.displayTempMessage(f"Solution not found in {round(m.runtime,2)} seconds!", LIGHTRED)  
            
            
