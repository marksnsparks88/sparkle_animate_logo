import cairo
import numpy as np
import math
import random
import os

class Vec():
    def __init__(self, posx, posy):
        self.pos = np.array((posx, posy))
        self.x = self.pos[0]
        self.y = self.pos[1]
    
    def update_xy(self):
        self.x = self.pos[0]
        self.y = self.pos[1]
    
    def dist(self, vecb):
        a = abs(self.pos[0] - vecb.pos[0])
        b = abs(self.pos[1] - vecb.pos[1])
        return math.sqrt(math.pow(a, 2)+math.pow(b, 2))
    
    def norm(self, ip=False):
        h = math.sqrt(math.pow(self.pos[0], 2) + math.pow(self.pos[1], 2))
        x = self.pos[0]/h if h != 0 else 0
        y = self.pos[1]/h if h != 0 else 0
        
        if ip == True:
            self.pos[0] = x
            self.pos[1] = y
            self.update_xy()
        else:
            return Vec(x, y)
    
    def sub(self, vecb, ip=False):
        if ip == True:
            self.pos = self.pos - vecb.pos
            self.update_xy()
        else:
            pos = self.pos - vecb.pos
            return Vec(pos[0], pos[1])
    
    def translate(self, vecb, step, ip=False):
        def orient(pos):
            o = [0, 0]
            for p in range(len(pos)):
                if pos[p] > 0:
                    o[p] = 1
                else:
                    o[p] = -1
            return o
                
        if list(self.pos) == list(vecb.pos):
            return Vec(self.pos[0], self.pos[1])
        
        vectmp = Vec(vecb.pos[0] - self.pos[0],
                   vecb.pos[1] - self.pos[1])
        norma = vectmp.norm()
        
        cpos = self.pos + (norma.pos * step)
        vecc = Vec(cpos[0], cpos[1])
        
        vectmp = Vec(vecb.pos[0] - vecc.pos[0],
                     vecb.pos[1] - vecc.pos[1])
        normb = vectmp.norm()
        
        if orient(norma.pos) != orient(normb.pos):
            vecc.pos = vecb.pos
            vecc.update_xy()
            
        if ip == True:
            self.pos = vecc.pos
            self.update_xy()
        else:
            return vecc
    
class Node():
    def __init__(self, pos, mask, spd, deplete, min_energy, rad0, rad1, grads):
        self.pos = pos
        self.mask = mask
        self.speed = spd
        self.deplete = deplete
        self.min_energy = min_energy
        
        self.rad0 = rad0
        self.rad1 = rad1
        self.grads = grads
        
        self.incoming = []
        self.outgoing = []
        self.sparks = []
        self.end = []
        self.spark = False
        self.energy = 0
    
    def GetConnections(self, nodes, max_con):
        min_ = 0
        xnodes = []
        for n in range(len(nodes)):
            for o in range(len(nodes[n].outgoing)):
                if nodes[n].outgoing[o].pos == self.pos:
                    self.incoming.append(nodes[n])
                    
        for n in range(len(nodes)):
            if nodes[n] not in self.incoming:
                xnodes.append(nodes[n])
        
        for i in range(max_con):
            max_ = 99999
            ndx = 0
            for n in range(len(xnodes)):
                dist = self.pos.dist(xnodes[n].pos)
                if dist < max_ and dist > min_:
                    max_ = dist
                    ndx = n
            min_ = max_
            self.outgoing.append(xnodes[ndx])
            self.sparks.append(Vec(self.pos.x, self.pos.y))
            self.end.append(0)
    
    def update(self, ctx):
        if self.energy <= self.min_energy:
            self.energy = 0
            self.spark = False
        elif self.spark == True:
            for s in range(len(self.sparks)):
                if list(self.sparks[s].pos) != list(self.outgoing[s].pos.pos) and self.end[s] == 0:
                    col = self.mask[int(self.sparks[s].y-1)][int(self.sparks[s].x-1)]
                    self.DrawSpark(ctx,
                                   self.sparks[s],
                                   col)
                    self.sparks[s].translate(self.outgoing[s].pos, self.speed, ip=True)
                else:
                    self.outgoing[s].energy = self.energy - self.deplete
                    self.outgoing[s].spark = True
                    self.sparks[s] = Vec(self.pos.x, self.pos.y)
                    self.end[s] = 1
                    
            for i in self.end:
                if i == 1:
                    self.spark = False
                else:
                    self.spark = True
                    
        if self.spark == False:
            self.end = [0 for i in range(len(self.sparks))]
    
    def DrawSpark(self, ctx, pos, col):
        t_rad1 = self.energy * self.rad1
        r = col[1]/255
        g = col[2]/255
        b = col[3]/255
        if list(col) != [255, 0, 0, 0]:
            ctx.arc(pos.x, pos.y, t_rad1, 0, 2*math.pi)
            grad = cairo.RadialGradient(pos.x, pos.y, t_rad1,
                                        pos.x, pos.y, self.rad0)
            for gr in self.grads:
                grad.add_color_stop_rgba(gr[0], r, g, b, gr[1])
            ctx.set_source(grad)
            ctx.fill()


