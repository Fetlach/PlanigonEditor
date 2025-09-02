from typing import Self
from math import tan, pi, sqrt, cos, sin
import numpy as np
from shapely.geometry import Point, Polygon
from dataclasses import dataclass
from typing import Optional
import math

# side length functions
def r(n): 
    return 1.0 / (2.0 * tan(pi / n))

def planigon_sides_from_vertex_config(face_seq):
    # face_seq: list of ints, e.g. [3,3,3,4,4]
    n = len(face_seq)
    return [ r(face_seq[i]) + r(face_seq[(i+1) % n]) for i in range(n) ]

class planigonNodeAttach:
    ID : any
    idx : int

class node:
    ID : any
    x: float
    y: float
    isPinned : bool
    angleAttachments : list[planigonNodeAttach] #list of planigon node attachments
    availableAngle : float

class planigon: 
    # angles are in clockwise order
    angles: list[float]
    # lengths are in clockwise order describing vert to next clockwise vert
    # (edge length between angle[i] and angle[i+1])
    lengths: list[float]

    def __init__(self, angles: list[float], lengths = [], lengthParms = []):
        self.angles = angles
        if len(lengths) <= 0:
            self.lengths = planigon_sides_from_vertex_config(lengthParms)
        else:
            self.lengths = lengths

## --- Planigon layouts --- ##
# List of planigon names
# Undividable tris: V3.7.42   V3.8.24   V3.9.18   V4.5.20   V3.10.15   V5.5.10
# tris: V3.12.12   V4.6.12   V6.6.6   V4.8.8
# quads: V3.3.4.12   V3.4.3.12   V3.3.6.6   V3.6.3.6   V3.4.4.6   V3.4.6.4   V4.4.4.4
# pents: V3.3.3.3.6   V3.3.4.3.4   V3.3.3.4.4
# hexes: V3.3.3.3.3.3

# - 6 sides - #
# internal angle = 720
# V3.3.3.3.3.3
planigon6_1 = planigon([120, 120, 120, 120, 120, 120], [1, 1, 1, 1, 1, 1]) # hexagon

# - 5 sides - #
# internal angle = 540
# V3.3.3.4.4
planigon5_1 = planigon([120, 120, 120, 90, 90], [1/sqrt(3), 1/sqrt(3), 1/2 + 1/(2*sqrt(3)), 1, 1/2 + 1/(2*sqrt(3))]) 
# V3.3.3.3.6
planigon5_2 = planigon([120, 120, 120, 120, 60], [1/sqrt(3), 1/sqrt(3), 1/sqrt(3), 2/sqrt(3), 2/sqrt(3)]) 
# V3.3.4.3.4
planigon5_3 = planigon([120, 120, 90, 120, 90], [1/sqrt(3), 1/2 + 1/(2*sqrt(3)), 1/2 + 1/(2*sqrt(3)), 1/2 + 1/(2*sqrt(3)), 1/2 + 1/(2*sqrt(3))])

# - 4 sides - #
# internal angle = 360
# V3.3.4.12
planigon4_1 = planigon([120, 120, 90, 30], [1/sqrt(3), 1/2 + 1/(2*sqrt(3)), (3 + sqrt(3))/2, 1 + 2/sqrt(3)])
# V3.4.3.12   
planigon4_2 = planigon([120, 90, 120, 30], [1/2 + 1/(2*sqrt(3)), 1/2 + 1/(2*sqrt(3)), 1 + 2/sqrt(3), 1 + 2/sqrt(3)])
# V3.3.6.6   
planigon4_3 = planigon([120, 120, 60, 60], [1/sqrt(3), 2/sqrt(3), sqrt(3), 2/sqrt(3)])
# V3.6.3.6   
planigon4_4 = planigon([120, 60, 120, 60], [2/sqrt(3), 2/sqrt(3), 2/sqrt(3), 2/sqrt(3)])
# V3.4.4.6   
planigon4_5 = planigon([120, 90, 90, 60], [1/2 + 1/(2*sqrt(3)), 1, (1 + sqrt(3))/2, 2/sqrt(3)])
# V3.4.6.4   
planigon4_6 = planigon([120, 90, 60, 90], [1/2 + 1/(2*sqrt(3)), (1 + sqrt(3))/2, (1 + sqrt(3))/2, 1/2 + 1/(2*sqrt(3))])
# V4.4.4.4
planigon4_7 = planigon([90, 90, 90, 90], [1, 1, 1, 1]) # square

