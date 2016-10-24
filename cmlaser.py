#!/bin/env python3

# Backtracking based solver for Crazy Machines 3 laser puzzles (e.g.campaign  67 (Laser beams and pyramid))
# Solves 67 in 2.5 minutes on an i7-2640m / 1.2 min on an i7-6700

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

	def __init__(self, pos, rot):
		self.pos = pos
		self.rot = rot
		self.pf = None

	def onAdd(self, playfield):
		self.pf = playfield

	def onRemove(self):
		self.playfield = None
	
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
	def __init__(self, pos=None, rot=0):
		super().__init__(pos, rot)
		self.transparent = False
		self.beamsIn = []
		self.beamsOut = []

	def onAdd(self, playfield):
		super().onAdd(playfield)

	def onRemove(self):
		super().onRemove()
		for beam in self.beamsOut:
			self.pf.removeBeam(beam)
		self.beamsOut.clear()
		for beam in self.beamsIn:
			beam.unblock(self)
		self.beamsIn.clear()

	def isTransparent(self):
		return self.transparent

	# laser beam hit object
	def hit(self, beam):
		if beam in self.beamsIn:
			raise Exception("Same beam hit multiple times")
			return
		self.beamsIn.append(beam)

	# Laser beam stops hitting object
	def unhit(self, beam):
		if beam in self.beamsIn:
			self.beamsIn.remove(beam)

class Target(LaserPart):
	def __init__(self, pos=None, rot=0):
		super().__init__(pos, rot)
		self.active = False

	def hit(self, beam):
		super().hit(beam);
		if not self.doesActivate(beam):
			return
		self.active = True

	def unhit(self, beam):
		super().unhit(beam);
		if not self.doesActivate(beam):
			return
		self.active = False

	def doesActivate(self, beam):
		return (2 - self.rot) % 4 == beam.getDir()

	def isActive(self):
		return self.active

	def __str__(self):
		return "U" if self.isActive() else "X"

class Frame(LaserPart):
	def __init__(self, pos=None):
		super().__init__(pos, 0)
		self.transparent = True

	def __str__(self):
		return 'O'

class Laser(LaserPart):
	def onAdd(self, playfield):
		super().onAdd(playfield)
		beam = LaserBeam(self, CMObject.dirToVec(self.rot), self.rot)
		self.beamsOut.append(beam)
		self.pf.addBeam(beam)

	def __str__(self):
		return '>'

class Mirror(LaserPart):
	def __init__(self, pos=None, rot=0):
		super().__init__(pos, rot)
		self.excitationMap = {}

	def hit(self, beam):
		super().hit(beam)
		dirout = self.doesExcite(beam)
		if dirout == -1:
			return
		beamout = LaserBeam(self, CMObject.dirToVec(dirout), dirout)
		self.beamsOut.append(beamout)
		self.excitationMap[beam] = beamout
		self.pf.addBeam(beamout)

	def unhit(self, beam):
		super().unhit(beam);
		if self.doesExcite(beam) == -1:
			return
		if not beam in self.excitationMap:
			return
		beamout = self.excitationMap.pop(beam)
		if not beamout in self.beamsOut:
			return
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
	def __init__(self, pos=None, rot=0):
		super().__init__(pos, rot)
		self.exciter = None

	def hit(self, beam):
		super().hit(beam)
		dirsout = self.doesExcite(beam)
		if not dirsout:
			return
		self.exciter = beam
		for dirout in dirsout:
			beamout = LaserBeam(self, CMObject.dirToVec(dirout), dirout)
			self.beamsOut.append(beamout)
			self.pf.addBeam(beamout)

	def unhit(self, beam):
		super().unhit(beam)
		if self.doesExcite(beam) == -1:
			return
		if beam != self.exciter:
			return
		for beamout in self.beamsOut:
			self.pf.removeBeam(beamout)
		self.beamsOut.clear()

	def doesExcite(self, beam):
		if (2 - self.rot) % 4 == beam.getDir():
			return [(self.rot - 1) % 4, (self.rot + 1) % 4]
		return None

	def __str__(self):
		return str(self.rot) #'T'

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
		part.onAdd(self)
		pos = part.getPos()
		i = pos.y * self.width + pos.x
		self.objects[i] = part
		if not part.isTransparent():
			for beam in self.beams[i]:
				beam.block(part)

	def removePart(self, part):
		pos = part.getPos()
		i = pos.y * self.width + pos.x
		if self.objects[i] != part:
			raise Exception("Can't remove nonexistent part")
		self.objects[i] = None
		part.onRemove()

	def getPartAtXY(self, x, y):
		return self.objects[y * self.width + x]

	def getPartAt(self, pos):
		return self.getPartAtXY(pos.x, pos.y)

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
laser = Laser(Pos2D(0, 1), 0)
pf.placePart(laser)
mirror = Mirror(Pos2D(4, 0), 0)
pf.placePart(mirror)
mirror = Mirror(Pos2D(8, 0), 3)
pf.placePart(mirror)
mirror = Mirror(Pos2D(12, 0), 0)
pf.placePart(mirror)
frame = Frame(Pos2D(16, 0))
pf.placePart(frame)
mirror = Mirror(Pos2D(17, 0), 3)
pf.placePart(mirror)
frame = Frame(Pos2D(21, 0))
pf.placePart(frame)

targets = []

target = Target(Pos2D(4, 5), 1)
pf.placePart(target)
targets.append(target)
target = Target(Pos2D(8, 5), 1)
pf.placePart(target)
targets.append(target)
target = Target(Pos2D(12, 5), 1)
pf.placePart(target)
targets.append(target)
target = Target(Pos2D(17, 5), 1)
pf.placePart(target)
targets.append(target)
target = Target(Pos2D(21, 5), 1)
pf.placePart(target)
targets.append(target)

# Calculate all valid locations
validlocs = []
for y in range(0, pf.height):
	for x in range(0, pf.width):
		if pf.getPartAtXY(x, y):
			continue
		if y != 0 and not pf.getPartAtXY(x, y - 1):
			continue
		validlocs.append(Pos2D(x, y))

placeables = [Frame(), Mirror(), Mirror(rot=3), Mirror(rot=3), Splitter(), Splitter(rot=2), Splitter(rot=1), Splitter(rot=1)]

def backtrack(validlocs, placeables):
	if(len(placeables) == 0):
		success = True
		for target in targets:
			if not target.isActive():
				success = False
# Uncomment to see intermediate steps
#			else:
#				print(str(pf))
		return success
	for pos in validlocs:
		# Place parts only in laser beams
		if not len(pf.getBeamsAt(pos)):
			continue
		for part in placeables:
			part.setPos(pos)
			pf.placePart(part)
			newlocs = list(validlocs)
			newlocs.remove(pos)
			# Calculate new valid placement location above $part
			newloc = pos + Vec2D(0, 1)
			if pf.isInside(newloc) and not pf.getPartAt(newloc):
				newlocs.append(newloc)
			newparts = list(placeables)
			newparts.remove(part)
			if backtrack(newlocs, newparts):
				return True
			pf.removePart(part)
	return False

print("Solving...")

if backtrack(validlocs, placeables):
	print("Solution:")
	print(str(pf))
else:
	print("No solution")
