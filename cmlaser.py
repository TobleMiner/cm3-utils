#!/bin/env python3

from math import sqrt, pow

class Thingy2D():
	def __init__(self, x=0, y=0):
		self.x = int(x)
		self.y = int(y)
	
	def clone(self):
		return self.__class__(self.x, self.y)

	def div(self, scalar):
		return self.__class__(self.x / scalar, self.y / scalar)

	def __add__(self, other):
		return self.__class__(self.x + other.x, self.y + other.y)

	def __iadd__(self, other):
		self.x += other.x
		self.y += other.y

	def __sub__(self, other):
		return self.__class__(self.x - other.x, self.y - other.y)

	def __isub__(self, other):
		self.x -= other.x
		self.y -= other.y

	def __str__(self):
		return "[{0},{1}]".format(self.x, self.y)

class Pos2D(Thingy2D):
	pass

class Vec2D(Thingy2D):
	def normalize(self):
		return self.div(self.len())

	def len(self):
		return sqrt(pow(self.x, 2) + pow(self.y, 2))

class CMObject():
	ROT_0 = 0
	ROT_90 = 1
	ROT_180 = 2
	ROT_270 = 3

	def dirToVec(dir):
		if dir == CMObject.ROT_0:
			return Vec2D(1, 0)
		if dir == CMObject.ROT_90:
			return Vec2D(0, 1)
		if dir == CMObject.ROT_180:
			return Vec2D(-1, 0)
		if dir == CMObject.ROT_270:
			return Vec2D(0, -1)
		raise Exception("Invalid direction")

	def __init__(self, playfield, pos, rot):
		self.pf = playfield
		self.pos = pos
		self.rot = rot

	def getPlayfield(self):
		return self.pf

	def getPos(self):
		return self.pos

	def setPos(self, pos):
		self.pos = pos

	def setPosXY(self, x, y):
		self.pos = Pos2D(x, y)
	
	def setRotation(self, rot):
		self.rot = rot

class LaserPart(CMObject):
	def __init__(self, playfield, pos, rot):
		super().__init__(playfield, pos, rot)
		self.transparent = False
		self.beamsIn = []
		self.beamsOut = []

	def onAdd(self):
		pass

	def onRemove(self):
		for beam in self.beamsOut:
			self.pf.removeBeam(beam)
		for beam in self.beamsIn:
			beam.unblock(self)

	def isTransparent(self):
		return self.transparent

	def hit(self, beam):
		pass

	def unhit(self, beam):
		pass

class Target(LaserPart):


	def __str__(self):
		return "X"

class Frame(LaserPart):
	def __init__(self, playfield, pos, rot):
		super().__init__(playfield, pos, rot)
		self.transparent = True

	def __str__(self):
		return 'O'

class Laser(LaserPart):
	def onAdd(self):
		beam = LaserBeam(self, CMObject.dirToVec(self.rot), self.rot)
		self.beamsOut.append(beam)
		self.pf.addBeam(beam)

	def __str__(self):
		return '>'

class Mirror(LaserPart):
	def __init__(self, playfield, pos, rot):
		super().__init__(playfield, pos, rot)
		self.excitationMap = {}

	def hit(self, beam):
		dirout = self.doesExcite(beam)
		if dirout == -1:
			return
		if beam in self.beamsIn:
			raise Exception("Same beam hit multiple times")
			return
		self.beamsIn.append(beam)
		beamout = LaserBeam(self, CMObject.dirToVec(dirout), dirout)
		self.beamsOut.append(beamout)
		self.excitationMap[beam] = beamout
		self.pf.addBeam(beamout)

	def unhit(self, beam):
		if self.doesExcite(beam) == -1:
			return
		if not beam in self.beamsIn:
			return
		self.beamsIn.remove(beam)
		beamout = self.excitationMap.pop(beam)
		self.beamsOut.remove(beamout)
		self.pf.removeBeam(beamout)

	def doesExcite(self, beam):
		if (3 - self.rot) % 4 == beam.getDir():
			return (beam.getDir() + 1) % 4
		if (2 - self.rot) % 4 == beam.getDir():
			return (beam.getDir() - 1) % 4
		return -1

	def __str__(self):
		return '/' if self.rot % 2 else '\\'

class Splitter(LaserPart):
	def hit(self, beam):
		dirsout = self.doesExcite(beam)
		if not dirsout:
			return
		if beam in self.beamsIn:
			raise Exception("Same beam hit multiple times")
			return
		self.beamsIn.append(beam)
		for dirout in dirsout:
			beamout = LaserBeam(self, CMObject.dirToVec(dirout), dirout)
			self.beamsOut.append(beamout)
			self.pf.addBeam(beamout)

	def unhit(self, beam):
		if self.doesExcite(beam) == -1:
			return
		if not beam in self.beamsIn:
			return
		self.beamsIn.remove(beam)
		for beamout in self.beamsOut:
			self.pf.removeBeam(beamout)
		self.beamsOut.clear()

	def doesExcite(self, beam):
		if (2 - self.rot) % 4 == beam.getDir():
			return [(self.rot - 1) % 4, (self.rot + 1) % 4]
		return None

	def __str__(self):
		return 'T'

