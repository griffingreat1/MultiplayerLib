import pygame
from math import *
from GameUtils.GameLib.GameConstants import *

def drawVignette(screen,player):
    # if player is under half health, draw a red vignette around edges of screen where the size and strength of the vignette is directly correlated to how much health remains
    if player.health <= 50: 
        num_parts = 10
        scale = (1-player.health/50)/num_parts
        for i in range(1,num_parts+1):
            vignettewidth = i*(50-player.health)/num_parts
            GB = min(255, max(0, round(255*(1-scale))))
            top = pygame.Rect(0,0,WIDTH,vignettewidth)
            bottom = pygame.Rect(0,HEIGHT-vignettewidth,WIDTH,vignettewidth)
            left = pygame.Rect(0,0,vignettewidth,HEIGHT)
            right = pygame.Rect(WIDTH-vignettewidth,0,vignettewidth,HEIGHT)
            screen.fill((255,GB,GB), top,pygame.BLEND_MULT)
            screen.fill((255,GB,GB), bottom,pygame.BLEND_MULT)
            screen.fill((255,GB,GB), left,pygame.BLEND_MULT)
            screen.fill((255,GB,GB), right,pygame.BLEND_MULT)

class MotionBlurManager:
    def __init__(self,numFramesBlurred):
        self.MAX_FRAMES = numFramesBlurred
        self.frames = []
    
    def createBlurSurface(self,screen):
        self.tmp = screen.copy()
        self.tmp.set_colorkey((150,150,150))
        return self.tmp
    
    def drawPlayerObjToBlurSurface(self,PlayerObj,font,nonblurscreen):
        PlayerObj.draw(self.tmp,font,nonblurscreen)
    
    def drawEntityObjToBlurSurface(self,entity):
        entity.draw(self.tmp)
    
    def drawParticleManager(self,particleManager,nonblurscreen):
        particleManager.draw(nonblurscreen,self.tmp)
    
    def drawBlurFrames(self,screen):
        for frame in self.frames:
            screen.blit(frame,(0,0))
        if len(self.frames) == self.MAX_FRAMES:
            self.frames.pop()
        self.frames.insert(0,self.tmp)
        screen.blit(self.tmp, (0,0))