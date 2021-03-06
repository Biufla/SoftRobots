from splib.numerics import sin, cos, to_radians
from stlib.physics.deformable import ElasticMaterialObject
from actuatedarm import ActuatedArm
from stlib.physics.collision import CollisionMesh
from splib.objectmodel import SofaPrefab, SofaObject
from stlib.physics.mixedmaterial import Rigidify
from stlib.components import addOrientedBoxRoi
from splib.numerics import vec3
from splib.numerics.quat import Quat
from tutorial import *


def ElasticBody(parent):
    body = parent.createChild("ElasticBody")

    e = ElasticMaterialObject(body,
                              volumeMeshFileName="data/mesh/tripod_mid.gidmsh",
                              translation=[0.0, 30, 0.0], rotation=[90, 0, 0],
                              youngModulus=800, poissonRatio=0.45, totalMass=0.032)

    visual = body.createChild("Visual")
    visual.createObject("MeshSTLLoader", name="loader", filename="data/mesh/tripod_mid.stl")
    visual.createObject("OglModel", name="renderer", src="@loader", color=[1.0, 1.0, 1.0, 0.5],
                        rotation=[90, 0, 0], translation=[0, 30, 0])

    visual.createObject("BarycentricMapping",
                        input=e.dofs.getLinkPath(),
                        output=visual.renderer.getLinkPath())

    return body


@SofaPrefab
class Tripod(SofaObject):

    def __init__(self, parent, name="Tripod", radius=60, numMotors=3, angleShift=180.0):
        self.node = parent.createChild(name)
        ElasticBody(self.node)

        dist = radius
        numstep = numMotors
        self.actuatedarms = []
        for i in range(0, numstep):
            name = "ActuatedArm"+str(i)
            translation, eulerRotation = self.__getTransform(i, numstep, angleShift, radius, dist)
            arm = ActuatedArm(self.node, name=name,
                              translation=translation, eulerRotation=eulerRotation)
            self.actuatedarms.append(arm)
            # Add limits to angle that correspond to limits on real robot
            arm.ServoMotor.minAngle = -2.0225
            arm.ServoMotor.maxAngle = -0.0255

        self.__attachToActuatedArms(radius, numMotors, angleShift)

    def __getTransform(self, index, numstep, angleShift, radius, dist):
        fi = float(index)
        fnumstep = float(numstep)
        angle = fi*360/fnumstep
        angle2 = fi*360/fnumstep+angleShift
        eulerRotation = [0, angle, 0]
        translation = [dist*sin(to_radians(angle2)), -1.35, dist*cos(to_radians(angle2))]

        return translation, eulerRotation

    def addCollision(self):
        CollisionMesh(self.node.ElasticBody.ElasticMaterialObject, surfaceMeshFileName="data/mesh/tripod_low.stl", name="CollisionModel", translation=[0.0, 30, 0.0], rotation=[90, 0, 0], collisionGroup=1)

        for arm in self.actuatedarms:
            CollisionMesh(arm.ServoMotor.ServoBody,
                          surfaceMeshFileName="data/mesh/servo_collision.stl",
                          name="TopServoCollision", mappingType='RigidMapping')

    def __attachToActuatedArms(self, radius=60, numMotors=3, angleShift=180.0):
        deformableObject = self.node.ElasticBody.ElasticMaterialObject

        dist = radius
        numstep = numMotors
        groupIndices = []
        frames = []
        for i in range(0, numstep):
            translation, eulerRotation = self.__getTransform(i, numstep, angleShift, radius, dist)
            box = addOrientedBoxRoi(self.node, position=deformableObject.dofs.getData("rest_position"), name="BoxROI"+str(i),
                                    translation=vec3.vadd(translation, [0.0, 25.0, 0.0]),
                                    eulerRotation=eulerRotation, scale=[45, 15, 30])

            box.drawBoxes = False
            box.init()
            deformableObject.init()
            groupIndices.append([ind[0] for ind in box.indices])
            frames.append(vec3.vadd(translation, [0.0, 25.0, 0.0]) + list(Quat.createFromEuler([0, float(i)*360/float(numstep), 0], inDegree=True)))

        # Rigidify the deformable part at extremity to attach arms
        rigidifiedstruct = Rigidify(self.node, deformableObject, groupIndices=groupIndices, frames=frames, name="RigidifiedStructure")
        rigidifiedstruct.DeformableParts.createObject("UncoupledConstraintCorrection")
        rigidifiedstruct.RigidParts.createObject("UncoupledConstraintCorrection")

        # Use this to activate some rendering on the rigidified object ######################################
        # setData(rigidifiedstruct.RigidParts.dofs, showObject=True, showObjectScale=10, drawMode=2)
        # setData(rigidifiedstruct.RigidParts.RigidifiedParticules.dofs, showObject=True, showObjectScale=1,
        #         drawMode=1, showColor=[1., 1., 0., 1.])
        # setData(rigidifiedstruct.DeformableParts.dofs, showObject=True, showObjectScale=1, drawMode=2)
        #####################################################################################################

        # Attach arms
        for i in range(0, numstep):
            rigidifiedstruct.RigidParts.createObject('RestShapeSpringsForceField', name="rssff"+str(i),
                                                     points=i,
                                                     external_rest_shape=self.actuatedarms[i].servoarm.dofs,
                                                     stiffness='1e12', angularStiffness='1e12')


def createScene(rootNode):
    scene = Scene(rootNode)

    scene.VisualStyle.displayFlags = "showBehavior"

    tripod = Tripod(scene.Modelling)

    scene.Simulation.addChild(tripod.RigidifiedStructure)
    motors = scene.Simulation.createChild("Motors")
    motors.addChild(tripod.ActuatedArm0)
    motors.addChild(tripod.ActuatedArm1)
    motors.addChild(tripod.ActuatedArm2)
