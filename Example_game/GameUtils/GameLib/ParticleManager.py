# Particle class
import pygame
import random
from math import *
from GameUtils.GameLib.GameConstants import *

class Particle:
    def __init__(self, x, y, color, magnitude, lifetime):
        self.x = x
        self.y = y
        self.dx = random.uniform(-magnitude, magnitude)
        self.dy = random.uniform(-magnitude, magnitude)
        self.lifetime = lifetime
        self.shouldBlur = False
        self.color = color

    def update(self,dt):
        self.x += self.dx*dt
        self.y += self.dy*dt
        self.lifetime -= dt

    def draw(self, window):
        position = (int(self.x), int(self.y))
        pygame.draw.circle(window, self.color, position, 2)

class BloodParticle:
    def __init__(self, x, y, magnitude, lifetime, damageVector):
        self.x = x
        self.y = y
        self.magnitude = random.uniform(0,magnitude)**2
        damageMagnitude,theta = damageVector
        if theta != None:
            self.direction = degrees(theta)+random.randint(-round(damageMagnitude),round(damageMagnitude))
        else:
            self.direction = random.randint(0,360)
        self.dx = self.magnitude*cos(radians(self.direction))
        self.dy = self.magnitude*-sin(radians(self.direction))
        self.lifetime = lifetime*random.randint(1,100)
        self.movingLifetime = lifetime
        self.colorscaler = 0.5
        self.GB = min(255, max(0, round(255*(1-self.colorscaler))))
        self.color = (255,self.GB,self.GB)
        self.rect = pygame.Rect(x,y,random.uniform(1, 3),random.uniform(1, 3))
        self.shouldBlur = False

    def update(self,dt):
        self.x += self.dx*dt
        self.y += self.dy*dt
        self.lifetime -= dt
        self.movingLifetime -= dt
        if self.movingLifetime <= 0:
            self.dx,self.dy = 0,0
        self.rect.center = self.x,self.y

    def draw(self, window):
        # position = (int(self.x), int(self.y))
        # pygame.draw.circle(window, self.color, position, 2)
        window.fill(self.color,self.rect,pygame.BLEND_MULT)

class ExplosionParticle:
    def __init__(self, x, y, magnitude, lifetime):
        self.x = x
        self.y = y
        self.magnitude = random.uniform(0,magnitude)
        self.direction = random.randint(0,360)
        self.dx = self.magnitude*cos(radians(self.direction))
        self.dy = self.magnitude*-sin(radians(self.direction))
        self.colorlifetime = lifetime*random.uniform(0.2,0.8)
        self.lifetime = lifetime*random.uniform(0.8,1.2)
        self.grayscale = False
        self.shouldBlur = True
        #assign type to this particle at random. higher colorscaler = deeper color
        
        mode = random.random()

        if mode <= 0.5: # orange particles
            self.colorscaler = random.uniform(0.75,1)
            self.otherColors = min(255, max(0, round(255*(1-self.colorscaler))))
            self.color = [255,self.otherColors,self.otherColors]
        elif mode <= 1: # Yellow particles
            self.colorscaler = random.uniform(0.75,1)
            self.otherColors = min(255, max(0, round(255*(1-self.colorscaler))))
            self.color = [255,255,self.otherColors]
        
        self.rect = pygame.Rect(x,y,random.uniform(2, 5),random.uniform(2, 5))

    def update(self,dt):
        self.x += self.dx*dt
        self.y += self.dy*dt
        self.lifetime -= dt
        self.colorlifetime -= dt
        self.rect.center = self.x,self.y
        if self.magnitude > 5:
            self.magnitude *= 0.9
            self.dx = self.magnitude*cos(radians(self.direction))
            self.dy = self.magnitude*-sin(radians(self.direction))
        
        if self.colorlifetime <= 0 and self.grayscale == False:
            self.colorscaler = (self.color[0]/255+self.color[1]/255+self.color[2]/255)/3
            self.otherColors = min(255, max(0, round(255*(self.colorscaler))))
            self.color = [self.otherColors,self.otherColors,self.otherColors] #[round(self.color[0]*random.uniform(0.85,1)),round(self.color[1]*random.uniform(0.85,1)),round(self.color[2]*random.uniform(0.85,1))]
            self.grayscale = True
        elif self.colorlifetime <= 0 and self.grayscale:
            i = 0
            for color in self.color:
                if color > 1:
                    self.color[i] -= 1
                i += 1   

    def draw(self, window):
        # position = (int(self.x), int(self.y))
        # pygame.draw.circle(window, self.color, position, 2)
        window.fill(self.color,self.rect,pygame.BLEND_MULT)

class Shockwave:
    def __init__(self, x, y, speed,maxradius):
        self.x = x
        self.y = y
        self.speed = speed
        self.magnitude = maxradius
       
        self.lifetime = 1
        self.shouldBlur = False

        self.radius = 1
        self.color = (200,200,200)
        self.width = int(self.speed/50)
        

    def update(self,dt):
        self.radius += self.speed*dt
        if self.radius >= self.magnitude:
            self.lifetime = 0

    def draw(self, window):
        position = (int(self.x), int(self.y))
        # pygame.draw.circle(window, self.color, position, 2)
        pygame.draw.circle(window, self.color, position, self.radius, max(1,int(round(self.width*(1-(self.radius/self.magnitude))))))

# Particle system class
class ParticleSystem:
    def __init__(self, particleModifier):
        self.particles = []
        self.ParticleCountModifier = particleModifier

    def add_particle(self, x, y, color, particleCount, magnitude, lifetime=30):
        for i in range(int(round(particleCount*self.ParticleCountModifier,0))):
            self.particles.append(Particle(x, y, color, magnitude, lifetime))

    def add_blood_particle(self, x, y, count, magnitude, lifetime=5, angle=None):
        for i in range(int(round(count*self.ParticleCountModifier,0))):
            self.particles.append(BloodParticle(x, y, magnitude, lifetime, angle))

    def createExplosion(self,x,y,particleCount,magnitude,maxParticleDistance,lifetime=5):
        for i in range(int(round(particleCount*self.ParticleCountModifier,0))):
            self.particles.append(ExplosionParticle(x,y,magnitude,lifetime))
        self.particles.append(Shockwave(x,y,magnitude,maxParticleDistance))

    def update(self,dt):
        for particle in self.particles:
            particle.update(dt)
            if particle.lifetime <= 0:
                self.particles.remove(particle)

    def draw(self, window:pygame.Surface, blurwindow:pygame.Surface | None=None):
        for particle in self.particles:
            if particle.shouldBlur and blurwindow != None:
                particle.draw(blurwindow)
            else:
                particle.draw(window)