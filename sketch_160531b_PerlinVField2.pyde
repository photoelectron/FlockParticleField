from Saver import saves

noiseSpace = 1080 / 20.
xoff = 0  # offsets for noise space (no need to divide by noiseSpace)
yoff = 0  # x+ = look right ; y- = look down
noiseTime = 0 / 100.
alp = 1  # alpha for particles
fade = True
fadeamt = 0.05  # min 0.004
freedom = 1.1  # particle freedom; values around 1.1 work for loose particles

nparticles = 143
F1 = 1
F2 = 1
MF = 10
N_PHI = 900
N_save = 100
autosave = True
multisave = False

def setup():
    global saver, p, img
    size(1080 / 4, 1080 / 4)
    # nparticles = int(floor(width*height/43.))
    colorMode(HSB, 1.0)
    noiseSeed(44357)
    noiseDetail(4)
    background(0)
    saver = saves(N_PHI, N_save)
    # particles, life, life mode (random,order,none), order, color, mode (perlin, diff, img)
    p = PSyst(nparticles, N_PHI, 'random', True, False, 'perlin')
    # drawField()
    # img = imgnse(loadImage("src/sm01.png"))
    # img.display()

def draw():
    global F1,F2,p
    # F1 += sin(TWO_PI*frameCount/900)
    # F2 = map(cos(TWO_PI*frameCount/(N_PHI)),-1,1,.5,5)
    if fade:
        blendMode(SUBTRACT)
        noStroke()
        fill(fadeamt)
        rect(0, 0, width, height)
        blendMode(BLEND)
    # background(0)
    if autosave:
        if frameCount == int(floor(1.1*N_PHI)):
            saver.onClick()
        if frameCount >= 3*N_PHI:
            noLoop()
    ### update with death(true/false)
    p.update(False)
    saver.save_frame()

#######################################
#######################################

def drawField():
    loadPixels()
    for i in xrange(width):
        for j in xrange(height):
            idx = i + j * width
            # h = map(idx,0,width*height,0,1)
            # s = noise(i/noiseSpace,frameCount*noiseTime)
            # b = noise(j/noiseSpace,frameCount*noiseTime)
            c = noise(
                (i + xoff) / noiseSpace, (j + yoff) / noiseSpace, frameCount * noiseTime)
            pixels[idx] = color(c * .5)
    updatePixels()
#######################################
#######################################

