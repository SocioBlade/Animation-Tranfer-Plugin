import pymel.core as pm
from maya import OpenMayaUI as mayaUi
from PySide2 import QtGui, QtCore, QtWidgets, QtUiTools
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtUiTools import *
from PySide2.QtWidgets import *
from shiboken2 import wrapInstance
import AnimationTransferMaster as at
reload(at)

sRootJoint = pm.ls(sl=True)[0]
tRootJoint = pm.ls(sl=True)[1]
sourceTree = []
targetTree = []
targetIndex = []

sListLength = 0
tListLength = 0

def getMayaWindow():
    mayaWindowPointer = mayaUi.MQtUtil.mainWindow()
    mayaWin = wrapInstance(long(mayaWindowPointer), QWidget)
    
def fixXML(path, qbyteArray):
    if path[-1] != "/":
        path += "/"
    path = path.replace("/", "\\")
    
    tempArr = QByteArray("<pixmap>" + path + "\\")
    
    lastPos = qbyteArray.indexOf("<pixmap>", 0)
    while lastPos != -1:
        qbyteArray.replace(lastPos, len("<pixmap"), tempArr)
        lastPos = qbyteArray.indexOf("<pixmap>", lastPos +1)
    return
    
def uiLoad(path):
    loader = QUiLoader()
    uiFile = QFile(path)
    
    dirIconShapes = ''
    buff = None
    
    if uiFile.exists():
        dirIconShapes = path
        uiFile.open(QFile.ReadOnly)
        
        buff = QByteArray(uiFile.readAll())
        uiFile.close()
    else:
        print 'UI file does not exist'
        exit(-1)
    
    fixXML(path, buff)
    qBuff = QBuffer()
    qBuff.open(QBuffer.ReadOnly | QBuffer.WriteOnly)
    qBuff.write(buff)
    qBuff.seek(0)
    ui = loader.load(qBuff, parentWidget = getMayaWindow())
    ui.path = path
    return ui


