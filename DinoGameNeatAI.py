"""
# Dinosaur Game with NEAT AI playing the Game
#      - based off the Google Chrome Offline Game
# Created By
#      - Josh Blayone
# 01/26/2020
"""

import os
import sys
import pygame
import neat
import random
import time
import visualize
import pickle
from pygame import *

#### Variables ####

debug = False

screen_size = (width, height) = (600*2, 150*2)
FPS = 60
gravity = 0.6
defaultgamespeed = 5
ground_height = 50

black = (0, 0, 0)
white = (255, 255, 255)
background_colour = (235, 235, 235)

high_score = 0
gen = 0
stats = 0

current_path = os.path.dirname(__file__)
resource_path = os.path.join(current_path, 'resources')

#### PyGame Setup ####

pygame.init()
pygame.font.init()

stat_font = pygame.font.SysFont("comicsans", 25)

screen = pygame.display.set_mode(screen_size)
clock = pygame.time.Clock()
pygame.display.set_caption("Dino Run")

#### Defintions ####

def load_image(name, sizex=-1, sizey=-1, colorkey=None):
    """
    Load in an image and its rect from a file
    """
    fullname = os.path.join(resource_path, name)
    image = pygame.image.load(fullname)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)

    if sizex != -1 or sizey != -1:
        image = pygame.transform.scale(image, (sizex, sizey))

    return (image, image.get_rect())

def load_sprite_sheet(sheetname, nx, ny, scalex = -1, scaley = -1, colorkey = None):
    """
    Load in sprites from a sprite sheet image
    """
    fullname = os.path.join(resource_path, sheetname)
    sheet = pygame.image.load(fullname)
    sheet = sheet.convert()

    sheet_rect = sheet.get_rect()

    sprites = []

    sizex = sheet_rect.width/nx
    sizey = sheet_rect.height/ny

    for i in range(0,ny):
        for j in range(0,nx):
            rect = pygame.Rect((j*sizex,i*sizey,sizex,sizey))
            image = pygame.Surface(rect.size)
            image = image.convert()
            image.blit(sheet,(0,0),rect)

            if colorkey is not None:
                if colorkey is -1:
                    colorkey = image.get_at((0,0))
                image.set_colorkey(colorkey,RLEACCEL)

            if scalex != -1 or scaley != -1:
                image = pygame.transform.scale(image,(scalex,scaley))

            sprites.append(image)

    sprite_rect = sprites[0].get_rect()

    return sprites,sprite_rect

def drawStats(win, score, gen, dinos):
    """
    Will show what the current score is, what generation it is, and how many birds are still alive
    """
    if gen == 0:
        gen = 1

    # score
    score_label = stat_font.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (width - score_label.get_width() - 15, 10))

    # generations
    score_label = stat_font.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    # alive
    score_label = stat_font.render("Alive: " + str(len(dinos)),1,(255,255,255))
    win.blit(score_label, (10, 50))

#### Classes ####