# - 3 sides, dividable - #
# internal angle = 180
# V3.12.12   
#planigon3_1 = planigon([120, 30, 30], [1 + 2/sqrt(3), 1 + sqrt(3), 1 + 2/sqrt(3)])
planigon3_1 = planigon([120, 30, 30], [], [3, 12, 12])
# V4.6.12   
planigon3_2 = planigon([90, 60, 30], [(1 + sqrt(3))/2, 1 + sqrt(3), (3 + sqrt(3))/2])
# V6.6.6   
planigon3_3 = planigon([60, 60, 60], [sqrt(3), sqrt(3), sqrt(3)]) # equilateral triangle
# V4.8.8
planigon3_4 = planigon([90, 45, 45], [(2 + sqrt(2))/2, 1 + sqrt(2), (2 + sqrt(2))/2])

# - 3 sides, not dividable - #
# internal angle = 180
# V3.7.42   
planigon3_5 = planigon([120, 51 + (3/7), 8 + (4/7)], [], [3, 7, 42])
# V3.8.24   
planigon3_6 = planigon([120, 45, 15], [], [3, 8, 24])
# V3.9.18   
planigon3_7 = planigon([120, 40, 20], [], [3, 8, 18])
# V4.5.20   
planigon3_8 = planigon([90, 72, 18], [], [4, 5, 20])
# V3.10.15   
planigon3_9 = planigon([120, 36, 24], [], [3, 10, 15])
# V5.5.10
planigon3_10 = planigon([72, 72, 36], [], [5, 5, 10])

planigons = [planigon6_1, 
             planigon5_1, planigon5_2, planigon5_3,
             planigon4_1, planigon4_2, planigon4_3, planigon4_4, planigon4_5, planigon4_6, planigon4_7,
             planigon3_1, planigon3_2, planigon3_3, planigon3_4,
             planigon3_5, planigon3_6, planigon3_7, planigon3_8, planigon3_9, planigon3_10]

def normalize(v):
    norm = np.linalg.norm(v)
    return v if norm == 0 else v / norm

def rotate2D(v, angle):
    c, s = cos(angle), sin(angle)
    return np.array([v[0] * c - v[1] * s,
                     v[0] * s + v[1] * c])

# note: rotation direction is counterclockwise
def getPositionOfNextCoord(hostEdge : tuple[tuple[float, float], tuple[float, float]], rotationAngle: float, newEdgeLength: float) -> any:
    edgeVector = np.array(hostEdge[1]) - np.array(hostEdge[0])
    edgeDirection = normalize(edgeVector)
    newDir = edgeDirection
    newDir[0] = edgeDirection[0] * cos(rotationAngle) - edgeDirection[1] * sin(rotationAngle) 
    newDir[1] = edgeDirection[0] * sin(rotationAngle) + edgeDirection[1] * cos(rotationAngle)
    newPos = hostEdge[1] + (newEdgeLength * edgeDirection)
    return newPos

## --- Planigon components --- ##

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class nodeTracker:
    __metaclass__ = Singleton
    nodeRefs: list[node]

    def remove(self, node: node) -> bool:
        if node.availableAngle < 1.0:
            self.nodeRefs.remove(node)
            return True
        return False
    
    def add(self, node: node) -> bool:
        if self.nodeRefs.count(node) <= 0:
            self.nodeRefs.append(node)
            return True
        return False
    
    def checkIsDuplicate(self, node:node) -> int:
        for n in self.nodeRefs:
            if abs(n.x - node.x) < 0.01 and abs(n.y - node.y) < 0.01:
                return self.nodeRefs.index(n)
        return -1
    
@dataclass
class Vertex:
    pos: tuple[float, float]
    outgoing: Optional['HalfEdge'] = None