class Particle():

    def __init__(self, x, y, c, life):
        self.pos = PVector(x, y)
        self.orig = self.pos.copy()
        self.vel = PVector(0, 0)
        self.acc = PVector(0, 0)
        self.c = c
        self.oc = c
        self.life = life
        self.time = self.life
        self.died = False
        self.maxSpeed = 1
        self.maxForce = .05

    def flow(self, desired):
        desired.limit(self.maxSpeed)
        steer = PVector.sub(desired, self.vel)
        steer.limit(self.maxForce)
        steer.mult(1)
        self.addForce(steer)
    
    def flock(self, psyst):
        # Separation variables
        separate = 20/2
        sepForce = PVector(0,0)
        sepCount = 0
        # Cohesion variables
        cohesion = 40/2
        cohTarget = PVector(0,0)
        cohForce = PVector(0,0)
        cohCount = 0
        # Alignment variables
        aligndist = 40/2
        aliSum = PVector(0,0)
        aliForce = PVector(0,0)
        aliCount = 0
        
        for i in xrange(len(psyst)):
            # Separation
            d = PVector.dist(self.pos, psyst[i].pos)
            if 0 < d <= separate:
                diff = PVector.sub(self.pos,psyst[i].pos)
                diff.normalize()
                diff.div(d)
                sepForce.add(diff)
                sepCount += 1
            # Cohesion
            if 0 < d <= cohesion:
                cohTarget.add(psyst[i].pos)
                cohCount += 1
            # Alignment
            if 0 < d <= aligndist:
                aliSum.add(psyst[i].vel)
                aliCount += 1
        
        # Separation
        if sepCount > 0:
            sepForce.div(sepCount)
            sepForce.normalize()
            sepForce.mult(self.maxSpeed)
            sepForce.sub(self.vel)
            sepForce.limit(self.maxForce)
        # Cohesion
        if cohCount > 0:
            cohTarget.div(cohCount)
            cohForce = self.seek(cohTarget)
        # Alignment
        if aliCount > 0:
            aliSum.div(aliCount)
            aliSum.normalize()
            aliSum.mult(self.maxSpeed)
            aliForce = PVector.sub(aliSum, self.vel)
            aliForce.limit(self.maxForce)            
        
        ###### FLOCK ######
        ### MULTIPLIERS ###
        sepForce.mult(2)
        cohForce.mult(1)
        aliForce.mult(0)
        self.addForce(sepForce)
        self.addForce(cohForce)
        self.addForce(aliForce)
    
    def seek(self, target):
        desired = PVector.sub(target, self.pos)
        desired.normalize()
        desired.mult(self.maxSpeed)
        steer = PVector.sub(desired, self.vel)
        steer.limit(self.maxForce)
        return steer
    
    def addForce(self, F):
        self.acc.add(F)

    def setVel(self, F):
        self.vel = F.copy()
    
    def update(self):
        self.vel.add(self.acc)
        self.vel.limit(self.maxSpeed)
        self.pos.add(self.vel)
        self.acc.mult(0)
        self.age()

    def age(self):
        self.life -= 1
        if self.life <= 0:
            self.reset(False)
            self.died = True

    def reset(self, rpos, rtime=True):
        self.vel = PVector(0, 0)
        self.c = self.oc
        if rtime:
            self.life = self.time
        if rpos:
            self.pos = PVector(random(width), random(height))
        else:
            self.pos = self.orig.copy()

    def show(self):
        stroke(self.c)
        point(floor(self.pos.x), floor(self.pos.y))

########################################
########################################