class Dino():
    """
    Dino class representing the Dinosaur Player
    """
    def __init__(self, sizex=-1, sizey=-1):
        self.images, self.rect = load_sprite_sheet('dino.png', 5, 1, sizex, sizey, -1)
        self.images1, self.rect1 = load_sprite_sheet('dino_ducking.png', 2, 1, 59, sizey, -1)
        self.groundX = height - ground_height
        self.rect.bottom = self.groundX
        self.rect.left = width/15
        self.image = self.images[0]
        self.posY = 0
        self.posX = 0
        self.velY = 0
        self.score = 0
        self.gravity = gravity
        self.speed = 0
        self.sizeWidth, self.sizeHeight = (20, 40)
        self.isJumping = False
        self.startJump = False
        self.index = 2
        self.isDead = False
        self.isDucking = False
        self.counter = 0
        self.movement = [0,0]
        self.jumpSpeed = 11.5

        self.stand_pos_width = self.rect.width
        self.duck_pos_width = self.rect.width

        # create varible for the dino AI to "see"
        self.distance_to_next_obstacle = 0
        self.height_of_obstacle = 0
        self.width_of_obstacle = 0
        self.isBird = False
        self.players_y_position = 0
        self.gap_between_obstacles = 0

    def draw(self): # Draws Dino onto the screen
        #draw.rect(screen, black, (50, (height-ground_height-self.sizeHeight)-self.posY, self.sizeWidth, self.sizeHeight), 0)
        screen.blit(self.image, self.rect)

    def jump(self): # Makes the Dino jump
        if not self.isJumping:
            if self.isDucking:
                self.duck()

            self.movement[1] = -1*self.jumpSpeed
            self.startJump = True
            self.isJumping = True
            self.index = 0

    def duck(self): # Makes the Dino duck
        if not self.isJumping:
            if self.isDucking:
                self.isDucking = False
                if(self.index == 0):
                    self.image = self.images[3]
                else:
                    self.image = self.images[2]
            else:
                self.isDucking = True
                if(self.index == 2):
                    self.image = self.images1[1]
                else:
                    self.image = self.images1[0]

    def ducktoggle(self, on): # Makes the Dino duck (togglable)
        if not self.isJumping:
            if not on:
                self.isDucking = False
                if(self.index == 0):
                    self.image = self.images[3]
                else:
                    self.image = self.images[2]
            elif on:
                self.isDucking = True
                if(self.index == 2):
                    self.image = self.images1[1]
                else:
                    self.image = self.images1[0]


    def update(self): # Runs the updates function as well as updating the X and Y position of the dino for the AI
        if not self.isDead:
            self.updates()

        self.posX = self.rect.right
        self.posY = self.rect.bottom - self.groundX

    def updates(self): # Runs the movement and drawing funtions and creates the animation of the dino
        self.counter += 1

        if(self.counter == 15):
            if(not self.isJumping):
                if(not self.isDucking):
                    self.image = self.images[3]
                    self.index = 3
                else:
                    self.image = self.images1[1]
                    self.index = 1
        if(self.counter >= 30):
            if(not self.isJumping):
                if(not self.isDucking):
                    self.image = self.images[2]
                    self.index = 2
                else:
                    self.image = self.images1[0]
                    self.index = 0
                self.counter = 0

        if not self.isDucking:
            self.rect.width = self.stand_pos_width
        else:
            self.rect.width = self.duck_pos_width

        if self.isJumping:
            self.movement[1] = self.movement[1] + self.gravity

        if(self.isDead):
            self.image = self.images[4]
            self.index = 4

        if(not self.isDead):
            self.score += 1

        self.move()
        self.draw()
        #self.debug()

    def checkbounds(self): # Checks is the dino is going through the floor
        if(self.rect.bottom >= self.groundX-1):
            self.rect.bottom = self.groundX
            self.movement = [0,0]
            self.isJumping = False
            self.startJumping = False
            self.index = 3

    def move(self): # Moves the dino's position
        if(self.isJumping == True and self.startJump == False):
            self.checkbounds()
        else:
            self.startJump = False

        self.rect = self.rect.move(self.movement)

    def debug(self): # Will print many varibles for debuging dino issues
        os.system('clear')
        print("isJumping: " + str(self.isJumping))
        print("GroundX: " + str(self.groundX))
        print("rect.bottom: " + str(self.rect.bottom))
        print("movement: " + str(self.movement))

class CactusTemp():
    """
    Used to fake an obstacle if there are none on the screen such as at the start
    """
    def __init__(self):
        self.posX = width + 1
        self.posY = 112
        self.width = 50