class Draw():
    def __init__(self, mask, imgs, retry, spacing, connections, energy, min_energy, speed, deplete_rate, sprk_rad_in, sprk_rad_out, sprk_grads, debug = 0):
        self.maskimg = mask
        self.imgs = imgs
        self.retry = retry
        self.spacing = spacing
        self.connex = connections
        self.energy = energy
        self.min_energy = min_energy
        self.spd = speed
        self.deplete = deplete_rate
        self.rad0 = sprk_rad_in
        self.rad1 = sprk_rad_out
        self.sprk_grads = sprk_grads
        
        self.mask = cairo.ImageSurface.create_from_png(self.maskimg)
        self.width = self.mask.get_width()
        self.height = self.mask.get_height()
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        self.ctx = cairo.Context(self.surface)
        
        if debug == 1:
            self.cdata = self.load_image()
            self.nodes = self.load_nodes()
            self.refresh(img=True)
            self.DebugNodes()
        elif debug == 2:
            self.refresh()
            c = [255, 255, 255, 0]
            s = 100
            q = 10
            self.DebugSpark(c, s, q)
        else:
            self.cdata = self.load_image()
            self.nodes = self.load_nodes()
            
            self.start = self.nodes[random.randint(0, len(self.nodes)-1)]
            self.start.energy = self.energy
            self.start.spark = True
            
    
    def refresh(self, img=False):
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.fill()
        if img == True:
            sur = cairo.ImageSurface.create_from_png(self.maskimg)
            imgpat = cairo.SurfacePattern(sur)
            self.ctx.set_source(imgpat)
            self.ctx.paint_with_alpha(0.5)
    
    def load_image(self):
        print("loading image...")
        buff = self.mask.get_data()
        data = np.ndarray(shape=(self.height, self.width), dtype=np.uint32, buffer=buff)
        cdata = np.ndarray(shape=(self.height, self.width, 4))
        for h in range(len(data)):
            for w in range(len(data[h])):
                argb = []
                hex_ = hex(data[h][w])
                for i in range(int(len(hex_)/2)):
                    hx = hex_[i*2+2:i*2+4]
                    if len(hx) != 0:
                        argb.append(int("0x"+hex_[i*2+2:i*2+4], 0))
                cdata[h][w] = argb
        print("done")
        return cdata
    
    def load_nodes(self):
        nodes = []
        print("setting up nodes...")
        nBlk = True
        spced = True
        while self.retry > 0:
            pos = Vec(random.randint(0, self.width-1), random.randint(0, self.height-1))
            if (list(self.cdata[pos.y][pos.x]) == [255.0, 0.0, 0.0, 0.0]):
                nBlk = False
            else:
                nBlk = True
                 
            dist = 99999
            for i in nodes:
                ndist = pos.dist(i.pos)
                if ndist < dist:
                    dist = ndist
            if (dist < self.spacing):
                spced = False
            else:
                spced = True
            
            if len(nodes) == 0 and nBlk == True:
                nodes.append(Node(pos, 
                                       self.cdata, 
                                       self.spd, 
                                       self.deplete, 
                                       self.min_energy, 
                                       self.rad0, 
                                       self.rad1,
                                       self.sprk_grads))
            elif nBlk == True and spced == True:
                nodes.append(Node(pos, 
                                       self.cdata, 
                                       self.spd, 
                                       self.deplete,
                                       self.min_energy, 
                                       self.rad0, 
                                       self.rad1,
                                       self.sprk_grads))
            else:                
                self.retry -= 1
                msgstr = "nodes: {}".format(len(nodes))
                print(" "*len(msgstr), end="\r")
                print(msgstr, end="\r")
                if self.retry < 0:
                    break
            
        for n in range(len(nodes)):
            nodes[n].GetConnections(nodes, self.connex)
        print("nodes:", len(nodes))
        
        return nodes
    
    def run(self):
        c=0
        while os.path.isdir(self.imgs+str(c)) == True:
            c+=1
        self.imgs = self.imgs+str(c)
        
        if os.path.isdir(self.imgs) == False:
            os.makedirs(self.imgs)
            
        frame=0
        active = 1
        while active > 0:
            self.refresh()
            active = 0
            for n in self.nodes:
                n.update(self.ctx)
                if n.spark == True:
                    active = active + 1
                    
            msgstr = "frame: {}, active: {},".format(frame, active)
            print(" "*len(msgstr), end="\r")
            print(msgstr, end="\r")
            self.surface.write_to_png("{}/{:0>3}.png".format(self.imgs, frame))
            frame += 1
        print()
    
    def DebugNodes(self):
        for n in self.nodes:
            for o in n.outgoing:
                self.ctx.move_to(n.pos.x, n.pos.y)
                self.ctx.line_to(o.pos.x, o.pos.y)
                self.ctx.set_source_rgba(0, 1, 0, 1)
                self.ctx.set_line_width(1)
                self.ctx.set_dash([5.0])
                self.ctx.stroke()
                
            self.ctx.arc(n.pos.x, n.pos.y, 5, 0, 2*math.pi)
            self.ctx.set_source_rgba(0, 1, 0, 1)
            self.ctx.fill_preserve()
            self.ctx.set_source_rgba(0, 1, 0, 1)
            self.ctx.set_line_width(0.5)
            self.ctx.stroke()
        
        self.surface.write_to_png("debug_nodes.png")
    
    def DebugSpark(self, col, spread, quant):
        t_rad1 = energy * self.rad1
        r = col[1]/255
        g = col[2]/255
        b = col[3]/255
        for i in range(quant):
            x = random.randint(-spread, spread)
            y = random.randint(-spread, spread)
            if list(col) != [255, 0, 0, 0]:
                self.ctx.arc(int(self.width/2)+x, int(self.height/2)+y, t_rad1, 0, 2*math.pi)
                grad = cairo.RadialGradient(int(self.width/2)+x, int(self.height/2)+y, t_rad1,
                                            int(self.width/2)+x, int(self.height/2)+y, self.rad0)
                for gr in self.sprk_grads:
                    grad.add_color_stop_rgba(gr[0], r, g, b, gr[1])
                
                self.ctx.set_source(grad)
                self.ctx.fill()
            
        self.surface.write_to_png("debug_spark.png")
        
            
if __name__ == '__main__':
    mask            = "python_1920x1080.png"
    imgs            = "intro"
    retry           = 15000
    spacing         = 25
    connections     = 5
    energy          = 3
    min_energy      = 1
    speed           = 5
    deplete_rate    = 0.02
    sprk_rad_in     = 1
    sprk_rad_out    = 60
                    #(pos, alpha)
    sprk_grads     = ((1, 1),
                      (0.97, 0.5),
                      (0.90, 0.15),
                      (0.83, 0.01),
                      (0, 0))
    debug = 0
    
    app = Draw(mask,
               imgs,
               retry,
               spacing,
               connections,
               energy,
               min_energy,
               speed,
               deplete_rate,
               sprk_rad_in,
               sprk_rad_out,
               sprk_grads,
               debug)
    
    if debug == 0:
        app.run()