@dataclass
class HalfEdge:
    origin: 'Vertex'
    twin: Optional['HalfEdge'] = None
    next: Optional['HalfEdge'] = None
    prev: Optional['HalfEdge'] = None
    face: Optional['Face'] = None
    boundary: bool = False

def iterate(he: HalfEdge) -> list[HalfEdge]:
    results = []
    results.append(he)
    curr = he.next
    while curr is not None and curr is not he:
        results.append(curr)
        curr = curr.next
    return results


@dataclass
class Face:
    edge: Optional['HalfEdge'] = None
    planigon_type: Optional[int] = None



class VertexIndex:
    def __init__(self, cell_size=1e-3):
        self.cell_size = cell_size
        self.grid = {}  # dict[(ix, iy)] -> list[Vertex]

    def _cell_coords(self, pos):
        return (math.floor(pos[0] / self.cell_size),
                math.floor(pos[1] / self.cell_size))

    def find_near(self, pos, eps):
        ix, iy = self._cell_coords(pos)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for v in self.grid.get((ix+dx, iy+dy), []):
                    if ((v.pos[0]-pos[0])**2 + (v.pos[1]-pos[1])**2) <= eps**2:
                        return v
        return None

    def add(self, v: Vertex):
        cell = self._cell_coords(v.pos)
        self.grid.setdefault(cell, []).append(v)

edge_map = {}  # dict[(vx_id, vy_id)] -> HalfEdge

class Diagram:
    edges: Optional[list['HalfEdge']] = None
    faces: Optional[list['Face']] = None
    vertices: Optional[list['Vertex']] = None
    vertex_index: VertexIndex
    edge_map = {}  # dict[(vx_id, vy_id)] -> HalfEdge

    def __init__(self):
        self.vertex_index = VertexIndex()

    def add_planigon(self, vertices_pos: list[tuple[float, float]]) -> Face:
        verts = []
        for p in vertices_pos:
            v = self.vertex_index.find_near(p, eps=1e-5)
            if not v:
                v = Vertex(p)
                self.vertex_index.add(v)
            verts.append(v)

        halfedges = []
        n = len(verts)
        for i in range(n):
            a, b = verts[i], verts[(i+1) % n]
            he = HalfEdge(origin=a)
            halfedges.append(he)
            a.outgoing = he
            key = (id(a), id(b))
            rev_key = (id(b), id(a))
            if rev_key in edge_map:
                twin = edge_map[rev_key]
                he.twin = twin
                twin.twin = he
                del edge_map[rev_key]
            else:
                edge_map[key] = he

        # link the cycle
        for i in range(n):
            halfedges[i].next = halfedges[(i+1) % n]
            halfedges[i].prev = halfedges[(i-1) % n]

        # create face
        f = Face(edge=halfedges[0])
        for he in halfedges:
            he.face = f

        return f

def getPlanigonVertices(in_origin, in_destination, edgeIdx, edgeLengths, Angles) -> list[Vertex]:
    results = [in_origin, in_destination]
    # base vector (direction from origin to destination)
    base_vec = np.array(in_destination.pos) - np.array(in_origin.pos)

    # scale factor to match this planigon’s nominal edge length to actual
    s = np.linalg.norm(base_vec) / edgeLengths[edgeIdx]

    # normalized direction vector
    n = normalize(base_vec)

    curr_pos = np.array(in_destination.pos)

    # we already have two vertices, compute the rest
    # we need len(edgeLengths) - 2 more
    for step in range(1, len(edgeLengths) - 1):
        curr_edge_idx = (edgeIdx + step) % len(edgeLengths)
        curr_angle_idx = (edgeIdx + step) % len(Angles)
        print("edgeIdx:", edgeIdx)
        print("sequence:", [(curr_edge_idx, curr_angle_idx) 
                        for step in range(1, len(edgeLengths)-1)])
        
        # turn to next edge direction
        n = rotate2D(n, -(pi - np.radians(Angles[curr_angle_idx])))

        # advance position
        curr_pos = curr_pos + n * edgeLengths[curr_edge_idx] * s

        # create vertex object (same type as input)
        vtx = Vertex(pos=tuple(curr_pos))
        results.append(vtx)

    return results


