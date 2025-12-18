import ctypes
import random
import threading
import time
from GameUtils import *
import pygame
from math import *

# MULTIPLAYER PACKET HANDLING
def update_network():
    """
    gets playerdata packet and then hands to network manager to send
    """
    global networkManager,player
    try:
        packet = player.createPositionPacket()
        networkManager.safe_send(packet)
    except:
        pass

def update_network_thread():
    """
    loop run with interval specified in multiplayerlib constants that updates the server.
    """
    global networkManager
    while networkManager.running:
        global networkLoop,gameloop
        if not networkLoop:
            break
        update_network()
        time.sleep(MultiplayerLib.POSITIONUPDATEINTERVAL)

def safe_recv_msg():
    """
    safely read latest messages from network manager queue and then hand packets off to a separate thread to be interpreted
    """
    global networkManager
    while networkManager.running:
        global conn,projectiles,is_host,networkLoop
        msg = networkManager.safe_receive()
        try:
            if msg:
                if time.time()-msg.get("timestamp",0) > 1:
                    continue
                if msg.get("type") == "quit":
                    conn = GameLib.ConnectedPlayer()
                    if not is_host:
                        networkManager.close()
                        networkLoop = False
                        break
                threading.Thread(target=update_conn_with_packet,args=(msg,),daemon=True).start()
                
        except:
            pass

def update_conn_with_packet(msg):
    """
    interprets and handles the packet recieved in safe_recv_msg
    
    :param msg: the packet
    """
    global conn,networkLoop
    packet_type = msg.get("type")
    if packet_type == "playerdata":
        prevdeaths = conn.deaths
        conn.updateWithPositionPacket(msg)
        if conn.deaths > prevdeaths:
            player.health = 100
    elif packet_type == "shoot":
        bullet = GameLib.Projectile(msg.get("pos",conn.rect.center),msg.get("vec",conn.fire_wpn()),(255,255,0),conn,GameLib.BULLET_DMG)
        bullet.update(conn.getLatency(msg))
        projectiles.append(bullet)
    else:
        print(f"unrecognized packet type: {packet_type}")

# GAME LOOPS
def update(dt,mousePos):
    """
    game update loop
    """
    global player,projectiles,conn,particleManager,networkManager
    player.update(mousePos,dt)
    conn.update(dt)
    player.hitCheck(projectiles)
    conn.hitCheck(projectiles)

    for projectile in projectiles:
        projectile.update(dt)
    
    particleManager.update(dt)
    for projectile in projectiles:
        if projectile.hit:
            projectiles.remove(projectile)

    if MultiplayerLib.POSITION_UPDATE_PACKET_IN_MAIN_LOOP:
        update_network()

def draw():
    """
    draws all sprites and objects onto the game surface.
    """
    global player,projectiles,conn,particleManager,networkManager,drawWindow
    drawWindow.fill((150,150,150))
    if GameLib.MOTION_BLUR:
        tmp = MotionBlurHandler.createBlurSurface(drawWindow)
        MotionBlurHandler.drawParticleManager(particleManager,drawWindow)
        MotionBlurHandler.drawPlayerObjToBlurSurface(player,font,drawWindow)
        MotionBlurHandler.drawPlayerObjToBlurSurface(conn,font,drawWindow)
        for projectile in projectiles:
            projectile.draw(drawWindow)
        MotionBlurHandler.drawBlurFrames(drawWindow)
    else:
        particleManager.draw(drawWindow)
        player.draw(drawWindow,font)
        conn.draw(drawWindow,font)
        for projectile in projectiles:
            projectile.draw(drawWindow)
    GameLib.drawVignette(drawWindow,player)

def mainloop():
    """Run the main loop"""
    global drawWindow,player,projectiles,conn,particleManager,networkManager,debug
    dt = clock.tick(60) / 1000.0
    mousePos = pygame.mouse.get_pos()
    # mousePos = (mousePos[0]*GameLib.WIDTH/GameLib.SCREENWIDTH,mousePos[1]*GameLib.HEIGHT/GameLib.SCREENHEIGHT)
    update(dt,mousePos)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            bulletVelo = player.fire_wpn()
            if bulletVelo:
                bulletpos = [player.rect.centerx+20*cos(player.get_rotation()),player.rect.centery+20*-sin(player.get_rotation())]
                bullet = GameLib.Projectile(bulletpos,bulletVelo,(255,255,0),player,GameLib.BULLET_DMG)
                projectiles.append(bullet)
                msg = {
                    "type": "shoot",
                    "pos":bulletpos,
                    "vec":bulletVelo,
                    "timestamp":time.time()
                }
                networkManager.safe_send(msg)

    draw()
    pygame.display.flip()
    return True

def main():
    global gameloop,networkManager
    gameloop = True
    if not MultiplayerLib.POSITION_UPDATE_PACKET_IN_MAIN_LOOP:
        sendthr = threading.Thread(target=update_network_thread,daemon=True)
        sendthr.start()
    while gameloop:
        global networkLoop
        gameloop = mainloop()
        if not networkLoop:
            break
        
    if networkManager.running:
        msg = {
            "type":"quit"
        }
        networkManager.safe_send(msg)
        time.sleep(1)
    networkManager.close()
    pygame.quit()

def initializeNetworkManager():
    global is_host,host_ip,useEncryption
    is_host = False
    host_ip = None

    while not host_ip and is_host == False:
        host_ip = input("peer ip address (or just leave blank to host): ")
        if host_ip == "":
            is_host = True
            # break
        elif len(host_ip.split(".")) != 4:
            print("that is not a valid IPv4 address!")
            host_ip = None

    if is_host:
        print("please note that no encryption is likely faster and lower latency")
        encryptionInput = input("would you like to use encryption (y/n)? ").lower()
        useEncryption = encryptionInput.startswith("y")
    else:
        encryptionInput = input("is the host using encryption (y/n)? ").lower()
        useEncryption = encryptionInput.startswith("y")

    key=None
    salt=None

    if useEncryption:
        if is_host:
            print("if you leave any of the following inputs blank, tell client to do the same, otherwise wont work")
        print("encryption key (leave blank to use a default key):")
        key = input("> ")
        if key == "":
            key = MultiplayerLib.DEFAULT_KEY
        try:
            print("encryption salt (an integer, if invalid input or no input is given, salt will be default):")
            salt = int(input("> "))
        except:
            salt = MultiplayerLib.DEFAULT_SALT
            if is_host:
                print("salt is default value")
    networkManager = MultiplayerLib.NetworkManager(is_host,host_ip,use_encryption=useEncryption,encryption_key=key,encryption_salt=salt)
    return networkManager

if __name__ == "__main__":
    pygame.init()
    networkManager = initializeNetworkManager()
    clock = pygame.time.Clock()
    font = pygame.font.Font('assets/Ubuntu-Regular.ttf', 16)
    
    drawWindow = pygame.display.set_mode((GameLib.WIDTH, GameLib.HEIGHT))

    MotionBlurHandler = GameLib.MotionBlurManager(GameLib.MAX_BLUR_FRAMES)
    particleManager = GameLib.ParticleSystem(1)

    if is_host:
        playercolor = (0,0,255)
        conncolor = (255,0,0)
    else:
        playercolor = (255,0,0)
        conncolor = (0,0,255)
    
    player = GameLib.Player(particleManager,playercolor)
    conn = GameLib.ConnectedPlayer(particleManager,conncolor)

    projectiles = []
    networkManager.start()
    networkLoop = True

    recvthr = threading.Thread(target=safe_recv_msg,daemon=True)
    recvthr.start()

    debug = False
    if __file__.endswith(".py"):
        debug = True
    main()