import math


class Location:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance(self, location: "Location") -> float:
        return math.sqrt((location.y - self.y) * (location.y - self.y) + (location.x - self.x) * (location.x - self.x))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))
