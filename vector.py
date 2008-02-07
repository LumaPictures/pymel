
"""
List based vector and matrix classes that support elementwise mathematical operations
"""

# based on a python vector class by A. Pletzer 5 Jan 00/11 April 2002



import math
from math import *
import node, core



class Vector(list):
	"""
		A list based vector class
	"""
	# no c'tor
	def __init__(self, elements=[0,0,0]):
		list.__init__(self, elements)
	
	def __repr__(self):
		return 'Vector(%s)' % list.__repr__(self)	
	def __getslice__(self, i, j):
		try:
			# use the list __getslice__ method and convert
			# result to Vector
			return Vector(super(Vector, self).__getslice__(i,j))
		except:
			raise TypeError, 'Vector::FAILURE in __getslice__'
		
	def __add__(self, other):
		try:
			return Vector(map(lambda x,y: x+y, self, other))
		except:
			return Vector(map( lambda x: x+other, self))
		
	def __neg__(self):
		return Vector(map(lambda x: -x, self))
	
	def __sub__(self, other):
		try:
			return Vector(map(lambda x,y: x-y, self, other))
		except:
			return Vector(map( lambda x: x-other, self))

	def __mul__(self, other):
		"""
		Element by element multiplication
		"""		
		#print "vec mul ", self, other, type(other)
		#if isinstance(other, Matrix):
		#if hasattr(other,'__class__') and other.__class__ is Matrix:		
		#if type(other) == Matrix:
		
		if isinstance(other, list):
			#print "LEN OTHER", len(other)
			if isinstance( other[0], list ):
				#return Matrix( map( lambda x: [x], self ) ) * other
				dif = other.ncols()-self.size()
				#print "VEC x MAT"
				res = Matrix( [list(self) + [1]*dif ]) * other 
				return res[0][0:self.size()]
			else:
				#print "VEC x VEC"
				return Vector(map(lambda x,y: x*y, self,other))

		#print "VEC x CONST"
		# other is a const
		return Vector(map(lambda x: x*other, self))


	def __rmul__(self, other):
		#print "vec rmul", self, other					
		return (self*other)

		
	def __div__(self, other):
		"""
		Element by element division.
		"""
		try:
			return Vector(map(lambda x,y: x/y, self, other))
		except:
			return Vector(map(lambda x: x/other, self))

	def __rdiv__(self, other):
		"""
		The same as __div__
		"""
		try:
			return Vector(map(lambda x,y: x/y, other, self))
		except:
			# other is a const
			return Vector(map(lambda x: other/x, self))

	def size(self): return len(self)



	def worldToObject(self, obj):
		return self * node.DependNode(obj).worldInverseMatrix.get()
	
	def worldToCamera(self, camera=None):
		if camera is None:
			camera = core.mel.getCurrentCamera()
		return self * node.DependNode(camera).worldInverseMatrix.get()
		
	def worldToScreen(self, camera=None):
		if camera is None:
			camera = node.Camera(core.mel.getCurrentCamera())
		else:
			camera = node.Camera(camera)
			
		screen = self.worldToCamera(camera)
		
		screen.x = (screen.x/-screen.z) / tan(radians(camera.horizontalFieldOfView/2))/2.0+.5
		screen.y = (screen.y/-screen.z) / tan(radians(camera.verticalFieldOfView/2))/2.0+.5 

		xres = core.getAttr( 'defaultResolution.width' )
		yres = core.getAttr( 'defaultResolution.height' )
		filmApX = camera.horizontalFilmAperture.get()
		filmApY = camera.verticalFilmAperture.get()
	
		filmAspect = filmApX/filmApY;
		resAspect  = xres/yres;
		ratio = filmAspect/resAspect;
	
		screen.y = linmap( ((ratio-1)/-2), (1+(ratio-1)/2), screen.y )
		
		return screen	
	
	def objectToWorld(self, object):
		worldMatrix = node.DependNode(object).worldMatrix.get()
		return self * worldMatrix
	
	def objectToCamera(self, object, camera=None):
		return self.objectToWorld(object).worldToCamera( camera )
		
	def objectToScreen(self, object, camera=None):
		return self.objectToWorld(object).worldToScreen( camera )

			
	def cameraToWorld(self, camera=None):
		if camera is None:
			camera = core.mel.getCurrentCamera()
		return self * node.DependNode(camera).worldMatrix.get()




	def conjugate(self):
		return Vector(map(lambda x: x.conjugate(), self))

	def ReIm(self):
		"""
		Return the real and imaginary parts
		"""
		return [
			Vector(map(lambda x: x.real, self)),
			Vector(map(lambda x: x.imag, self)),
			]

	def AbsArg(self):
		"""
		Return modulus and phase parts
		"""
		return [
			Vector(map(lambda x: abs(x), self)),
			Vector(map(lambda x: atan2(x.imag,x.real), self)),
			]

	def setToZeros(self):
		self[:] = [0]*self.size() 

	def setToOnes(self):
		self[:] = [1]*self.size() 

	def setToRandom(self, lmin=0.0, lmax=1.0):
		import whrandom
		new = Vector([])
		gen = whrandom.whrandom()
		self[:] = map( lambda x: (lmax-lmin)*gen.random() + lmin, range(self.size()) )
		
	def norm(self):
		"""
		Computes the norm of Vector a.
		"""
		return sqrt(abs(dot(self,self)))

	def mag(self):
		return self.norm()
	
	def normalize(self):
		self /= self.mag()

	def sum(self):
		"""
		Returns the sum of the elements of a.
		"""
		return reduce(lambda x, y: x+y, self, 0)
	
					
	x = property( lambda self: self.__getitem__(0) ,  lambda self, val: self.__setitem__(0,val) )
	y = property( lambda self: self.__getitem__(1) ,  lambda self, val: self.__setitem__(1,val) )
	z = property( lambda self: self.__getitem__(2) ,  lambda self, val: self.__setitem__(2,val) )


