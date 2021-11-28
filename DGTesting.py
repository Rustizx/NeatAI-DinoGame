# Dinosaur Game
#      - based off the Google Chrome Offline Game
# Created By
#      - Josh Blayone
# 12/12/2019

import os
import sys
import pygame
import random
from pygame import *

#### Variables ####

screen_size = (width, height) = (600*2, 150*2)
FPS = 60
gravity = 0.6
gamespeed = 5
ground_height = 50

black = (0, 0, 0)
white = (255, 255, 255)
background_colour = (235, 235, 235)

high_score = 0

current_path = os.path.dirname(__file__)
resource_path = os.path.join(current_path, 'resources')

#### PyGame Setup ####

pygame.init()

screen = pygame.display.set_mode(screen_size)
clock = pygame.time.Clock()
pygame.display.set_caption("Dino Run")

#### Defintions ####

def load_image(
    name,
    sizex=-1,
    sizey=-1,
    colorkey=None,
    ):

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

def load_sprite_sheet(
        sheetname,
        nx,
        ny,
        scalex = -1,
        scaley = -1,
        colorkey = None,
        ):
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

def disp_gameOver_msg(retbutton_image,gameover_image):
    retbutton_rect = retbutton_image.get_rect()
    retbutton_rect.centerx = width / 2
    retbutton_rect.top = height*0.52

    gameover_rect = gameover_image.get_rect()
    gameover_rect.centerx = width / 2
    gameover_rect.centery = height*0.35

    screen.blit(retbutton_image, retbutton_rect)
    screen.blit(gameover_image, gameover_rect)

def extractDigits(number):
    if number > -1:
        digits = []
        i = 0
        while(number/10 != 0):
            digits.append(number%10)
            number = int(number/10)

        digits.append(number%10)
        for i in range(len(digits),5):
            digits.append(0)
        digits.reverse()
        return digits

#### Classes ####

class Dino():
    def __init__(self, sizex=-1, sizey=-1):
        self.images, self.rect = load_sprite_sheet('dino.png', 5, 1, sizex, sizey, -1)
        self.images1, self.rect1 = load_sprite_sheet('dino_ducking.png', 2, 1, 59, sizey, -1)
        self.groundX = height - ground_height
        self.rect.bottom = self.groundX
        self.rect.left = width/15
        self.image = self.images[0]
        self.posY = 0
        self.velY = 0
        self.score = 0
        self.gravity = gravity
        self.speed = gamespeed
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

    def draw(self):
        #draw.rect(screen, black, (50, (height-ground_height-self.sizeHeight)-self.posY, self.sizeWidth, self.sizeHeight), 0)
        screen.blit(self.image, self.rect)

    def jump(self):
        if not self.isJumping:
            if self.isDucking:
                self.duck()

            self.movement[1] = -1*self.jumpSpeed
            self.startJump = True
            self.isJumping = True
            self.index = 0

    def duck(self):
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

    def update(self):
        if not self.isDead:
            self.updates()

    def updates(self):
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

    def checkbounds(self):
        if(self.rect.bottom >= self.groundX-1):
            self.rect.bottom = self.groundX
            self.movement = [0,0]
            self.isJumping = False
            self.startJumping = False
            self.index = 3

    def move(self):

        if(self.isJumping == True and self.startJump == False):
            self.checkbounds()
        else:
            self.startJump = False

        self.rect = self.rect.move(self.movement)

    def debug(self):
        os.system('clear')
        print("isJumping: " + str(self.isJumping))
        print("GroundX: " + str(self.groundX))
        print("rect.bottom: " + str(self.rect.bottom))
        print("movement: " + str(self.movement))


