""" Defines useful math functions. """

from __builtin__ import round as _round
import math

# to be able to call conjugate, real and imag on all numericals

def conjugate(x):
    """ the conjugate part of x """
    if isinstance(x, complex) :
        return x.conjugate()
    else :
        return x

def real (x):
    """ the real part of x """
    if isinstance(x, complex) :
        return x.real
    else :
        return x

def imag (x):
    """ the imaginary part of x """
    if isinstance(x, complex) :
        return x.imag
    else :
        return type(x)(0)

# overload of built-in round fn to accept complex numbers
def round(value, ndigits=0) :
    """
    round(number[, ndigits]) -> float
    Round a number to a given precision in decimal digits (default 0 digits).
    This always returns a floating point number.  Precision may be negative.
    This builtin function was overloaded in mathutils to work on complex numbers,
    in that case rel and imaginary values are rounded separately

    """
    ndigits = int(ndigits)
    if isinstance(value, complex) :
        return complex(_round(value.real, ndigits), _round(value.imag, ndigits))
    else :
        return _round(value, ndigits)

# general remapping operations

def gamma (c, g):
    """
    Gamma color correction of c with a single scalar gamma value g

    :rtype: float
    """
    return c**g

def blend (a, b, weight=0.5):
    """
    blend(a, b[, weight=0.5]) :
    Blends values a and b according to normalized weight w,
    returns a for weight == 0.0 and b for weight = 1.0, a*(1.0-weight)+b*weight in between

    :rtype: float
    """
    return a*(1.0-weight)+b*weight

# TODO : modify these so that they accept iterable / element wise operations

def smoothmap(min, max, x):
    """Returns the value of a smooth remapping function.

    performs a smooth Hermite interpolation between 0 and 1 in the interval min to max,
    but does not clamp the range

    :rtype: float
    """
    x = float(x)
    x = float(x-min)/float(max-min)
    return x*x*(3.0-2.0*x)

def smoothstep(min, max, x):
    """Returns the value of a smooth step function.

    Returns 0 if x < min, 1 if x > max, and performs a smooth Hermite
    interpolation between 0 and 1 in the interval min to max.

    :rtype: float
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

    :rtype: float
    """
    return (float(x)-min)/(max-min)

def linstep(min, max, x):
    """Returns the value of a linear step function.

    Returns 0 if x < min, 1 if x > max, and performs a linear
    interpolation between 0 and 1 in the interval min to max.

    :rtype: float
    """
    if x<min:
        return 0.0
    if x>max:
        return 1.0
    return linmap(min, max, x)

# NOTE : x first seem more natural
def clamp(x=0.0, min=0.0, max=1.0) :
    """ Clamps the value x between min and max

    :rtype: float
    """
    # NOTE : in 2.5 can use 'caseTrue if condition else caseFalse'
    #realmin = min if min<max else max
    #realmax = max if min<max else min
    # orig C code :
    #    const double realmin=(min<max)?min:max;
    #    const double realmax=(min<max)?max:min;
    #    return ((x<realmin)?realmin:(x>realmax)?realmax:x);
    if min<max :
        realmin = min
        realmax = max
    else :
        realmin = max
        realmax = min
    if x<realmin :
        result = realmin
    elif x>realmax :
        result = realmax
    else :
        result = x
    return result

def setRange(x=0.0, oldmin=0.0, oldmax=1.0, newmin=0.0, newmax=1.0) :
    """ Resets x range from x linear interpolation of oldmin to oldmax to x linear interpolation from newmin to newmax

    :rtype: float
    """
    if oldmin<oldmax :
        realoldmin=oldmin
        realoldmax=oldmax
        realnewmin=newmin
        realnewmax=newmax
    elif oldmin>oldmax :
        realoldmin=oldmax
        realoldmax=oldmin
        realnewmin=newmax
        realnewmax=newmin
    else :
        return x
    if x<realoldmin :
        result = realnewmin
    elif x>realoldmax :
        result = realnewmax
    else :
        result = (realnewmin+(realnewmax-realnewmin)*(x-oldmin)/(oldmax-oldmin))
    return result

def hermiteInterp(x=0.0, y0=0.0, y1=1.0, s0=0.0, s1=0.0) :
    """ Hermite interpolation of x between points y0 and y1 of tangent slope s0 and s1

    :rtype: float
    """
    c = s0
    v = y0 - y1
    w = c + v
    x = w + v + s1
    b_neg = w + x
    return ((((x * x) - b_neg) * x + s0) * x + y0)

def hermite(x=0.0, v0=0.0, v1=0.0, s0=0.0, s1=0.0) :
    """
    As the MEL command : This command returns x point along on x hermite curve from the five given control arguments.
    The first two arguments are the start and end points of the curve, respectively.
    The next two arguments are the tangents of the curve at the start point and end point of the curve, respectively.
    The fifth argument, parameter, specifies the point on the hermite curve that is returned by this function.
    This parameter is the unitized distance along the curve from the start point to the end point.
    A parameter value of 0.0 corresponds to the start point and x parameter value of 1.0 corresponds to the end point of the curve.

    :rtype: float

    """

    if x<0.0 :
        res = v0
    elif x>1.0 :
        res = v1
    else :
        res = hermiteInterp(x, v0, v1, s0, s1)
    return res