class Matrix(list):
	"""
		A list based Vector class
	"""
	def __init__(self, rowColList = [[0]*4]*4 ):
		for i in range( 0, len(rowColList )):
			rowColList[i] = Vector( rowColList[i] )
		
		list.__init__(self, rowColList)
	
	def __str__(self):
		res = ''
		for i in range(0,len(self)):
			 res += ', '.join( map( lambda x: "%.03f" % x, self[i]) ) + '\n'
		return res
		
	def __add__(self, other):
		try:
			return Matrix(map(lambda x,y: x+y, self, other))
		except:
			return Matrix(map( lambda x: x+other, self))
		
	def __neg__(self):
		return Matrix(map(lambda x: -x, self))
	
	def __sub__(self, other):
		try:
			return Matrix(map(lambda x,y: x-y, self, other))
		except:
			return Matrix(map( lambda x: x-other, self))


	def __mul__(self, other):
		"""
		Element by element multiplication
		"""
		temp = other.transpose()
		return Matrix( [ [ dot(row,col) for col in temp ] for row in self ] )

	def __rmul__(self, other):
		return (self*other)
		
	def __div__(self, other):
		"""
		Element by element division.
		"""
		try:
			return Vector(map(lambda x,y: x/y, self, other))
		except:
			return Vector(map(lambda x: x/other, self))

	def __rdiv__(self, other):
		"""
		The same as __div__
		"""
		try:
			return Vector(map(lambda x,y: x/y, other, self))
		except:
			# other is a const
			return Vector(map(lambda x: other/x, self))
	
	def row(self, row):
		return self[row]
		
	def col(self, col):
		import operator
		return Vector(map(operator.itemgetter(col),self))
	
	def nrows(self):
		len(self)
	
	def ncols(self):
		return len(self.transpose())
	
	def transpose(self):
		return Matrix( apply( map, [None]+self ) )
		
	

	def toList(self):
		return reduce( lambda x,y: list(x)+list(y), self ) 