class Cactus(pygame.sprite.Sprite):
    """
    Cactus class representing the cactus obstacles
    """
    def __init__(self, speed=5, sizex = -1, sizey = -1):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.images, self.rects = load_sprite_sheet('cacti-small.png',3,1,sizex,sizey,-1)
        self.images1, self.rects1 = load_sprite_sheet('cacti-big.png',3,1,sizex,sizey,-1)
        self.groundX = height - ground_height
        self.rects.bottom = self.groundX
        self.rects1.bottom = self.groundX
        self.speed = speed
        self.rects.left = width + self.rects.width + self.speed
        self.rects1.left = width + self.rects1.width + self.speed
        self.rect = self.rects
        self.posX = 0
        self.posY = 0
        self.width = 0
        self.height = 0

        # Randomize the cactus
        if(random.randrange(0,1) == 1):
            self.image = self.images1[random.randrange(0,3)]
            self.rect = self.rects1
        else:
            self.image = self.images[random.randrange(0,3)]
            self.rect = self.rects

        self.movement = [-1*self.speed,0]

    def draw(self): # Draw the cactus on the screen
        screen.blit(self.image,self.rect)

    def update(self): # Calls the draw functions as well as move the catcus and track it's X and Y position for the AI
        self.rect = self.rect.move(self.movement)

        if self.rect.right < 0:
            self.kill()

        self.draw()

        self.posX = self.rect.left
        self.posY = self.rect.centery
        self.width = self.rect.width

class Bird(pygame.sprite.Sprite):
    """
    Bird class representing the bird obstacles
    """
    def __init__(self, speed=5, sizex=-1,sizey=-1,type = -1):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.images,self.rect = load_sprite_sheet('bird.png',2,1,sizex,sizey,-1)
        self.groundX = height - ground_height
        self.rect.left = width + self.rect.width
        self.image = self.images[0]
        self.movement = [-1*speed,0]
        self.index = 0
        self.counter = 0
        self.isTall = False

        # Randomize Heights of the bird
        self.bird_height = [height*0.82,height*0.74,height*0.65]
        self.height = 100
        if(type == -1):
            self.rando = random.randrange(0,3)
        else:
            self.rando = type
        self.rect.centery = self.bird_height[self.rando]
        if self.rando == 2:
            self.isTall = True
        self.heights_bird = [115, 220, 500]


        self.posX = 0
        self.rposY = self.bird_height[self.rando]
        self.posY = self.heights_bird[self.rando]
        self.width = self.rect.width

    def draw(self): # Draw the bird on the screen
        screen.blit(self.image,self.rect)
        #draw.rect(screen, black, self.rect, 1)

    def update(self): # Move and Draws the bird as well as track its X postion for the AI
        if self.counter % 10 == 0:
            self.index = (self.index+1)%2
        self.image = self.images[self.index]
        self.rect = self.rect.move(self.movement)
        self.counter = (self.counter + 1)
        if self.rect.right < 0:
            self.kill()

        self.posX = self.rect.left
        self.draw()

class TallBirdLine(pygame.sprite.Sprite):
    """
    Will create a line that cannot be passed
    """
    def __init__(self):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.groundX = height - ground_height
        self.rect = pygame.Rect((0,0),(0,0))
        self.posX = 0
        self.posY = height*0.65
        self.rect.height = self.posY
        self.rect.width = 10
        self.rect.topleft = (self.posX, 0)
        self.rect.bottomleft = (self.posX, self.posY)
        #self.image = pygame.Surface((self.width,int(self.posY)))
        #self.image.fill(black)

    def draw(self): # Draw the line on the screen
        #screen.blit(self.image, self.rect)
        draw.rect(screen, background_colour, self.rect, 1)

    def update(self, birdS): # Move and Draws the line with the bird
        if(len(birdS) > 0):
            self.posX = birdS[0].posX
            self.posY = birdS[0].rposY
        if birdS[0].isTall == False:
            self.kill()
        if self.posX < 0:
            self.kill()

        self.rect.height = self.posY
        self.rect.topleft = (self.posX, 0)
        self.rect.bottomleft = (self.posX, self.posY)

        self.draw()


