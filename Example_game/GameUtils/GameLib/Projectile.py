from math import *
from GameUtils.GameLib.GameConstants import *
import pygame

class Projectile:
    def __init__(self,pos,velocity,color,source,damage=20):
        self.vx = velocity[0]
        self.vy = velocity[1]
        self.pos = [pos[0],pos[1]]
        self.lastPos = [pos[0],pos[1]]
        self.color = color
        self.source = source
        self.damage = damage
        self.rot = 0
        self.width = 2
        self.lifetime = 0
        self.hit = False
    
    def update(self,dt):
        self.lastPos = [self.pos[0],self.pos[1]]
        self.pos[0] += self.vx*dt
        self.pos[1] += self.vy*dt
        if (self.pos[0] < 0) or (self.pos[0] > WIDTH) or (self.pos[1] < 0) or (self.pos[1] > HEIGHT):
            self.hit = True
            return
        self.lifetime += 1

    def draw(self,window):
        pygame.draw.circle(window,self.color,self.pos,self.width)