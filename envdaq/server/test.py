import abc


class Parent(abc.ABC):

    def __init__(self):

        self.__x = 0
        self.__y = 0

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x):
        self.__x = x

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, y):
        self.__y = y

    @abc.abstractmethod
    def increment(self):

        self.x += 1


class Child(Parent):

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def increment(self):
        super().increment()
        self.y += 1

class GrandChild(Child):

    def __init__(self):
        super().__init__()
        pass

    def increment(self):
        self.x += 1
        super().increment()
#        self.y ++ 2

#p = Child()
p = GrandChild()

print('Before: x = {}, y = {}'.format(p.x, p.y))
p.increment()
print('After: x = {}, y = {}'.format(p.x, p.y))
