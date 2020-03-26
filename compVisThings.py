import pygame
import numpy as np
import math
from pygame import gfxdraw

size = width, height = 650, 650

normalizes = True
randomizes = True
hungerWeight = 4
mateWeight = 8
qubsradius = 5
startpixvel = 2  # pix per lifecycle/frame
population = []
trackinglist = []
for i in range(62*62):
    trackinglist.append([])
    
def clamp(n, minimum, maximum):
    return max(minimum, min(n, maximum))

def randomize_velo(v):
    scale_fac = clamp(1 + np.random.normal(0, .2) / np.linalg.norm(v), .6, 1.4) if np.linalg.norm(v) != 0 else 1
    v = v * scale_fac 

class collision_states:
    class free:
        def __init__(self, m_ball):
            self.ball = m_ball
            
        def get_state(self):
            return 'free'
        
    class unhandled_collided:
        def __init__(self, m_ball, m_other):
            self.ball = m_ball
            self.other = m_other
            
        def get_state(self):
            return 'unhandled collided'
        
        def get_other(self):
            return self.other
    
    class recovering:
        def __init__(self, m_ball, m_other):
            self.ball = m_ball
            self.other = m_other
             
        def get_state(self):
            return 'recovering'
        
        def get_other(self):
            return self.other
    
def collide(qub_one, qub_two):
    diff = qub_two.pos - qub_one.pos
    dist = np.linalg.norm(diff)
    col_vec = (1/dist) * diff
    one_proj = np.dot(qub_one.vel, col_vec)
    two_proj = np.dot(qub_two.vel, col_vec)
    qub_one.vel += (two_proj - one_proj) * col_vec
    qub_two.vel += (one_proj - two_proj) * col_vec        
    if normalizes:
        one_spd = np.linalg.norm(qub_one.vel)
        two_spd = np.linalg.norm(qub_two.vel)
        qub_one.vel = (1/one_spd) * qub_one.vel if one_spd != 0 else qub_one.vel
        qub_two.vel = (1/two_spd) * qub_two.vel if two_spd != 0 else qub_two.vel
    if randomizes:
        randomize_velo(qub_one.vel)
        randomize_velo(qub_two.vel)

pygame.init()

win = pygame.display.set_mode(size)
clock = pygame.time.Clock()

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
        self.collision_state = collision_states.free(self)
        self.last_collision_state = collision_states.free(self)
    def get_dist(self, other):
        return np.linalg.norm(self.pos - other.pos)
    def update_collision_state(self):
        self.last_collision_state = self.collision_state
        min_col_dist = math.inf
        min_dist_qub = None
        for section in returnsorroundingboxes(trackinglist, self.trackinglistpos):
            for i in section:
                if i != self and self.get_dist(i) < min_col_dist:
                    min_col_dist = self.get_dist(i)
                    min_dist_qub = i
        #If you're free your state is now free no matter what you were last time
        if min_dist_qub is None:
            self.collision_state = collision_states.free(self)
        else:
            if self.last_collision_state.get_state() == 'free':
                if min_col_dist > 2 * qubsradius:
                    self.collision_state = self.last_collision_state
                else:
                    self.collision_state = collision_states.unhandled_collided(self, min_dist_qub)
            elif self.last_collision_state.get_state() == 'unhandled collided':
                #We don't handle this here. We don't move the balls until the collider collides them.
                self.collision_state = self.last_collision_state
            elif self.last_collision_state.get_state() == 'recovering':
                recov_with = self.last_collision_state.get_other()
                if min_col_dist > 2 * qubsradius:
                    self.collision_state = collision_states.free(self)
                else:
                    if min_dist_qub == recov_with:
                        self.collision_state = self.last_collision_state
                    else:
                        self.collision_state = collision_states.unhandled_collided(self, min_dist_qub)
            else:
                raise Exception('Invalid Collision State')
        if normalizes:
            spd = np.linalg.norm(self.vel)
            self.vel = (1 / spd) * self.vel if spd != 0 else self.vel
        return self.collision_state.get_state() != 'unhandled collided'   
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
        shouldrand = True
        if (self.pos[0] <= 24 or self.pos[0] >= 624) and (self.pos[1] <= 24 or self.pos[1] >= 624):
            self.vel = [[-1, 0], [0, -1]] @ self.vel
        elif self.pos[1] <= 24 or self.pos[1] >= 624:
            self.vel = [[1, 0], [0, -1]] @ self.vel
        elif self.pos[0] <= 24 or self.pos[0] >= 624:
            self.vel = [[-1, 0], [0, 1]] @ self.vel
        else:
            shouldrand = False
        if shouldrand and randomizes:
            randomize_velo(self.vel)
        if self.update_collision_state():
            self.pos += self.vel * startpixvel
    def gethappy(self):
        return self.happy.values
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
    for i in qubslist:
        if i.collision_state.get_state() == 'unhandled collided':
            j = i.collision_state.get_other()
            collide(i, j)
            i.last_collision_state = i.collision_state
            i.collision_state = collision_states.recovering(i, j)
            j.last_collision_state = j.collision_state
            j.collision_state = collision_states.recovering(j, i)
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
    clock.tick(40)
    print(str(population[0].pos))