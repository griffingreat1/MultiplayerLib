import random
import threading
import time
import pygame
from GameUtils.GameLib.GameConstants import *
from GameUtils.GameLib.ParticleManager import ParticleSystem
from math import *

class Player:
    radius = 8
    linewidth = radius*5/4
    def __init__(self,particleManager:ParticleSystem,color):
        pos = [random.randint(0,600),random.randint(0,600)]
        self.rect = pygame.Rect(pos[0],pos[1],2*self.radius,2*self.radius)
        self.rect.center = pos
        self.head = pygame.Rect(pos[0],pos[1],self.radius,self.radius)
        self.head.center = self.rect.center
        self.color = color
        self.helmetcolor = (color[0]/2,color[1]/2,color[2]/2)
        self.can_shoot = True
        self.rot = 0
        self.health = 100
        self.ammo = MAX_BULLETS
        self.gunlength = self.radius*5/2
        self.particleManager = particleManager
        self.lastSprintTime = 0
        self.dx,self.dy = 0,0
        self.stamina = PLAYER_MAX_STAMINA
        self.reloading = False
        self.deaths = 0
        self.ID = random.randint(0,100000)
        self.packetNum = 0
    
    def draw(self,window,font,textsurface=None):
        if not textsurface:
            textsurface = window
        pygame.draw.line(window,(0,0,0),self.rect.center,
                                 (self.rect.centerx+self.gunlength*cos(self.rot),
                                  self.rect.centery-self.gunlength*sin(self.rot)),int(self.linewidth/4))
        pygame.draw.circle(window, self.color, self.rect.center, self.radius)
        pygame.draw.circle(window, self.helmetcolor, self.head.center,int(round(self.radius/2)))
        healthText,healthRect = self.playerHealthText(font)
        textsurface.blit(healthText,healthRect)
        ammoText,ammoRect = self.getAmmoText(font)
        textsurface.blit(ammoText,ammoRect)

    def update(self,mousePos,dt):
        prevpos = self.rect.center
        if self.health <= 0:
            self.deaths += 1
            self.health = 100
            self.can_shoot = True
            self.rect.center = [random.randint(0,600),random.randint(0,600)]
        
        if time.time()-self.lastSprintTime > PLAYER_STAMINA_COOLDOWN:
            if self.stamina < PLAYER_MAX_STAMINA:
                self.stamina += 1
            self.stamina = min(self.stamina,PLAYER_MAX_STAMINA)
        keys = pygame.key.get_pressed()
        self.doMovement(keys,dt)

        self.dx,self.dy = prevpos[0]-self.rect.centerx,prevpos[1]-self.rect.centery
        self.pointAtPos(mousePos)
        self.head.center = self.rect.center
    
    def doMovement(self,keys,dt):
        playerIsSprinting = False
        playerMoved = False

        if keys[pygame.K_LSHIFT] and self.stamina > 0:
            playerIsSprinting = True
        
        if keys[pygame.K_w]:
            if playerIsSprinting:
                self.rect.centery -= PLAYER_SPRINT_MULT*PLAYER_SPEED*dt
            else:
                self.rect.centery -= PLAYER_SPEED*dt
            playerMoved = True
        if keys[pygame.K_s]:
            if playerIsSprinting:
                self.rect.centery += PLAYER_SPRINT_MULT*PLAYER_SPEED*dt
            else:
                self.rect.centery += PLAYER_SPEED*dt
            playerMoved = True
        if keys[pygame.K_a]:
            if playerIsSprinting:
                self.rect.centerx -= PLAYER_SPRINT_MULT*PLAYER_SPEED*dt
            else:
                self.rect.centerx -= PLAYER_SPEED*dt
            playerMoved = True
        if keys[pygame.K_d]:
            if playerIsSprinting:
                self.rect.centerx += PLAYER_SPRINT_MULT*PLAYER_SPEED*dt
            else:
                self.rect.centerx += PLAYER_SPEED*dt
            playerMoved = True
        
        if keys[pygame.K_r]:
            if not self.reloading and self.ammo < MAX_BULLETS:
                threading.Thread(target=self.reloadGun,daemon=True).start()

        if playerMoved and playerIsSprinting:
            self.lastSprintTime = time.time()
            self.stamina = max(self.stamina-100*dt,0)
        
        if time.time()-self.lastSprintTime > PLAYER_STAMINA_COOLDOWN:
            if self.stamina < PLAYER_MAX_STAMINA:
                self.stamina += 1
            self.stamina = min(self.stamina,PLAYER_MAX_STAMINA)

        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
    
    def pointAtPos(self,pos):
        direction = pygame.Vector2(pos)-pygame.Vector2(self.rect.center)
        distance_to_point,angle_target = direction.as_polar()
        self.angle_target = angle_target
        self.rot = radians(-self.angle_target)

    def fire_wpn(self):
        if self.can_shoot and self.ammo > 0 and not self.reloading:
            self.ammo -= 1
            threading.Thread(target=self.gunCooldown,daemon=True).start()
            return [BULLET_SPEED*cos(self.rot),BULLET_SPEED*-sin(self.rot)]
        else:
            return False
    
    def reloadGun(self):
        self.reloading = True
        time.sleep(RELOAD_TIME_SECS)
        self.ammo = MAX_BULLETS
        self.reloading = False
    
    def gunCooldown(self):
        self.can_shoot = False
        time.sleep(GUNCOOLDOWN)
        self.can_shoot = True

    def playerHealthText(self,font):
        text = font.render(f"health: {round(self.health,0)}", True, (255,255,255))
        textRect = text.get_rect()
        textRect.bottomleft = [0,HEIGHT-5]
        return text,textRect
    
    def getAmmoText(self,font):
        textstr = f"{self.ammo}/{MAX_BULLETS}" if not self.reloading else "reloading..."
        text = font.render(textstr, True, (255,255,255))
        textRect = text.get_rect()
        textRect.bottomright = [WIDTH-5,HEIGHT-5]
        return text,textRect

    def createPositionPacket(self):
        """
        constructs a packet to send to the server. the packet is a dictionary list.
        """
        self.packetNum += 1
        msg = {
            "type":"playerdata",
            "packetNum":self.packetNum,
            "position":{
                "x":round(self.rect.centerx),
                "y":round(self.rect.centery),
                "rotation":round(self.rot,3)
            },
            "velocity":[self.dx,self.dy],
            "health":self.health,
            "timestamp":time.time(),
            "deaths":self.deaths,
            "ID":self.ID
        }
        return msg

    def hitCheck(self, projectiles):
        for projectile in projectiles:
            prevPos, curPos = projectile.lastPos, projectile.pos
            hitinfo = self.rect.clipline(prevPos,curPos)
            if len(hitinfo) > 0 and projectile.source != self:
                headshot = self.head.clipline(prevPos,curPos)
                damageTheta = atan2(hitinfo[0][1]-hitinfo[1][1],hitinfo[1][0]-hitinfo[0][0])
                if len(headshot) > 0:
                    hitinfo = headshot
                    projectile.damage = projectile.damage*HEADSHOT_DMG_MULTIPLIER
                damageOrigin = hitinfo[-1]
                self.damage(projectile.damage,damageOrigin,damageTheta)
                projectile.hit = True
        return projectiles
    
    def damage(self, damageMagnitude, damageOrigin, damageTheta=None):
        self.health -= damageMagnitude
        damageVec = (damageMagnitude,damageTheta)
        num = damageMagnitude/10
        if num <= 11:
            self.particleManager.add_blood_particle(damageOrigin[0],damageOrigin[1],BLOOD_PARTICLE_COUNT,BLOOD_PARTICLE_SPEED,BLOOD_PARTICLE_LIFETIME,damageVec)
        else:
            self.particleManager.add_blood_particle(damageOrigin[0],damageOrigin[1],min(BLOOD_PARTICLE_COUNT*num,MAX_BLOOD_PARTICLES),BLOOD_PARTICLE_SPEED*min(num/10,2),BLOOD_PARTICLE_LIFETIME,damageVec)

    def get_rotation(self):
        return self.rot

