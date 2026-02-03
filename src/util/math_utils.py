"""
Math utility functions for animations and interpolation.
"""

from typing import Union

Number = Union[int, float]


def lerp(a: Number, b: Number, t: float) -> float:
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * t


def clamp(value: Number, min_val: Number, max_val: Number) -> Number:
    """Clamp value between min_val and max_val."""
    return max(min_val, min(max_val, value))


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out function."""
    return 1 - (1 - t) * (1 - t)


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out function."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


def ease_out_elastic(t: float) -> float:
    """Elastic ease-out for bouncy effects."""
    if t == 0 or t == 1:
        return t
    import math
    c4 = (2 * math.pi) / 3
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def ease_out_back(t: float) -> float:
    """Back ease-out for overshoot effect."""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def distance_squared(x1: Number, y1: Number, x2: Number, y2: Number) -> float:
    """Calculate squared distance between two points."""
    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy


def normalize_angle(angle: float) -> float:
    """Normalize angle to [0, 360) range."""
    import math
    angle = angle % (2 * math.pi)
    if angle < 0:
        angle += 2 * math.pi
    return angle
