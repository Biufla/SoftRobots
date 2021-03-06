from splib3.objectmodel import SofaPrefab, SofaObject
from splib3.numerics import getOrientedBoxFromTransform


@SofaPrefab
class FixingBox(SofaObject):
    """Fix a set of 'dofs' according to a translation & orientation"""

    def __init__(self, parent, target, name="FixingBox",
                 translation=[0.0, 0.0, 0.0], eulerRotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0]):

        ob = getOrientedBoxFromTransform(translation=translation, eulerRotation=eulerRotation, scale=scale)

        self.node = parent.addChild(name)
        self.node.addObject("BoxROI",
                               orientedBox=ob,
                               name="boxroi",
                               position=target.dofs.getData("rest_position"),
                               drawBoxes=False)

        c = self.node.addChild("Constraint")
        target.addChild(c)

        c.addObject('RestShapeSpringsForceField',
                       points=self.node.boxroi.getData("indices"),
                       stiffness='1e12')