def eval_genomes(genomes, config):
    """
    Runs the simulation of the current population of birds
    and sets their fitness based on the distance they travel
    """
    global screen, gen, FPS
    win = screen
    gen += 1

    # start by creating lists holding the genome itself, the
    # neural network associated with the genome and the
    # dino object that uses that network to play
    nets = []
    dinos = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0 # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        dinos.append(Dino(44, 47))
        ge.append(genome)


    # create input variables that the AI will use to "see"
    distance_to_next_obstacle = 0
    height_of_obstacle = 0
    width_of_obstacle = 0
    isBird = False
    ca = CactusTemp()
    ob = CactusTemp()
    pastOb = 0
    lastOb = 0
    birdcount = 0
    birdCountEnable = False
    secOb = CactusTemp()
    speed = 0
    players_y_position = 0
    gap_between_obstacles = 0

    counter = 0

    # creates a group to store all obstacles on screen
    cacti = pygame.sprite.Group()
    birds = pygame.sprite.Group()
    lines = pygame.sprite.Group()
    last_obstacle = pygame.sprite.Group()

    Cactus.containers = cacti
    Bird.containers = birds
    TallBirdLine.containers = lines

    gamespeed = defaultgamespeed
    score = 0

    visualize.draw_net(config, genome)


    # starts the game
    run = True
    while run and len(dinos) > 0:
        # set the tick rate of the game, clear the screen and draw the ground
        clock.tick(FPS)
        screen.fill(background_colour)
        draw.lines(screen, black, False, [(0, height-ground_height), (width, height-ground_height)])

        # if escape is pressed it will stop the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                    pygame.quit()
                    break
                elif event.key == pygame.K_RIGHT:
                    FPS += 30
                elif event.key == pygame.K_LEFT:
                    FPS -= 30

        # generate the Inputs for the AI, basically what it can see
        for dino in dinos:
            d = dino.posX
            tempOb = ob
            cactiSprites = cacti.sprites()
            birdSprites = birds.sprites()
            # will find the closest obstacle whether its a bird or cactus
            if(len(cactiSprites) != 0 or len(birdSprites) != 0):
                if(len(cactiSprites) != 0):
                    a = cactiSprites[0]
                else:
                    a = CactusTemp()
                if(len(cactiSprites) > 1):
                    b = cactiSprites[1]
                else:
                    b = CactusTemp()
                if(a.posX < d):
                    ca = b
                    secOb = a
                elif(b.posX < d):
                    ca = a
                    secOb = b
                elif(b.posX > a.posX):
                    ca = a
                    secOb = b
                elif(a.posX > b.posX):
                    ca = b
                    secOb = a
                else:
                    ca = a
                    secOb = b
                if(len(birdSprites) > 0):
                    c = birdSprites[0]
                    if(c.posX < d):
                        ob = ca
                        isBird = False
                        secOb = c
                    elif(c.posX > ca.posX):
                        ob = ca
                        isBird = False
                        secOb = c
                    elif(ca.posX > c.posX):
                        ob = c
                        isBird = True
                        secOb = ca
                    else:
                        ob = c
                        isBird = True
                        secOb = ca
                else:
                    isBird = False
                    ob = ca
                # describe things about the closest obstacle and second closest
                dino.distance_to_next_obstacle = ob.posX - dino.posX
                dino.height_of_obstacle = ob.posY
                dino.width_of_obstacle = ob.width
                dino.gap_between_obstacles = secOb.posX - ob.posX
            if tempOb != ob:
                lastOb = tempOb
            dino.isBird = isBird
            dino.speed = gamespeed
            dino.players_y_position = abs(dino.posY)


        for x, dino in enumerate(dinos): # give each dino a fitness of 0.1 for each frame it stays alive
            ge[x].fitness += 0.1
            dino.update()

            # send the AI what the dino can see
            output = nets[dinos.index(dino)].activate((dino.distance_to_next_obstacle, dino.height_of_obstacle, dino.width_of_obstacle, int(dino.isBird), dino.speed, dino.players_y_position, dino.gap_between_obstacles))

            # will receives what the output of the AI is using the tanh activation function
            if output[0] > 0.5:
                dino.jump()
            elif output[1] > 0:
                dino.ducktoggle(True)
            elif output[1] < 0:
                dino.ducktoggle(False)

        # will check for any collisions with obstacles and if so remove that dino player from the game
        for dino in dinos:
            for c in cacti:
                c.movement[0] = -1*gamespeed
                if pygame.sprite.collide_mask(dino, c):
                    ge[dinos.index(dino)].fitness -= 1
                    nets.pop(dinos.index(dino))
                    ge.pop(dinos.index(dino))
                    dinos.pop(dinos.index(dino))
                    dino.isDead = True

            for b in birds:
                b.movement[0] = -1*gamespeed
                if pygame.sprite.collide_mask(dino, b):
                    ge[dinos.index(dino)].fitness -= 1
                    nets.pop(dinos.index(dino))
                    ge.pop(dinos.index(dino))
                    dinos.pop(dinos.index(dino))
                    dino.isDead = True

            try:
                for li in lines:
                    if li.rect.colliderect(dino):
                        ge[dinos.index(dino)].fitness -= 1
                        nets.pop(dinos.index(dino))
                        ge.pop(dinos.index(dino))
                        dinos.pop(dinos.index(dino))
                        dino.isDead = True
            except:
                continue

        # will place obstacles randomly
        if(len(cacti) < 2):
            if(len(cacti) == 0):
                last_obstacle.empty()
                last_obstacle.add(Cactus(gamespeed, 40,40))
                isBird = False
            else:
                for l in last_obstacle:
                    if(l.rect.right < width*0.7 and random.randrange(0,50) == 10):
                        last_obstacle.empty()
                        last_obstacle.add(Cactus(gamespeed, 40, 40))
                        isBird = False

        if len(birds) == 0 and random.randrange(0, 20) == 10:# and counter > 500:
            for l in last_obstacle:
                if l.rect.right < width*0.8:
                    last_obstacle.empty()
                    rando = random.randrange(0,3)
                    last_obstacle.add(Bird(gamespeed, 46, 40, rando))
                    if(rando == 2):
                        lines.add(TallBirdLine())
                    isBird = True

        # for every 100 points (score), is a checkpoint so each dino will receive a reward
        if(counter % 100 == 0):
            for genome in ge:
                genome.fitness += 5

        # for every 1000 points, speed the game up by 1
        if(counter % 1000 == 0):
            gamespeed += 1

        # update the obstacles as well as the screen
        lines.update(birds.sprites())
        birds.update()
        cacti.update()

        # display stats
        drawStats(screen, score, gen, dinos)


        counter += 1
        if birdCountEnable:
            birdcount += 1
        score += 1
        display.update()

    visualize.plot_stats(stats)

