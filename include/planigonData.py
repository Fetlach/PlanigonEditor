from typing import Self

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

    def __init__(self, angles: list[float], lengths: list[float]):
        self.angles = angles
        self.lengths = lengths
        

## --- Planigon layouts --- ##
planigon1 = planigon([60, 60, 60, 60, 60, 60], [1, 1, 1, 1, 1, 1]) # hexagon - V6^3

planigon2 = planigon([60, 60, 60, 90, 90])
planigon3 = planigon([60, 60, 60, 60, 120])

planigon4 = planigon([60, 60, 90, 150])
planigon5 = planigon([60, 60, 120, 120])
planigon6 = planigon([60, 90, 90, 120])
planigon7 = planigon([90, 90, 90, 90], [1, 1, 1, 1]) # square

planigon8 = planigon([60, 128 + (4/7), 171 + (3/7)])
planigon9 = planigon([60, 135, 165])
planigon10 = planigon([60, 140, 160])
planigon11 = planigon([60, 144, 156])
planigon12 = planigon([60, 150, 150])
planigon13 = planigon([90, 108, 162])
planigon14 = planigon([90, 120, 150])
planigon15 = planigon([90, 135, 135]) # can't use this one with others
planigon16 = planigon([108, 108, 144])
planigon17 = planigon([120, 120, 120], [1, 1, 1]) # equilateral triangle

## --- Planigon components --- ##
class planigonComponent:
    nodes : list[node]
    planigonRef : planigon
    depth : int
    parentSide : int
    flipped : bool
    children : list[Self]

    def __init__(self, nodeArr: list[node], planigon: planigon, depth: int, parentSideIdx: int, flipped: bool):
        self.nodes = nodeArr
        self.planigonRef = planigon
        self.depth = depth
        self.parentSideIdx = parentSideIdx
        self.flipped = flipped
        self.children = []


    def Attach(self, planigon: planigon, mySide: int, attacheeSide: int, attacheeFlipped: bool) -> bool:
        # check other children to see if attached side is occupied
        for child in self.children:
            if child.parentSide is mySide:
                return False
        
        # check nodes on edge to see if attachment is possible
        # check left node
        # check right node

        # create new nodes for child, fill in own nodes for edge
        childNodes = []
        
        # create new component
        newChild = planigonComponent(childNodes, planigon, self.depth + 1, mySide, attacheeFlipped)

        # update own children
        self.children.append(newChild)

        # update own nodes
        # update left node
        # update right node
            #if node.leftSide.ID is self and node.leftSide.idx is mySide:
                # attachee is new left node
        # 
        
        return True

    def Delete(self):
        # recursive delete down tree
        for comp in self.attachedIDs:
            comp.Delete()
        # update attached nodes to remove self attachment

        del self
