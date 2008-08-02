def Enum(*names):
   ##assert names, "Empty enums are not supported" # <- Don't like empty enums? Uncomment!

    class EnumClass(object):
        __slots__ = names
        def __iter__(self):        return iter(constants)
        def __len__(self):         return len(constants)
        def __getitem__(self, i):  return constants[i]
        def __repr__(self):        return 'Enum' + str(names)
        def __str__(self):         return 'enum ' + str(constants)

    class EnumValue(int):
        #def __init__(self, value, name): self.name = name
        EnumType = property(lambda self: EnumType)
        name = property( lambda self: names[self] )
        #def __str__(self): return 'enum value ( %s=%s )' % (self.name, self)
        
    maximum = len(names) - 1
    constants = [None] * len(names)
    for i, each in enumerate(names):
        val = EnumValue(i)
        #setattr(val, 'name', each)
        setattr(EnumClass, each, val)
        constants[i] = each
    constants = tuple(constants)
    EnumType = EnumClass()
    return EnumType


if __name__ == '__main__':
   print '\n*** Enum Demo ***'
   print '--- Days of week ---'
   Days = Enum('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
   print Days
   print Days.Mo
   print Days.Fr
   print Days.Mo < Days.Fr
   print list(Days)
   for each in Days:
      print 'Day:', each
   print '--- Yes/No ---'
   Confirmation = Enum('No', 'Yes')
   answer = Confirmation.No
   print 'Your answer is not', ~answer