class PSyst():

    def __init__(self, n, life, lifemode, order, col, mode):
        ### Variables for controlling diff eq grid space ################
        # diffRangex: total value across all pixels
        # zero for diffOffx = -width/2
        self.diffRangex = 2
        self.diffRangey = 2
        self.diffSpacex = (width / self.diffRangex)
        self.diffSpacey = (height / self.diffRangey)
        self.diffOffx = -width * (.5 - 0)
        self.diffOffy = -height * (.5 - 0)
        ### Multiply/add factor for diffeq color
        self.colf = [-1, 0.3]
        # --------------------------------------------
        self.F = PVector(0,0)
        self.mode = mode
        self.col = col
        self.particles = []
        self.empty = False
        wh = width * height
        L = [1. * life * i / wh for i in xrange(0, wh, wh / n)]
        for i in xrange(0, wh, wh / n):
            if order:
                x = i % width
                y = i / width
            else:
                x = int(floor(random(width)))
                y = int(floor(random(height)))
            if col and (mode == 'diff'):
                self.anx, self.any = diffeq2((x + self.diffOffx) / self.diffSpacex,
                                             (y + self.diffOffy) / self.diffSpacey)
                self.F = PVector(self.anx,self.any)
                h = map(self.F.mag(),0,PI,0,1)
                h = self.F.mag()*self.colf[0] + self.colf[1]
                c = color(h, 1, 1, alp)
            elif col:
                h = 1. * i / wh
                c = color(h, 1, 1, alp)
            else:
                c = color(1, alp)
            P = Particle(x, y, c, life)
            if lifemode == 'random':
                # For randomized life spans
                r = int(floor(random(len(L))))
                P.life -= L[r]
                L.pop(r)
            elif lifemode == 'order':
                # For ordered life spans
                P.life -= int(round(1. * life * i / wh))

            self.particles.append(P)

    def update(self,death):
        
        ### For changing field
        # self.diffRangex = F2
        # self.diffRangey = F2
        # self.diffSpacex = (width / self.diffRangex)
        # self.diffSpacey = (height / self.diffRangey)
        ###
        
        for i in xrange(len(self.particles)-1,-1,-1):
            self.CV(i)
            # self.particles[i].addForce(self.F)
            # self.particles[i].setVel(self.F)
            self.particles[i].flow(self.F)
            self.particles[i].flock(self.particles)
            self.particles[i].update()
            if death:
                if self.particles[i].died:
                    self.particles.pop(i)
                else:
                    self.oobshow(i)
            else:
                self.oobshow(i)
        if len(self.particles) == 0:
            if not(self.empty):
                print "No particles", frameCount
            self.empty = True
    
    def oobshow(self,k):
        self.oob(k)
        ### ooba: random position, reset life
        # self.oob2(k, False, False)
        self.CV(k)
        self.particles[k].show()
    
    #####################
    ############## VECTOR
    #####################
    def getVector(self,i):
        """ Get Vel/Acc vector for current particle """
        if self.mode == 'perlin':
            self.an = noise((self.particles[i].pos.x + xoff) / noiseSpace,
                            (self.particles[i].pos.y + yoff) / noiseSpace,
                            frameCount * noiseTime)
            self.ar = map(self.an, 0, 1, -PI, PI)
            self.F = PVector.fromAngle(self.ar)
            # self.F.setMag(self.an)
        elif self.mode == 'diff':
            self.anx, self.any = diffeq2((self.particles[i].pos.x + self.diffOffx) / self.diffSpacex,
                                         (self.particles[i].pos.y + self.diffOffy) / self.diffSpacey)
            # self.F = PVector.fromAngle(self.anx)
            # self.F.mult(self.any)
            self.F = PVector(self.anx, self.any)
            Fm = map(self.F.mag(),0,PI/2**.5,.5,1)
            self.Fc = map(self.F.mag(),0,PI/2**.5,0,1)
            self.F.setMag(Fm)
        elif self.mode == 'img':
            self.ah, self.ass, self.ab = img.getHSB(self.particles[i].pos.x, 
                                                    self.particles[i].pos.y)
            ar = map((self.ah * .3 + self.ab * .3 + self.ass * 2.4), 
                    0, 3, -TWO_PI, TWO_PI)
            self.F = PVector(self.ah, self.ab)
            self.F.rotate(ar)

    #####################
    ############### COLOR
    #####################
    def getColor(self,k):
        """ Get color for current particle """
        if self.mode == 'perlin':
            if self.col:
                h = map(self.an, 0, 1, -.0025, .0025)
                nh = hue(self.particles[k].c) + h
                if not(0 <= nh <= 1):
                    nh -= abs(nh) / nh
                self.particles[k].c = color(nh, 1, 1, alp)
            else:
                # nb = brightness(self.particles[k].c) + self.an
                # if not(0 <= nb <= 1):
                #     nb -= abs(nb) / nb
                # nb = self.an
                self.particles[k].c = color(1, alp)
        elif self.mode == 'diff':
            if self.col:
                # h = cos(self.anx)*sin(self.any)/10
                # nh = hyp(self.anx,self.any,self.colf)
                nh = self.Fc*self.colf[0] + self.colf[1]
                if not(0 <= nh <= 1):
                    nh -= abs(nh) / nh
                self.particles[k].c = color(nh, 1, 1, alp)
            else:
                b = map(self.any + self.anx, -PI, PI, -.01, .01)
                nb = brightness(self.particles[k].c) + b
                alpf = sin(.5 * PI * self.particles[k].life / self.particles[k].time)
                if not(0 <= nb <= 1):
                    nb -= abs(nb) / nb
                self.particles[k].c = color(1, alp)
        elif self.mode == 'img':
            if self.col:
                h = self.ah + (hue(self.particles[k].c) - self.ah) / 2
                if not(0 <= h <= 1):
                    h -= abs(h) / h
                self.particles[k].c = color(h, self.ass, 1 - self.ab, alp)
            else:
                hsb = (self.ah * .5 + (1 - self.ass * 1) + self.b * 1.5) / 3
                self.particles[k].c = color(hsb, alp)

    def CV(self,k):
        self.getVector(k)
        self.getColor(k)

    #####################
    ################# OOB
    #####################
    def oob(self, k):
        """ Continuous edges """
        if not(0 <= self.particles[k].pos.x < width):
            self.particles[k].pos.x -= (width * abs(self.particles[k].pos.x) /
                                        self.particles[k].pos.x)
        if not(0 <= self.particles[k].pos.y < height):
            self.particles[k].pos.y -= (height * abs(self.particles[k].pos.y) /
                                        self.particles[k].pos.y)

    def oob2(self, k, rnd, rlife=True):
        """ Resets to original/random position, life after OOB """
        if (not(0 <= self.particles[k].pos.x < width) or
                not(0 <= self.particles[k].pos.y < height)):
            self.particles[k].reset(rnd,rlife)

    def direction(self, p, cn):
        x = p.pos.x
        y = p.pos.y
        v = p.vel.copy()
        w = PVector(0, 0)
        for i in xrange(-1, 2):
            for j in xrange(-1, 2):
                xi = x + i
                yj = y + j
                if x == xi and y == yj:
                    continue
                if not(0 <= xi < width):
                    xi -= width * abs(xi) / xi
                if not(0 <= yj < height):
                    yj -= height * abs(yj) / yj
                # noiseold
                # n = noise((xi + xoff)/noiseSpace,
                #           (yj + yoff)/noiseSpace,
                #           frameCount*noiseTime)
                h, n, s = img.getHSB(xi, yj)
                if n < cn:
                    w = PVector(i, j)
                    w.setMag(cn - n ** freedom)
                    cn = n
        # w.lerp(v,.5)
        a = PVector.angleBetween(v, w)
        a = map(a, 0, TWO_PI, -TWO_PI, TWO_PI)
        w.rotate(a / 4)
        return w

