# -*- utf-8
# ==================================================================
# Changes appearance in Maya viewport to bounding box on interaction
# Author: Mahendra Gangaiwar
# Disclaimer: Not tested in production
# ==================================================================
"""Makes your interaction in viewport fast, by installing this event
viewport changes to bounding box

Usage::

    >> tracker = BBBlastTracker('modelPanel1')
    >> tracker.install()
    >> tracker.uninstall()
    # OR from active camera view
    >> BBBlastTracker.install_from_active_panel()

"""
import shiboken2
from PySide2 import QtWidgets, QtCore

import maya.cmds as cmds
import maya.OpenMayaUI as apiUI


class BBBlastTracker(QtCore.QObject):
    _all = []

    # ---- Constructors
    @classmethod
    def install_from_active_panel(cls):
        """Install event from current active view"""
        panel = cmds.getPanel(wf=True)
        editor = cmds.modelPanel(panel, q=True, modelEditor=True)
        watcher = cls(editor)
        watcher.install()
        return watcher

    @classmethod
    def uninstall_all(cls):
        """Uninstall all events"""
        [each.uninstall() for each in cls._all]

    # ---- Initializer
    def __init__(self, editor):
        """Makes your interaction in viewport fast, by installing this event
        viewport changes to bounding box

        Args:
            editor(str): modelEditor

        Usage::

            >> tracker = BBBlastTracker('modelPanel1')
            >> tracker.install()
            >> tracker.uninstall()
            # OR
            >> BBBlastTracker.install_from_active_panel()

        """
        super(BBBlastTracker, self).__init__()

        self.editor = editor
        self.last_appearance = cmds.modelEditor(self.editor,
                                                q=True,
                                                displayAppearance=True)
        self.restore_on_release = True
        self.timer = None
        self.timeout = 0.05

        # get QWidget from the view
        view = apiUI.M3dView()
        apiUI.M3dView.getM3dViewFromModelPanel(self.editor, view)
        self.view = shiboken2.wrapInstance(long(view.widget()),
                                           QtWidgets.QWidget)
        self.__class__._all.append(self)

    # ---- Behaviour
    def set_bb_appearance(self):
        """Set BoundingBox appearance for current view"""
        cmds.modelEditor(self.editor, e=True, displayAppearance="boundingBox")

    def restore_appearance(self):
        """Restore appearance for current view"""
        cmds.modelEditor(self.editor,
                         e=True,
                         displayAppearance=self.last_appearance)

    def _check_n_restore(self):
        """Start timer which would check if appearence need to be restored"""
        if QtWidgets.QApplication.queryKeyboardModifiers(
        ) != QtCore.Qt.AltModifier:
            cmds.modelEditor(self.editor,
                             e=True,
                             displayAppearance=self.last_appearance)
            self.timer = None
        else:
            self.start_timer()

    def start_timer(self):
        """Start timer which would check if appearence need to be restored"""
        if self.timer is None or (isinstance(self.timer, QtCore.QTimer)
                                  and not self.timer.isActive()):
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self._check_n_restore)
            self.timer.start(self.timeout)

    def install(self):
        """Install event to current view"""
        self.view.installEventFilter(self)
        self.control = QtWidgets.QPushButton(self.view)
        self.control.setText('Exit!')
        self.control.move(10, 10)
        self.control.released.connect(self.uninstall)
        self.control.show()

    def uninstall(self):
        """Uninstall tracker from current view"""
        self.view.removeEventFilter(self)
        self.restore_appearance()
        self.control.deleteLater()
        self.deleteLater()
        self.__class__._all.remove(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and event.isAutoRepeat():
            return super(self.__class__, self).eventFilter(obj, event)

        # check if we have Alt button pressed, we dont want to restore appearance
        # if it is
        self.restore_on_release = QtWidgets.QApplication.queryKeyboardModifiers(
        ) != QtCore.Qt.AltModifier

        # if mouse button pressed, set bb
        if (event.type() == QtCore.QEvent.MouseButtonPress
                and QtWidgets.QApplication.queryKeyboardModifiers() ==
                QtCore.Qt.AltModifier):
            self.set_bb_appearance()

        if event.type() == QtCore.QEvent.MouseButtonRelease:
            # do we have Alt pressed?
            if self.restore_on_release:
                self.restore_appearance()
            else:
                # start timer which would check, in case there is a delay
                # in Alt button release
                self.start_timer()

        # pass event to parent widget
        return super(self.__class__, self).eventFilter(obj, event)
