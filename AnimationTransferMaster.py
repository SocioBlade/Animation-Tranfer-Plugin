import pymel.core as pm
import pymel.core.datatypes as dt
import LoadMyUI as myUI

maxTime = pm.playbackOptions(q = True, max = True)
minTime = pm.playbackOptions(q = True, min = True)

timeLen = int((maxTime - minTime) + 2)

getBindPose = 0
firstPass = 0

#Math results stored in lists
isolatedRotation = []
worldSpaceRotation = []
translatedRotation = []

sJointRotation = []
sJointOrientation = []
tJointRotation = []

def printTree(node, listType):
    for child in node.getChildren():
        printTree(child, listType)
        if listType == 'source':
            myUI.sourceTree.append(child)
        if listType == 'target':
            myUI.targetTree.append(child)

def calcSourceParentBP(child, parentBindPose):
    parent = child.getParent()
    if parent:
        parentBindPose = calcSourceParentBP(parent, parentBindPose)
        #parentBindPose = (parent.getRotation().asMatrix() * parent.getOrientation().asMatrix()) * parentBindPose
        parentBindPose = (dt.EulerRotation(parent.rotate.get(t = 0)).asMatrix() * dt.EulerRotation(parent.jointOrient.get(t = 0)).asMatrix()) * parentBindPose

    return parentBindPose

def sourceTree(node, currTime, jointIndex = 0):
    for child in node.getChildren():
        if child.numChildren() > 0:
            jointIndex = sourceTree (child, currTime, jointIndex)
        
        if getBindPose == 0:
            sJointRotation.append(child.getRotation().asMatrix())
            sJointOrientation.append(child.getOrientation().asMatrix())      
        
        isolatedRotation.append(sJointRotation[jointIndex].inverse() * child.getRotation().asMatrix())

        parentBindPose = 1
        sourceParentBP = calcSourceParentBP(child, parentBindPose)

        worldSpaceRotation.append(child.getOrientation().asMatrix().inverse() * sourceParentBP.inverse() * isolatedRotation[jointIndex] * sourceParentBP * child.getOrientation().asMatrix())
        jointIndex += 1
    
    return jointIndex


def targetTree(node, currTime, jointIndex = 0, targetIndex = 0):
    for child in node.getChildren():
        if child.numChildren() > 0:
            jointIndex, targetIndex = targetTree(child, currTime, jointIndex, targetIndex)
        
        if myUI.targetIndex[targetIndex] > -1:
            if getBindPose == 0:
                tJointRotation.append(child.getRotation().asMatrix())
                pm.setKeyframe(child)

            parentBindPose = 1
            targetParentBP = calcSourceParentBP(child, parentBindPose)

            pm.currentTime(currTime)

            translatedRotation.append(child.getOrientation().asMatrix() * targetParentBP * worldSpaceRotation[jointIndex] * targetParentBP.inverse() * child.getOrientation().asMatrix().inverse()) 

            translatedRotation[jointIndex] = tJointRotation[jointIndex] * translatedRotation[jointIndex]
     
            child.setRotation(dt.degrees(dt.EulerRotation(translatedRotation[jointIndex])))
            
            jointIndex += 1
                
        targetIndex += 1
    return jointIndex, targetIndex
    
def setTargetTree(node, jointIndex = 0, targetIndex = 0):
    for child in node.getChildren():
        if child.numChildren() > 0:
            jointIndex, targetIndex = setTargetTree(child, jointIndex, targetIndex)

        if myUI.targetIndex[targetIndex] < len(myUI.targetTree) + 1:
            if myUI.targetIndex[targetIndex] > -1:
                child.setRotation(dt.degrees(dt.EulerRotation(translatedRotation[myUI.targetIndex[targetIndex]])))
                pm.setKeyframe(child)
                jointIndex += 1
        else:
            jointIndex += 1

        targetIndex += 1

    return jointIndex, targetIndex