#####################
#####################

def diffeq(x, y):
    f1 = 5
    f2 = 5
    yy = x * (y - 1) ** 2
    angle = atan(yy)
    return angle

def diffeq2(x, y):
    ### Use F1,F2 in global variables /\
    # f1 = 1
    # f2 = 6
    ### Spiral in middle
    xx = -y + x * (x ** 2 + y ** 2) * sin(PI / (x ** 2 + y ** 2) ** .5)
    yy = x + y * (x ** 2 + y ** 2) * sin(PI / (x ** 2 + y ** 2) ** .5)
    ### 2 spirals
    # xx = y**2 - 1
    # yy = x**2 - 1
    ### Chladnis?
    # xx = sin(F1*x)*cos(F2*y)
    # yy = cos(F2*x)*sin(F1*y)
    ### ???
    # xx = cos(x*y)*sin(y*y)
    # yy = cos(x*x)*sin(y*x)
    angley = atan(yy)
    anglex = atan(xx)
    return anglex, angley
    
#####################
#####################

class imgnse():

    def __init__(self, img):
        self.img = img
        self.w = img.width
        self.h = img.height

    def display(self):
        image(self.img, 0, 0)

    def getHSB(self, x, y):
        x = int(floor(x))
        y = int(floor(y))
        h = hue(self.img.pixels[x + y * self.w])
        b = brightness(self.img.pixels[x + y * self.w])
        s = saturation(self.img.pixels[x + y * self.w])
        return h, s, b

    def getRGB(self, x, y):
        x = int(floor(x))
        y = int(floor(y))
        r = red(self.img.pixels[x + y * self.w])
        g = green(self.img.pixels[x + y * self.w])
        b = blue(self.img.pixels[x + y * self.w])
        return r, g, b

#####################
#####################

def mouseClicked():
    saver.onClick()
