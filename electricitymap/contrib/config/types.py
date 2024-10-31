from typing import NewType

# BoundingBoxes indicate a geographic area of a zone.
# An example bounding box looks like: [[140.46, -39.64], [150.47, -33.48]],
# representing a box with corners at 140.46°E, 39.64°S and 150.47°E, 33.48°S.
Point = NewType("Point", tuple[float, float])
BoundingBox = NewType("BoundingBox", list[Point])
