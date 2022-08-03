import pygame
from settings import *

class Button:
    def __init__(self, x, y, width, height, text=None, colour=BLUE,
                 highlightedColour=LIGHTGREY, function=None):
        self.image = pygame.Surface((width, height))
        self.font = pygame.font.SysFont("arial", 20, bold=1)
        self.renderedText = self.font.render(text, False, BLACK)
        self.pos = (x,y)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        self.text = text
        self.colour = colour
        self.highlightedColour = highlightedColour
        self.function = function
        self.width = width
        self.height = height
        self.isHighlighted = False

        
    def update(self, mouse):
        if self.rect.collidepoint(mouse):
            self.isHighlighted = True
        else:
            self.isHighlighted = False
    
    def draw(self, window):
        self.image.fill(self.highlightedColour if self.isHighlighted else self.colour)
        if self.text:
            self.drawText(self.text)
        window.blit(self.image, self.pos)
    
    def click(self):
        self.function()
        
    def drawText(self, text):
        width, height = self.renderedText.get_size()
        x = (self.width-width)//2
        y = (self.height-height)//2
        self.image.blit(self.renderedText, (x, y))
    