def run(config_file):
    global stats
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)
    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    #p.add_reporter(neat.Checkpointer(5))

    # Run for up to 50 generations.
    winner = p.run(eval_genomes, 10000)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))



def debugGameMechanics():
    """
    Used to test the game for debuging purposes, allows the user to play the game and print what the AI would see
    """
    global high_score
    gameOver = False
    gameQuit = False
    demo = False
    counter = 0
    gamespeed = defaultgamespeed

    dino = Dino(44, 47)

    cacti = pygame.sprite.Group()

    birds = pygame.sprite.Group()
    lines = pygame.sprite.Group()
    last_obstacle = pygame.sprite.Group()

    distance_to_next_obstacle = 0
    height_of_obstacle = 0
    width_of_obstacle = 0
    isBird = False
    ca = CactusTemp()
    ob = CactusTemp()
    secOb = CactusTemp()
    speed = 0
    players_y_position = 0
    gap_between_obstacles = 0

    Cactus.containers = cacti
    Bird.containers = birds
    TallBirdLine.containers = lines


    while not gameQuit:
        while not gameOver:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    gameQuit = True
                    gameOver = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP:
                        dino.jump()
                    if event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        dino.duck()
                    if event.key == pygame.K_ESCAPE:
                        gameQuit = True
                        gameOver = True

            screen.fill(background_colour)

            draw.lines(screen, black, False, [(0, height-ground_height), (width, height-ground_height)])



            if not demo:
                for c in cacti:
                    c.movement[0] = -1*gamespeed
                    if pygame.sprite.collide_mask(dino, c):
                        dino.isDead = True

                for b in birds:
                    b.movement[0] = -1*gamespeed
                    if pygame.sprite.collide_mask(dino, b):
                        dino.isDead = True

                for li in lines:
                    if li.rect.colliderect(dino):
                        dino.isDead = True

            if(len(cacti) < 2):
                if(len(cacti) == 0):
                    last_obstacle.empty()
                    last_obstacle.add(Cactus(gamespeed, 40,40))
                    isBird = False
                else:
                    for l in last_obstacle:
                        if(l.rect.right < width*0.7 and random.randrange(0,50) == 10):
                            last_obstacle.empty()
                            last_obstacle.add(Cactus(gamespeed, 40, 40))
                            isBird = False

            if len(birds) == 0 and random.randrange(0, 20) == 10: #and counter > 500:
                for l in last_obstacle:
                    if l.rect.right < width*0.8:
                        last_obstacle.empty()
                        last_obstacle.add(Bird(gamespeed, 46, 40))
                        lines.add(TallBirdLine())
                        isBird = True

            lines.update(birds.sprites())
            dino.update()
            birds.update()
            cacti.update()

            display.update()
            clock.tick(FPS)

            if dino.isDead:
                gameOver = True
                if(dino.score > high_score):
                    high_score = dino.score

            counter = (counter + 1)
            os.system('clear')

            d = dino.posX
            cactiSprites = cacti.sprites()
            if(len(cactiSprites) > 0):
                a = cactiSprites[0]
            if(len(cactiSprites) > 1):
                b = cactiSprites[1]
            else:
                b = CactusTemp()

            if(a.posX < d):
                ca = b
                secOb = a
            elif(b.posX < d):
                ca = a
                secOb = b
            elif(b.posX > a.posX):
                ca = a
                secOb = b
            elif(a.posX > b.posX):
                ca = b
                secOb = a
            else:
                ca = a
                secOb = b

            birdSprites = birds.sprites()
            if(len(birdSprites) > 0):
                c = birdSprites[0]
                if(c.posX < d):
                    ob = ca
                    isBird = False
                    secOb = c
                elif(c.posX > ca.posX):
                    ob = ca
                    isBird = False
                    secOb = c
                elif(ca.posX > c.posX):
                    ob = c
                    isBird = True
                    secOb = ca
                else:
                    ob = c
                    isBird = True
                    secOb = ca
            else:
                isBird = False
                ob = ca

            distance_to_next_obstacle = ob.posX - dino.posX
            height_of_obstacle = ob.posY
            width_of_obstacle = ob.width

            speed = gamespeed
            players_y_position = abs(dino.posY)
            gap_between_obstacles = secOb.posX - ob.posX


            print("distance_to_next_obstacle: " + str(distance_to_next_obstacle))
            print("height_of_obstacle: " + str(height_of_obstacle))
            print("width_of_obstacle: " + str(width_of_obstacle))
            print("isBird: " + str(isBird))
            print("speed: " + str(speed))
            print("players_y_position: " + str(players_y_position))
            print("gap_between_obstacles: " + str(gap_between_obstacles))


        if gameQuit:
            break

        while gameOver:
            for event in pygame.event.get():
                if(event.type == pygame.QUIT):
                    gameQuit = True
                    gameOver = False
                if(event.type == pygame.KEYDOWN):
                    if(event.key == pygame.K_ESCAPE):
                        gameQuit = True
                        gameOver = False

                    if(event.key == pygame.K_RETURN or event.key == pygame.K_SPACE):
                        gameOver = False
                        debugGameMechanics()


            display.update()
            clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    if(not debug):
        local_dir = os.path.dirname(__file__)
        config_path = os.path.join(local_dir, 'config-feedforward.txt')
        run(config_path)
    else:
        debugGameMechanics()
