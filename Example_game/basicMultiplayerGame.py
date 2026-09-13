import threading
import time
from GameUtils import *
import pygame
from math import *

class Game:

    # INITIALIZATION STUFF
    def __init__(self):
        pygame.init()
        self.networkManager = self.initializeNetworkManager()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font('assets/Ubuntu-Regular.ttf', 16)
        
        self.drawWindow = pygame.display.set_mode((GameLib.WIDTH, GameLib.HEIGHT))

        self.MotionBlurHandler = GameLib.MotionBlurManager(GameLib.MAX_BLUR_FRAMES)
        self.particleManager = GameLib.ParticleSystem(1)
        self.playercolor = (0,255,0)
        self.conncolor = (255,0,0)
        
        self.player = GameLib.Player(self.particleManager,self.playercolor)

        self.projectiles = []
        self.networkManager.start()
        self.networkLoop = True

        recvthr = threading.Thread(target=self.safe_recv_msg,daemon=True)
        recvthr.start()

        self.debug = False
        if __file__.endswith(".py"):
            self.debug = True
        self.main()
    
    def initializeNetworkManager(self):
        """
        does exactly what it says. it initializes the network manager.
        """
        self.is_host = False
        self.host_ip = None

        while not self.host_ip and self.is_host == False:
            self.host_ip = input("peer ip address (or just leave blank to host): ")
            if self.host_ip == "":
                self.is_host = True
                # break
            elif len(self.host_ip.split(".")) != 4:
                print("that is not a valid IPv4 address!")
                self.host_ip = None

        if self.is_host:
            print("please note that no encryption is likely faster and lower latency")
            encryptionInput = input("would you like to use encryption (y/n)? ").lower()
            self.useEncryption = encryptionInput.startswith("y")
        else:
            encryptionInput = input("is the host using encryption (y/n)? ").lower()
            self.useEncryption = encryptionInput.startswith("y")

        key=None
        salt=None

        if self.useEncryption:
            if self.is_host:
                print("if you leave any of the following inputs blank, tell client to do the same, otherwise wont work")
            print("encryption key (leave blank to use a default key):")
            key = input("> ")
            if key == "":
                key = multiplayerlib.DEFAULT_KEY
            try:
                print("encryption salt (an integer, if invalid input or no input is given, salt will be default):")
                salt = int(input("> "))
            except:
                salt = multiplayerlib.DEFAULT_SALT
                if self.is_host:
                    print("salt is default value")
        self.networkManager = multiplayerlib.NetworkManager(self.is_host,self.host_ip,use_encryption=self.useEncryption,encryption_key=key,encryption_salt=salt)
        return self.networkManager
    
    # MULTIPLAYER PACKET HANDLING
    def _update_network(self):
        """
        gets playerdata packet and then hands to network manager to send
        """
        try:
            packet = self.player.createPositionPacket()
            self.networkManager.safe_send(packet)
        except:
            pass

    def update_network_thread(self):
        """
        loop run with interval specified in multiplayerlib constants that updates the server.
        """
        while self.networkManager.running:
            if not self.networkLoop:
                break
            self._update_network()
            time.sleep(GameLib.POSITIONUPDATEINTERVAL)

    def safe_recv_msg(self):
        """
        safely read latest messages from network manager queue and then hand packets off to a separate thread to be interpreted
        """
        while self.networkManager.running:
            msg = self.networkManager.safe_receive()
            try:
                if msg:
                    if time.time()-msg.get("timestamp",0) > 1:
                        continue
                    if msg.get("type") == "quit":
                        if not self.is_host:
                            self.networkManager.close()
                            self.networkLoop = False
                            break
                    threading.Thread(target=self._update_conn_with_packet,args=(msg,),daemon=True).start()
                    
            except:
                pass

    def _update_conn_with_packet(self,msg):
        """
        interprets and handles the packet recieved in safe_recv_msg
        
        :param msg: the packet
        """
        packet_type = msg.get("type")
        conn = GameLib.ConnectedPlayer.getInstance(self.particleManager,self.conncolor,msg.get("ID"))
        if packet_type == "playerdata":
            prevdeaths = conn.deaths
            conn.updateWithPositionPacket(msg)
            if conn.deaths > prevdeaths:
                self.player.health = 100
        elif packet_type == "shoot":
            bullet = GameLib.Projectile(msg.get("pos",conn.rect.center),msg.get("vec",conn.fire_wpn()),(255,255,0),conn,GameLib.BULLET_DMG)
            bullet.update(conn.getLatency(msg))
            conn.heartbeat()
            self.projectiles.append(bullet)
        else:
            print(f"unrecognized packet type: {packet_type}")

    # GAME LOOPS
    def update(self,dt,mousePos):
        """
        game update loop
        """
        self.player.update(mousePos,dt)
        GameLib.ConnectedPlayer.updateAll(dt)
        self.player.hitCheck(self.projectiles)
        GameLib.ConnectedPlayer.hitCheckAll(self.projectiles)

        for projectile in self.projectiles:
            projectile.update(dt)
        
        self.particleManager.update(dt)
        for projectile in self.projectiles:
            if projectile.hit:
                self.projectiles.remove(projectile)

        if GameLib.POSITION_UPDATE_PACKET_IN_MAIN_LOOP:
            self._update_network()

    def draw(self):
        """
        draws all sprites and objects onto the game surface.
        """
        self.drawWindow.fill((150,150,150))
        if GameLib.MOTION_BLUR:
            tmp = self.MotionBlurHandler.createBlurSurface(self.drawWindow)
            self.MotionBlurHandler.drawParticleManager(self.particleManager,self.drawWindow)
            self.MotionBlurHandler.drawPlayerObjToBlurSurface(self.player,self.font,self.drawWindow)
            for conn in GameLib.ConnectedPlayer.registry:
                self.MotionBlurHandler.drawPlayerObjToBlurSurface(conn,self.font,self.drawWindow)
            for projectile in self.projectiles:
                projectile.draw(self.drawWindow)
            self.MotionBlurHandler.drawBlurFrames(self.drawWindow)
        else:
            self.particleManager.draw(self.drawWindow)
            self.player.draw(self.drawWindow,self.font)
            GameLib.ConnectedPlayer.drawAll(self.drawWindow,self.font)
            for projectile in self.projectiles:
                projectile.draw(self.drawWindow)
        GameLib.drawVignette(self.drawWindow,self.player)

    def mainloop(self):
        """Run the main loop"""
        dt = self.clock.tick(60) / 1000.0
        mousePos = pygame.mouse.get_pos()
        # mousePos = (mousePos[0]*GameLib.WIDTH/GameLib.SCREENWIDTH,mousePos[1]*GameLib.HEIGHT/GameLib.SCREENHEIGHT)
        self.update(dt,mousePos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                bulletVelo = self.player.fire_wpn()
                if bulletVelo:
                    bulletpos = [self.player.rect.centerx+20*cos(self.player.get_rotation()),self.player.rect.centery+20*-sin(self.player.get_rotation())]
                    bullet = GameLib.Projectile(bulletpos,bulletVelo,(255,255,0),self.player,GameLib.BULLET_DMG)
                    self.projectiles.append(bullet)
                    msg = {
                        "type": "shoot",
                        "pos":bulletpos,
                        "vec":bulletVelo,
                        "timestamp":time.time(),
                        "ID":self.player.ID
                    }
                    self.networkManager.safe_send(msg)

        self.draw()
        pygame.display.flip()
        return True

    def main(self):
        self.gameloop = True
        if not GameLib.POSITION_UPDATE_PACKET_IN_MAIN_LOOP:
            sendthr = threading.Thread(target=self.update_network_thread,daemon=True)
            sendthr.start()
        while self.gameloop:
            self.gameloop = self.mainloop()
            if not self.networkLoop:
                break
            
        if self.networkManager.running:
            msg = {
                "type":"quit"
            }
            self.networkManager.safe_send(msg)
            time.sleep(1)
        self.networkManager.close()
        pygame.quit()

if __name__ == "__main__":
    game = Game()