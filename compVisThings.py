import pygame
import numpy as np
import math
from pygame import gfxdraw

size = width, height = 650, 650

hungerWeight = 4
mateWeight = 8
qubsradius = 5
startpixvel = 2  # pix per lifecycle/frame
population = []
trackinglist = []
for i in range(62*62):
    trackinglist.append([])

pygame.init()

win = pygame.display.set_mode(size)
clock = pygame.time.Clock()

def clamp(n, minimum, maximum):
    return max(minimum, min(n, maximum))
def getabsdistance(x1, y1, x2, y2):
    return math.fabs(math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2)))
def returnsorroundingboxes(l, position):
    return [l[clamp(position, 0, 3843)], l[clamp(position + 1, 0, 3843)], l[clamp(position - 1, 0, 3843)], l[clamp(position + 62, 0, 3843)],
            l[clamp(position - 62, 0, 3843)], l[clamp(position + 61, 0, 3843)], l[clamp(position -61, 0, 3843)],
            l[clamp(position + 63, 0, 3843)], l[clamp(position - 63, 0, 3843)]]

class emotion(object):
    def __init__(self, value):
        self.value = value
    def eq(self, eqval):
        self.value = clamp(self.value, 0, 100)
    def pluseq(self, eqval):
        self.value = clamp(self.value + eqval, 0, 100)
    def minuseq(self, eqval):
        self.value = clamp(self.value - eqval, 0, 100)
    def multiply(self, multval):
        self.value = clamp(self.value * multval, 0, 100)
    def divide(self, divval):
        self.value = clamp(self.value / divval, 0, 100)

class qub(object):
    def __init__(self, x, y, direction):
        self.pos = np.array([x, y])
        self.vel = np.array([math.cos(direction), math.sin(direction)])
        self.happy = emotion(75.0)
        self.sad = emotion(10.0)
        self.apathy = emotion(0.0)
        self.matetimes = 0
        self.eattimes = 0
        self.lifecycles = 0
        self.oldpos = self.pos
        self.trackinglistpos = math.trunc(self.pos[0]/150) + (6*math.trunc(self.pos[1]/150)) - 1
    def mate(self):
        self.happy.pluseq(mateWeight * math.pow(self.matetimes + 1, 1/2))
        self.matetimes += 1
        self.apathy.minuseq(7)
    def eat(self):
        self.happy.pluseq(hungerWeight * math.pow(self.eattimes + 1, 3/4))
        self.eattimes += 1
        self.apathy.minuseq(2)
    def live(self):
        self.lifecycles += 1
        self.apathy.pluseq(1)
        self.happy.minuseq(math.pow(self.apathy.value, 1.5))
        self.sad.pluseq(((100 - self.happy.value)/4) + (-self.matetimes/self.lifecycles) + np.random.randint(0, 15))
        if (self.pos[0] <= 24 or self.pos[0] >= 624) and (self.pos[1] <= 24 or self.pos[1] >= 624):
            self.vel = [[-1, 0], [0, -1]] @ self.vel
        elif self.pos[1] <= 24 or self.pos[1] >= 624:
            self.vel = [[1, 0], [0, -1]] @ self.vel
        elif self.pos[0] <= 24 or self.pos[0] >= 624:
            self.vel = [[-1, 0], [0, 1]] @ self.vel
        for section in returnsorroundingboxes(trackinglist, self.trackinglistpos):
            for i in section:
                if getabsdistance(self.pos[0], self.pos[1], i.pos[0], i.pos[1]) <= qubsradius*2 and i != self:
                    self.vel = (np.inner(self.vel - i.vel, self.pos - i.pos)) / (np.inner(i.pos - self.pos, i.pos - self.pos)) * (self.pos - i.pos)
                    self.vel = np.array([math.cos(math.atan2(self.vel[1], self.vel[0])), math.sin(math.atan2(self.vel[1], self.vel[0]))])
                    break
        self.pos += self.vel * startpixvel


    def gethappy(self):
        return self.happy.value
    def getsad(self):
        return self.sad.value
    def getapathy(self):
        return self.apathy.value

ptslist = []
def generatequbs(num):
    listqubs = []
    while len(listqubs) < clamp(num, 1, 144):
        x = 49.0 + (50 * (len(listqubs) % ((size[0]-50)/50)))
        y = 49.0 + (50 * math.trunc(len(listqubs)/((size[0]-50)/50)))
        listqubs.append(qub(x, y, np.deg2rad(np.random.randint(0, 361))))
    ptslist.append((int(listqubs[0].pos[0]), int(listqubs[0].pos[1])))
    return listqubs


def displayqubs(qubslist):
    win.fill((0,0,0))
    for i in qubslist:
        pygame.draw.circle(win, (84, 0, 228), (int(i.pos[0]), int(i.pos[1])), qubsradius)
        gfxdraw.aacircle(win, int(i.pos[0]), int(i.pos[1]), qubsradius, (84, 0, 228))
        if i == qubslist[0]:
            ptslist.append((int(i.pos[0]), int(i.pos[1])))
            pygame.draw.aalines(win, (0, 150, 150), False, ptslist, True)

    pygame.display.update()

def livequbs(qubslist):
    global trackinglist
    for i in qubslist:
        i.trackinglistpos = 63 + math.trunc((i.pos[0]-25)/10) + (62*math.trunc((i.pos[1]-25)/10))
        trackinglist[i.trackinglistpos].append(i)
    for i in qubslist:
        i.live()
    print(trackinglist[14])
    trackinglist.clear()
    for i in range(62*62):
        trackinglist.append([])


population = generatequbs(((size[0] - 50) / 50) * (size[1] - 50) / 50)

run = True
while run:
    livequbs(population)
    displayqubs(population)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            run = False
    clock.tick(10)
    print(str(population[0].pos))
print("COLLISION DOESN'T WORK YET")
