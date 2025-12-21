

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def toString(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return self.toString()

    def toTouple(self):
        return self.x, self.y

    def __add__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def copy(self):
        return Cell(self.x, self.y)

    def __eq__(self, other):
        return self.x==other.x and self.y==other.y

    def eq(self, x, y):
        return self.x == x and self.y == y

    def __iter__(self):
        return (self.x, self.y).__iter__()

    def distManhattan(self, other):
        return abs(self.x-other.x)+abs(self.y-other.y)

    def distSquared(self, other):
        return (self.x-other.x)**2+(self.y-other.y)**2

    def lengthSquared(self):
        return self.x**2+self.y**2

    def dirto(self, other):
        if  abs(other.x-self.x) > abs(other.y-self.y):
            return Cell(min(max(other.x-self.x, -1), 1), 0)
        else:
            return Cell(0, min(max(other.y - self.y, -1), 1))

    def isdir(self):
        return abs(self.x)+abs(self.y)==1


    def converttodir(self):
        self.x = min(max(self.x, -1), 1)
        self.y = min(max(self.y, -1), 1)

    def neighbors(self):
        return tuple(self.copy()+Cell.numtodir(d) for d in range(4))

    @staticmethod
    def dirtonum(dir):
        if dir.x == -1: return 0
        if dir.y == -1: return 1
        if dir.x == 1: return 2
        if dir.y == 1: return 3
        return 4

    @staticmethod
    def dirtostr(dir):
        return str(Cell.dirtonum(dir))

    @staticmethod
    def numtodir(num):
        return [Cell(-1, 0), Cell(0, -1), Cell(1, 0), Cell(0, 1)][num]

    @staticmethod
    def dirtokeycode(dir):
        return ["left", "up", "right", "down"][Cell.dirtonum(dir)]

    @staticmethod
    def reversedir(dir):
        return Cell.numtodir((Cell.dirtonum(dir)+2)%4)

    @staticmethod
    def leftturn(dir):
        return Cell.numtodir((Cell.dirtonum(dir) + 3) % 4)

    @staticmethod
    def rightturn(dir):
        return Cell.numtodir((Cell.dirtonum(dir) + 1) % 4)