class ConnectedPlayer(Player):
    registry = {}
    _snapshot = {}
    def __init__(self,particleManager,color,ID):
        super().__init__(particleManager,color)
        pos = [-100,-100]
        self.rect = pygame.Rect(pos[0],pos[1],2*self.radius,2*self.radius)
        self.rect.center = pos
        self.head = pygame.Rect(pos[0],pos[1],self.radius,self.radius)
        self.head.center = self.rect.center
        self.can_shoot = True
        self.rot = 0
        self.health = 100
        self.gunlength = self.radius*5/2
        self.latency = 0
        self.goalPosition = [0,0]
        self.lastKnownVelocity = [0,0]
        self.ID = ID
        self.latestPacketTime = time.time()
    
    def draw(self,window,font,textsurface=None):
        if not textsurface:
            textsurface = window
        pygame.draw.line(window,(0,0,0),self.rect.center,
                                 (self.rect.centerx+self.gunlength*cos(self.rot),
                                  self.rect.centery-self.gunlength*sin(self.rot)),int(self.linewidth/4))
        pygame.draw.circle(window, self.color, self.rect.center,self.radius)
        pygame.draw.circle(window, self.helmetcolor, self.head.center,int(round(self.radius/2)))

        pingText,pingTextRect = self.playerPingText(font)
        textsurface.blit(pingText,pingTextRect)

    def update(self,dt):
        # self.rect.centerx += self.lastKnownVelocity[0]*dt
        # self.rect.centery += self.lastKnownVelocity[1]*dt
        self.rect.centerx = pygame.math.lerp(self.rect.centerx,self.goalPosition[0],5*dt)
        self.rect.centery = pygame.math.lerp(self.rect.centery,self.goalPosition[1],5*dt)
        self.head.center = self.rect.center
    
    def pointAtPos(self,pos):
        pass
    
    def updateWithPositionPacket(self,datas):
        if datas.get("packetNum",0) > self.packetNum:
            self.goalPosition[0] = datas.get("position").get("x",0)
            self.goalPosition[1] = datas.get("position").get("y",0)
            self.rot = datas.get("position").get("rotation",0)
            self.health = datas.get("health",-1)
            self.deaths = datas.get("deaths",0)
            self.getLatency(datas)
            self.packetNum = datas.get("packetNum")
        self.heartbeat()
    
    def heartbeat(self):
        self.latestPacketTime = time.time()
    
    def getLatency(self,datas):
        self.latency = time.time()-datas.get("timestamp",time.time())
        return self.latency

    def fire_wpn(self):
        return [BULLET_SPEED*cos(self.rot),BULLET_SPEED*-sin(self.rot)]
    
    def playerPingText(self,font):
        text = font.render(f"ping: {round(self.latency*1000)}", True, (255,255,255))
        textRect = text.get_rect()
        textRect.midtop = self.rect.midbottom
        return text,textRect

    def get_is_alive(self):
        return time.time()-self.latestPacketTime < PEER_TIMEOUT

    @classmethod
    def getInstance(cls, particleManager, color, value):
        with cls.registry_lock:
            instance = cls.registry.get(value)
            if instance is None:
                instance = cls(particleManager, color, value)
                cls.registry[value] = instance
            return instance

    @classmethod
    def updateAll(cls, dt):
        cls.snapshot_registry()

        for instance in cls._snapshot.values():
            instance.update(dt)

    @classmethod
    def hitCheckAll(cls, projectiles):
        for instance in cls._snapshot.values():
            instance.hitCheck(projectiles)

    @classmethod
    def drawAll(cls, window, font):
        for instance in cls._snapshot.values():
            instance.draw(window, font)

    @classmethod
    def callExternalMethodOnAll(cls, func, **args):
        for instance in cls._snapshot.values():
            func(instance, **args)
    
    @classmethod
    def snapshot_registry(cls):
        """
        Called once per frame at the start of updateAll().
        Produces a stable view of all alive players.
        """
        with cls.registry_lock:
            cls._snapshot = {
                id: instance
                for id, instance in cls.registry.items()
                if instance.get_is_alive()
            }
            cls.registry = cls._snapshot