class UIController:
    def __init__(self, ui):
        #Connect ui signals
        ui.TransferButton.clicked.connect(self.animationTransfer)
        ui.Up_Left.clicked.connect(lambda: self.Up_Left(ui))
        ui.Up_Right.clicked.connect(lambda: self.Up_Right(ui))
        ui.Delete_Left.clicked.connect(lambda: self.Delete_Left(ui))
        ui.Delete_Right.clicked.connect(lambda: self.Delete_Right(ui))
        ui.Down_Left.clicked.connect(lambda: self.Down_Left(ui))
        ui.Down_Right.clicked.connect(lambda: self.Down_Right(ui))
        
        self.getList(ui)
        sListLength = len(sourceTree)
        tListLength = len(targetTree)

        self.ui = ui
        ui.setWindowFlags(Qt.WindowStaysOnTopHint)
        ui.show()

    def cleanUpLists(self):
        del at.isolatedRotation[:]
        del at.worldSpaceRotation[:]
        del at.translatedRotation[:]

    def copyPasteRootAttribs(self, rootJointS, rootJointT):
        rootJointT.setRotation(rootJointS.getRotation())
        rootJointT.setTranslation(rootJointS.getTranslation())
        rootJointT.setOrientation(rootJointS.getOrientation())

    def animationTransfer(self):
        for at.frames in range(at.timeLen):
            pm.currentTime(at.frames)

            self.cleanUpLists()

            rootJointS = pm.ls(sl=True)[0]
            rootJointT = pm.ls(sl=True)[1]

            at.sourceTree(rootJointS, at.frames, sListLength)
            at.targetTree(rootJointT, at.frames, tListLength)
            at.setTargetTree(rootJointT)
            at.getBindPose = 1

            self.copyPasteRootAttribs(rootJointS, rootJointT)

            pm.setKeyframe(rootJointT)
            print 'Frame: ' + str(at.frames) + ' calculated of: ' + str(at.timeLen - 1)

    def getList(self, ui):
        ui.SourceRoot.setText(str(sRootJoint))
        del sourceTree[:]
        at.printTree(sRootJoint, 'source')

        self.updateSourceList(ui, sourceTree)

        ui.TargetRoot.setText(str(tRootJoint))
        del targetTree[:]
        at.printTree(tRootJoint, 'target')

        self.updateTargetList(ui, targetTree)

        if at.firstPass == 0:
            for nrOfJoints in range(len(sourceTree)):
                targetIndex.append(nrOfJoints)
            at.firstPass = 1
    
    def updateSourceList(self, ui, sourceTree):
        sItemModel = QStandardItemModel(ui.SourceList)
        for joint in sourceTree:
            item = QStandardItem(str(joint))
            sItemModel.appendRow(item)
        ui.SourceList.setModel(sItemModel)

    def updateTargetList(self, ui, targetTree):
        tItemModel = QStandardItemModel(ui.TargetList)
        for joint in targetTree:
            item = QStandardItem(str(joint))
            tItemModel.appendRow(item)
        ui.TargetList.setModel(tItemModel)

    def Up_Left(self, ui):
        listIndex = ui.SourceList.currentIndex()
        itemName = str(listIndex.data())
        select = pm.select(itemName)
        joint = pm.ls(sl=True)[0]
        pm.undo()

        temp = sourceTree[listIndex.row()]
        sourceTree[listIndex.row()] = sourceTree[listIndex.row() -1]
        sourceTree[listIndex.row() - 1] = temp

        self.updateSourceList(ui, sourceTree)

    def Up_Right(self, ui):
        listIndex = ui.TargetList.currentIndex()
        itemName = str(listIndex.data())
        selected = pm.select(itemName)
        joint = pm.ls(sl=True)[0]
        pm.undo()

        temp = targetTree[listIndex.row()]
        targetTree[listIndex.row()] = targetTree[listIndex.row() -1]
        targetTree[listIndex.row() - 1] = temp
    
        tempIndex = targetIndex[listIndex.row()]
        targetIndex[listIndex.row()] = targetIndex[listIndex.row() - 1]
        targetIndex[listIndex.row() - 1] = tempIndex

        self.updateTargetList(ui, targetTree)

    def Delete_Left(self, ui):
        listIndex = ui.SourceList.currentIndex()

        del sourceTree[listIndex.row()]
        self.updateSourceList(ui, sourceTree)

    def Delete_Right(self, ui):
        listIndex = ui.TargetList.currentIndex()

        if len(targetTree) > len(sourceTree):
            targetIndex[listIndex.row()] = -1
            for targets in range(len(targetIndex)):
                if targets > listIndex.row():
                    targetIndex[targets] -= 1
        else:
            targetIndex[listIndex.row()] = len(targetIndex) + 1
        
        del targetTree[listIndex.row()]
        self.updateTargetList(ui, targetTree)

    def Down_Left(self, ui):
        listIndex = ui.SourceList.currentIndex()
        itemName = str(listIndex.data())
        selected = pm.select(itemName)
        joint = pm.ls(sl=True)[0]
        pm.undo()

        temp = sourceTree[listIndex.row()]
        sourceTree[listIndex.row()] = sourceTree[listIndex.row() + 1]
        sourceTree[listIndex.row() + 1] = temp

        self.updateSourceList(ui, sourceTree)
    
    def Down_Right(self, ui):
        listIndex = ui.TargetList.currentIndex()
        itemName = str(listIndex.data())
        selected = pm.select(itemName)
        joint = pm.ls(sl=True)[0]
        pm.undo()

        temp = targetTree[listIndex.row()]
        targetTree[listIndex.row()] = targetTree[listIndex.row() + 1]
        targetTree[listIndex.row() +1 ] = temp

        tempIndex = targetIndex[listIndex.row()]
        targetIndex[listIndex.row()] = targetIndex[listIndex.row() + 1]
        targetIndex[listIndex.row() + 1] = tempIndex

        self.updateTargetList(ui, targetTree)
   