class Cactus(pygame.sprite.Sprite):
    def __init__(self, speed=5, sizex = -1, sizey = -1, type = 0):
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
        self.type = type

        if(type == 0):
            if(random.randrange(0,1) == 1):
                self.image = self.images1[random.randrange(0,3)]
                self.rect = self.rects1
            else:
                self.image = self.images[random.randrange(0,3)]
                self.rect = self.rects
        # elif(type == 1):
        #     self.image = self.images[random.randrange(0,3)]
        #     self.rect = self.rects1
        # else:
        #     self.image = self.images[random.randrange(0,3)]
        #     self.rect = self.rects

        self.movement = [-1*self.speed,0]

    def draw(self):
        screen.blit(self.image,self.rect)

    def update(self):
        self.rect = self.rect.move(self.movement)

        if self.rect.right < 0:
            self.kill()

        self.draw()

class Bird(pygame.sprite.Sprite):
    def __init__(self, speed=5, sizex=-1,sizey=-1):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.images,self.rect = load_sprite_sheet('bird.png',2,1,sizex,sizey,-1)
        self.bird_height = [height*0.82,height*0.75,height*0.65]
        self.rect.centery = self.bird_height[random.randrange(0,3)]
        self.rect.left = width + self.rect.width
        self.image = self.images[0]
        self.movement = [-1*speed,0]
        self.index = 0
        self.counter = 0

    def draw(self):
        screen.blit(self.image,self.rect)

    def update(self):
        if self.counter % 10 == 0:
            self.index = (self.index+1)%2
        self.image = self.images[self.index]
        self.rect = self.rect.move(self.movement)
        self.counter = (self.counter + 1)
        if self.rect.right < 0:
            self.kill()

        self.draw()

class Scoreboard():
    def __init__(self,x=-1,y=-1):
        self.score = 0
        self.tempimages,self.temprect = load_sprite_sheet('numbers.png',12,1,11,int(11*6/5),-1)
        self.image = pygame.Surface((55,int(11*6/5)))
        self.rect = self.image.get_rect()
        if x == -1:
            self.rect.left = width*0.89
        else:
            self.rect.left = x
        if y == -1:
            self.rect.top = height*0.1
        else:
            self.rect.top = y

    def draw(self):
        screen.blit(self.image,self.rect)

    def update(self,score):
        score_digits = extractDigits(score)
        self.image.fill(background_colour)
        for s in score_digits:
            self.image.blit(self.tempimages[s],self.temprect)
            self.temprect.left += self.temprect.width
        self.temprect.left = 0

        self.draw()

def main():
    global high_score
    gameOver = False
    gameQuit = False
    demo = False
    counter = 0

    dino = Dino(44, 47)
    scb = Scoreboard()

    cacti = pygame.sprite.Group()
    birds = pygame.sprite.Group()
    last_obstacle = pygame.sprite.Group()

    Cactus.containers = cacti
    Bird.containers = birds

    retbutton_image, retbutton_rect = load_image('replay_button.png',35,31,-1)
    gameover_image, gameover_rect = load_image('game_over.png',190,11,-1)


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

                if(len(cacti) < 2):
                    if(len(cacti) == 0):
                        last_obstacle.empty()
                        last_obstacle.add(Cactus(gamespeed, 40,40))
                    else:
                        for l in last_obstacle:
                            if(l.rect.right < width*0.7 and random.randrange(0,50) == 10):
                                last_obstacle.empty()
                                last_obstacle.add(Cactus(gamespeed, 40, 40))

                if len(birds) == 0 and random.randrange(0, 20) == 10 and counter > 500:
                    for l in last_obstacle:
                        if l.rect.right < width*0.8:
                            last_obstacle.empty()
                            last_obstacle.add(Bird(gamespeed, 46, 40))


            dino.update()
            birds.update()
            cacti.update()
            scb.update(dino.score)

            display.update()
            clock.tick(FPS)

            if dino.isDead:
                gameOver = True
                if(dino.score > high_score):
                    high_score = dino.score

            counter = (counter + 1)


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
                        main()

            disp_gameOver_msg(retbutton_image,gameover_image)

            display.update()
            clock.tick(FPS)

    pygame.quit()

main()
