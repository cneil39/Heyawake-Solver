import pygame
from settings import *

class NumberInput:
    def __init__(self, x, y, width, height, xPos=None, yPos=None, defaultColour=GREY):
        self.image = pygame.Surface((width, height))
        self.renderedFont = None
        self.width = width
        self.height = height
        self.pos = (x, y)
        self.xPos = xPos
        self.yPos = yPos
        self.num = None
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        self.defaultColour = defaultColour
        self.highlightedColour = LIGHTGREY
        self.groupedColour = LIGHTGREEN
        self.regionColour = GREEN
        self.isHighlighted = False
        self.isSelected = False
        self.isGrouped = 0
        self.isLocked = True
        self.inRegion = False
        self.inSolver = False
        self.fontSize = int(self.height/1.3)
        self.font = pygame.font.SysFont("arial", self.fontSize, bold=1) 
        
        self.north = False
        self.east = False
        self.south = False
        self.west = False
        
        self.updateFont()
    
    def update(self, mouse):
        if self.rect.collidepoint(mouse):
            self.isHighlighted = True
        else:
            self.isHighlighted = False
            
    def draw(self, window):
        if self.isSelected:
            self.image.fill(self.highlightedColour)
        elif self.isGrouped:
            self.image.fill(self.groupedColour)
        elif self.inSolver:
            self.image.fill(self.defaultColour)
        elif self.inRegion:
            self.image.fill(self.regionColour)
        else:
            self.image.fill(self.defaultColour)
            
        if self.num:
            self.drawText(self.num)
        
        window.blit(self.image, self.pos)
        
    def updateFont(self, textColour = BLACK):
        self.renderedFont = self.font.render(self.num, False, textColour)        
        
    def drawText(self, renderedFont):
        width, height = self.renderedFont.get_size()
        x = (self.width-width)//2
        y = (self.height-height)//2
        self.image.blit(self.renderedFont, (x, y))
        
    def getPos(self):
        return (self.xPos, self.yPos)

    def reset(self):         # Reset to default state
        self.isLocked = True
        self.num = None
        self.inRegion = False
        self.regionColour = GREEN
        
        self.west = False
        self.south = False
        self.east = False
        self.north = False
        


