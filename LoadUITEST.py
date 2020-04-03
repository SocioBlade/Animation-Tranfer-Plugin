import pymel.core as pm
from maya import OpenMayaUI as mayaUi
import PySide2
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
        ui.Tranfer.clicked.connect(self.animationTransfer)
        ui.L_Up.clicked.connect(lambda: self.L_Up(ui))
        ui.R_Up.clicked.connect(lambda: self.R_Up(ui))
        ui.L_Delete.clicked.connect(lambda: self.L_Delete(ui))
        ui.R_Delete.clicked.connect(lambda: self.R_Delete(ui))
        ui.L_Down.clicked.connect(lambda: self.L_Down(ui))
        ui.R_Down.clicked.connect(lambda: self.R_Down(ui))
        
        self.getList(ui)
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

            at.sourceTree(rootJointS, at.frames)
            at.targetTree(rootJointT, at.frames)
            at.setTargetTree(rootJointT)
            at.getBindPose = 1

            self.copyPasteRootAttribs(rootJointS, rootJointT)

            pm.setKeyframe(rootJointT)
            print 'Frame: ' + str(at.frames) + ' calculated of: ' + str(at.timeLen)

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
        sourceModel = QStandardItemModel(ui.SourceList)

        for joint in sourceTree:
            item = QStandardItem(str(joint))
            sourceModel.appendRow(item)
        
        ui.SourceList.setModel(sourceModel)

    def updateTargetList(self, ui, targetTree):
        targetModel = QStandardItemModel(ui.TargetList)
        for joint in targetTree:
            item = QStandardItem(str(joint))
            targetModel.appendRow(item)
        ui.TargetList.setModel(targetModel)

    def L_Up(self, ui):
        index = ui.SourceList.currentIndex()
        itemText = str(index.data())

        select = pm.select(itemText)
        selectedJoint = pm.ls(sl=True)[0]
        pm.undo()

        temp = sourceTree[index.row()]
        sourceTree[index.row()] = sourceTree[index.row() -1]
        sourceTree[index.row() - 1] = temp

        self.updateSourceList(ui, sourceTree)

    def R_Up(self, ui):
        index = ui.TargetList.currentIndex()
        itemText = str(index.data())

        selected = pm.select(itemText)
        selectedJoint = pm.ls(sl=True)[0]
        pm.undo()

        temp = targetTree[index.row()]
        targetTree[index.row()] = targetTree[index.row() -1]
        targetTree[index.row() - 1] = temp

        tempIndex = targetIndex[index.row()]
        targetIndex[index.row()] = targetIndex[index.row() - 1]
        targetIndex[index.row() - 1] = tempIndex

        self.updateTargetList(ui, targetTree)

    def L_Delete(self, ui):
        index = ui.SourceList.currentIndex()

        del sourceTree[index.row()]
        print sourceTree

        self.updateSourceList(ui, sourceTree)

    def R_Delete(self, ui):
        index = ui.TargetList.currentIndex()

        if len(targetTree) > len(sourceTree):
            targetIndex[index.row()] = -1
            for targets in range(len(targetIndex)):
                if targets > index.row():
                    targetIndex[targets] -= 1
        
        else:
            targetIndex[index.row()] = len(targetIndex) + 1
        
        del targetTree[index.row()]
        print targetIndex
        self.updateTargetList(ui, targetTree)

    def L_Down(self, ui):
        index = ui.SourceList.currentIndex()
        itemText = str(index.data())

        selected = pm.select(itemText)
        selectedJoint = pm.ls(sl=True)[0]
        pm.undo()

        temp = sourceTree[index.row()]
        sourceTree[index.row()] = sourceTree[index.row() + 1]
        sourceTree[index.row() + 1] = temp

        self.updateSourceList(ui, sourceTree)
    
    def R_Down(self, ui):
        index = ui.TargetList.currentIndex()
        itemText = str(index.data())

        selected = pm.select(itemText)
        selectedJoint = pm.ls(sl=True)[0]
        pm.undo()

        temp = targetTree[index.row()]
        targetTree[index.row()] = targetTree[index.row() + 1]
        targetTree[index.row() +1 ] = temp

        tempIndex = targetIndex[index.row()]
        targetIndex[index.row()] = targetIndex[index.row() + 1]
        targetIndex[index.row() + 1] = tempIndex

        self.updateTargetList(ui, targetTree)
   