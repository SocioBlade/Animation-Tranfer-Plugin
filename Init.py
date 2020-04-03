import sys

if "F:/Summer2019/AnimationTransferPlugin/AnimTransferAssignment/final" not in sys.path:
    sys.path.append("F:/Summer2019/AnimationTransferPlugin/AnimTransferAssignment/final/")
    import LoadMyUI as myUI
        
reload(myUI)
ui = myUI.uiLoad("F:/Summer2019/AnimationTransferPlugin/AnimTransferAssignment/final/AnimationTransferUI.ui")
controllerClass = myUI.UIController(ui)