class LaserBeam():
	# src = Source laser part
	def __init__(self, src, vec, dir):
		self.src = src
		self.vec = vec.normalize()
		self.dir = dir
		self.dest = None
		self.beamparts = []

	def onAdd(self):
		self.updateDest()
	
	def raytrace(self, pos=None):
		if not pos:
			pos = self.src.getPos() + self.vec
		pf = self.src.getPlayfield()
		while pf.isInside(pos):
			obj = pf.getObjAt(pos)
			if obj and not obj.isTransparent():
				return obj
			self.beamparts.append(pos)
			pf.addBeamPart(self, pos)
			pos = pos + self.vec
		return False

	def updateDest(self, pos=None):
		if self.dest:
			self.dest.unhit(self)
		self.dest = self.raytrace(pos)
		if self.dest:
			self.dest.hit(self)

	# Something has been placed in the beam
	def block(self, part):
		for pos in self.beamparts:
			self.src.getPlayfield().removeBeamPart(self, pos)
		self.beamparts.clear();
		self.updateDest()

	def unblock(self, part):
		self.updateDest(part.getPos())

	def getDir(self):
		return self.dir 

	def onRemove(self):
		self.destroy()

	def destroy(self):
		for pos in self.beamparts:
			self.src.getPlayfield().removeBeamPart(self, pos)
		self.beamparts.clear();
		if self.dest:
			self.dest.unhit(self)

	def __str__(self):
		return '|' if self.dir % 2 else '-'

class Playfield():
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.beams = [[] for i in range(0, width * height)]
		self.objects = [False for i in range(0, width * height)]
		
	def placePart(self, part):
		pos = part.getPos()
		i = pos.y * self.width + pos.x
		self.objects[i] = part
		for beam in self.beams[i]:
			beam.block(part)
		part.onAdd()

	def removePart(self, part):
		pos = part.getPos()
		i = pos.y * self.width + pos.x
		self.objects[i] = None
		part.onRemove()

	def getBeamsAtXY(self, x, y):
		return self.beams[y * self.width + x]

	def getBeamsAt(self, pos):
		return self.getBeamsAtXY(pos.x, pos.y)

	def addBeamPart(self, beam, pos):
		self.beams[pos.y * self.width + pos.x].append(beam)

	def removeBeamPart(self, beam, pos):
		self.beams[pos.y * self.width + pos.x].remove(beam)

	def addBeam(self, beam):
		beam.onAdd()

	def removeBeam(self, beam):
		beam.onRemove()

	def getObjAtXY(self, x, y):
		return self.objects[y * self.width + x]

	def getObjAt(self, pos):
		return self.getObjAtXY(pos.x, pos.y)

	def isInside(self, pos):
		return pos.x >= 0 and pos.y >= 0 and pos.x < self.width and pos.y < self.height

	def __str__(self):
		s = "=" * self.width + "\n"
		for y in reversed(range(0, self.height)):
			for x in range(0, self.width):
				chr = ' '
				chrs = list(map(lambda lzr: str(lzr), self.getBeamsAtXY(x, y)))
				if len(chrs):
					if '|' in chrs and '-' in chrs:
						chr = '+'
					else:
						chr = chrs[0]
				obj = self.getObjAtXY(x, y)
				if obj:
					chr = str(obj)
				s += chr
			s += "\n"
		s += "=" * self.width + "\n"
		return s


pf = Playfield(23, 6)
laser = Laser(pf, Pos2D(0, 2), 0)
pf.placePart(laser)
mirror = Mirror(pf, Pos2D(4, 0), 0)
pf.placePart(mirror)
mirror = Mirror(pf, Pos2D(8, 0), 3)
pf.placePart(mirror)
mirror = Mirror(pf, Pos2D(12, 0), 0)
pf.placePart(mirror)
frame = Frame(pf, Pos2D(16, 0), 2)
pf.placePart(frame)
mirror = Mirror(pf, Pos2D(17, 0), 3)
pf.placePart(mirror)
frame = Frame(pf, Pos2D(21, 0), 2)
pf.placePart(frame)

target = Target(pf, Pos2D(4, 5), 2)
pf.placePart(target)
target = Target(pf, Pos2D(8, 5), 2)
pf.placePart(target)
target = Target(pf, Pos2D(12, 5), 2)
pf.placePart(target)
target = Target(pf, Pos2D(17, 5), 2)
pf.placePart(target)
target = Target(pf, Pos2D(21, 5), 2)
pf.placePart(target)

splitter1 = Splitter(pf, Pos2D(4, 2), 2)
pf.placePart(splitter1)

splitter2 = Splitter(pf, Pos2D(8, 2), 1)
pf.placePart(splitter2)

splitter3 = Splitter(pf, Pos2D(17, 2), 2)
pf.placePart(splitter3)
print(str(pf))

pf.removePart(laser)
print(str(pf))