###############################################################################
	
def dot(a, b):
	"""
	dot product of two MVecs.
	"""
	try:
		return reduce(lambda x, y: x+y, a*b, 0.)
	except:
		raise TypeError, 'Vector::FAILURE in dot'



# elementwise operations
	
def log10(a):
	log10.__doc__
	try:
		return a.__class__(map(math.log10, a))
	except:
		return math.log10(a)

def log(a):
	log.__doc__
	try:
		return a.__class__(map(math.log, a))
	except:
		return math.log(a)
		
def exp(a):
	exp.__doc__
	try:
		return a.__class__(map(math.exp, a))
	except:
		return math.exp(a)

def sin(a):
	sin.__doc__
	try:
		return a.__class__(map(math.sin, a))
	except:
		return math.sin(a)
		
def tan(a):
	tan.__doc__
	try:
		return a.__class__(map(math.tan, a))
	except:
		return math.tan(a)
		
def cos(a):
	cos.__doc__
	try:
		return a.__class__(map(math.cos, a))
	except:
		return math.cos(a)

def asin(a):
	asin.__doc__
	try:
		return a.__class__(map(math.asin, a))
	except:
		return math.asin(a)

def atan(a):
	atan.__doc__
	try:
		return a.__class__(map(math.atan, a))
	except:
		return math.atan(a)

def acos(a):
	acos.__doc__
	try:
		return a.__class__(map(math.acos, a))
	except:
		return math.acos(a)

def sqrt(a):
	sqrt.__doc__
	try:
		return a.__class__(map(math.sqrt, a))
	except:
		return math.sqrt(a)

def sinh(a):
	sinh.__doc__
	try:
		return a.__class__(map(math.sinh, a))
	except:
		return math.sinh(a)

def tanh(a):
	tanh.__doc__
	try:
		return a.__class__(map(math.tanh, a))
	except:
		return math.tanh(a)

def cosh(a):
	cosh.__doc__
	try:
		return a.__class__(map(math.cosh, a))
	except:
		return math.cosh(a)


def pow(a,b):
	"""
	Takes the elements of a and raises them to the b-th power
	"""
	try:
		return a.__class__(map(lambda x: x**b, a))
	except:
		try:
			return a.__class__(map(lambda x,y: x**y, a, b))
		except:
			return math.pow(a,b)
	
def atan2(a,b):	   
	"""
	Arc tangent
	
	"""
	try:
		return a.__class__(map(atan2, a, b))
	except:
		return math.atan2(a,b)
	

# general remapping operations

def smoothmap(min, max, x):
	"""Returns the value of a smooth remapping function.

	performs a smooth Hermite interpolation between 0 and 1 in the interval min to max,
	but does not clamp the range
	"""
	x = float(x)
	x = (-min)/(max-min)
	return x*x*(3.0-2.0*x)
	
def smoothstep(min, max, x):
	"""Returns the value of a smooth step function.

	Returns 0 if x < min, 1 if x > max, and performs a smooth Hermite
	interpolation between 0 and 1 in the interval min to max.
	"""
	if x<min:
		return 0.0
	if x>max:
		return 1.0
	return smoothmap(min, max, x)

def linmap(min, max, x):
	"""Returns the value of a linear remapping function.

	performs a linear interpolation between 0 and 1 in the interval min to max,
	but does not clamp the range
	"""
	return (float(x)-min)/(max-min)
	
def linstep(min, max, x):
	"""Returns the value of a linear step function.

	Returns 0 if x < min, 1 if x > max, and performs a linear
	interpolation between 0 and 1 in the interval min to max.
	"""
	if x<min:
		return 0.0
	if x>max:
		return 1.0
	return linmap(min, max, x)
	
	