from enum import Enum


class Unit(Enum):
    MM = "mm"
    INCH = "inch"
    DEGREE = "deg"
    MICROMETER = "um"


class FeatureType(Enum):
    CIRCLE = "CIRCLE"
    CYLINDER = "CYLINDER"
    PLANE = "PLANE"
    LINE = "LINE"
    POINT = "POINT"
    CONE = "CONE"
    SPHERE = "SPHERE"