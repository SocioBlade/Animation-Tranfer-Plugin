import pymel.core as pm
import pymel.core.datatypes as dt
import LoadMyUI as myUI

maxTime = pm.playbackOptions(q = True, max = True)
minTime = pm.playbackOptions(q = True, min = True)

timeLen = int((maxTime - minTime) + 2)

getBindPose = 0
firstPass = 0
sourceCount = 0
targetCount = 0

#Math results stored in lists
isolatedRotation = []
worldSpaceRotation = []
translatedRotation = []

sJointRotation = []
sJointOrientation = []
tJointRotation = []

newSourceList = []
newTargetList = []

def printTree(node, aList):
    for child in node.getChildren():
        if aList == 'source':
            myUI.sourceTree.append(child)
        if aList == 'target':
            myUI.targetTree.append(child)
        printTree(child, aList)

def calcSourceParentBP(child, parentBindPose):
    parent = child.getParent()
    if parent:
        parentBindPose = calcSourceParentBP(parent, parentBindPose)
        #parentBindPose = (parent.getRotation().asMatrix() * parent.getOrientation().asMatrix()) * parentBindPose
        parentBindPose = (dt.EulerRotation(parent.rotate.get(t = 0)).asMatrix() * dt.EulerRotation(parent.jointOrient.get(t = 0)).asMatrix()) * parentBindPose

    return parentBindPose

def sourceTree(sourceTreeItem, currTime, listLength):
    global sourceCount
    global getBindPose
    global newSourceList
    global sJointRotation
    global sJointOrientation
    print 'sourceTreeItem'
    print sourceTreeItem
    childIndex = 0
        
    if sourceCount != 0:
        for items in range(listLength):
            if getBindPose == 0:
                print 'inside bindPose'
                sJointRotation.append(sourceTreeItem.getRotation().asMatrix())
                sJointOrientation.append(sourceTreeItem.getOrientation().asMatrix())      
            
            print 'before if count'
            print sourceCount
            print sourceCount
            print 'sJointRotation'
            print sJointRotation
            #k1 calculation
            isolatedRotation.append(sJointRotation[childIndex].inverse() * sourceTreeItem.getRotation().asMatrix())

            #k2 calculation
            #pm.currentTime(0)       
    
            parentBindPose = 1
            sourceParentBP = calcSourceParentBP(sourceTreeItem, parentBindPose)
            
            #pm.currentTime(currTime)
            print 'Before worldspacerotation'
            print sourceTreeItem
            worldSpaceRotation.append(sourceTreeItem.getOrientation().asMatrix().inverse() * sourceParentBP.inverse() * isolatedRotation[childIndex] * sourceParentBP * sourceTreeItem.getOrientation().asMatrix())
            
            
            sourceCount += 1
            print 'listLength'
            print listLength
            if listLength > sourceCount:
                print 'SourceList in if'
                print sourceCount
                sourceTree (newSourceList[sourceCount], currTime, listLength)
            elif listLength == sourceCount:
                print 'SourceList in if'
                print sourceCount
                sourceTree (newSourceList[sourceCount], currTime, listLength)
    else:
        print 'first'
        print listLength
        sourceCount += 1
        sourceTree(newSourceList[sourceCount], currTime, listLength)
    


def targetTree(targetTreeItem, currTime, listLength):
    global targetCount
    global newTargetList
    global getBindPose
    global tJointRotation

    if targetCount != 0:
        for items in range(listLength):

            if getBindPose == 0:
                tJointRotation.append(targetTreeItem.getRotation().asMatrix())
                pm.setKeyframe(targetTreeItem)

                #pm.currentTime(0)
            
            parentBindPose = 1
            targetParentBP = calcSourceParentBP(targetTreeItem, parentBindPose)

            pm.currentTime(currTime)

            translatedRotation.append(targetTreeItem.getOrientation().asMatrix() * targetParentBP * worldSpaceRotation[targetCount] * targetParentBP.inverse() * targetTreeItem.getOrientation().asMatrix().inverse()) 

            translatedRotation[targetCount] = tJointRotation[targetCount] * translatedRotation[targetCount]

            targetTreeItem.setRotation(dt.degrees(dt.EulerRotation(translatedRotation[targetCount])))

            targetCount += 1
            if listLength != targetCount:
                targetTree (targetList[targetCount], currTime, listLength)
            
            #Calculate the rotation for the node and set keyframe if node is still in the list
            checkViable = checkInList(node, aList)
    
            if checkVialbe == 1:
                pm.setKeyFrame()
    else:
        targetCount += 1
        targetTree(targetList[targetCount], currTime, listLength)


    
def setNewLists(sourceList, targetList, sourceRoot, targetRoot):
    global sourceCount
    global targetCount
    global getBindPose
    global newSourceList
    global newTargetList

    newSourceList.append(sourceRoot)
    newSourceList.extend(sourceList)
    newTargetList.append(targetRoot)
    newTargetList.extend(targetList)

    sListLength = len(sourceList)
    tListLength = len(targetList)
    print 'sListLength'
    print sListLength
    print 'tListLength'
    print tListLength

    for frames in range(timeLen):
            pm.currentTime(frames)

            cleanUpLists()

            sourceTree(newSourceList[sourceCount], frames, sListLength)
            targetTree(newTargetList[targetCount], frames, tListLength)
            getBindPose = 1

            copyPasteRootAttribs(sourceRoot, targetRoot)

            pm.setKeyframe(targetRoot)
            print 'Frame: ' + str(frames) + ' calculated of: ' + str(timeLen - 1)

def checkInList(node, listLength):
    found = 0
    selectedJntName = node.name()

    for item in range(listLength):
        temp = [item]
        if temp == selectedJntName:
            found = 1

            return found
        else:
            found = 0

    return found

def cleanUpLists():
    del isolatedRotation[:]
    del worldSpaceRotation[:]
    del translatedRotation[:]

def copyPasteRootAttribs(rootJointS, rootJointT):
    rootJointT.setRotation(rootJointS.getRotation())
    rootJointT.setTranslation(rootJointS.getTranslation())
    rootJointT.setOrientation(rootJointS.getOrientation())