import pygame
from settings import *

class Textbox:
    def __init__(self, x, y, width, height, text=None):
        self.image = pygame.Surface((width, height))
        self.font = pygame.font.SysFont("arial", 25, bold=1)
        self.renderedText = None
        self.pos = (x, y)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        self.text = text
        self.colour = BLUE
        self.width = width
        self.height = height
        
        self.updateFont()
        
    
    def draw(self, window):
        self.image.fill(self.colour)
        if self.text:
            self.drawText(self.text)
        window.blit(self.image, self.pos)
        
    def updateFont(self):      
        self.renderedText = self.font.render(self.text, False, BLACK)        
        
    def drawText(self, text):
        width, height = self.renderedText.get_size()
        x = (self.width-width)//2
        y = (self.height-height)//2
        self.image.blit(self.renderedText, (x, y))
        

