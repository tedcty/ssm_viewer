import sys
import os
from typing import Optional

import time

from threading import Thread
from defaults.viewer import WorldView

from ptb.util.io.helper import BasicIO
from ptb.util.io.opendialog import OpenFiles

from PySide6.QtWidgets import (QMainWindow, QApplication, QMenuBar, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox)
from PySide6.QtGui import QIcon, QColor
from PySide6.QtCore import QSize, Qt


class MainWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.par = parent
        self.layout = QVBoxLayout()
        self.config = PCASSM()
        self.menu_bar = MainMenuBar(parent=self, custom_view=self.config)

        # self.menu_bar.add_open_action(self.config.load)
        self.setStyleSheet(self.menu_bar.sty)
        self.layout.setMenuBar(self.menu_bar)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#ededeb"))
        self.setPalette(p)
        self.no_3d = [0, 0]
        self.with_3d = [100, 100]

    def setno_3dwidth(self):
        self.par.width = self.no_3d[0]
        self.par.height = self.no_3d[1]
        self.par.resize(QSize(self.no_3d[0], self.no_3d[1]))

    def setwith_3dwidth(self):
        self.par.width = self.with_3d[0]
        self.par.height = self.with_3d[1]
        self.par.resize(QSize(self.with_3d[0], self.with_3d[1]))

    def set_view(self, view):
        self.menu_bar.set_view(view)
        self.config.world = view
        pass

    def add(self, widget):
        self.layout.addWidget(widget)

    def set_save_action(self, handle):
        self.menu_bar.add_save_action(handle)

    def set_open_action(self, handle):
        self.menu_bar.add_open_action(handle)

class CustomConfig:
    def __init__(self, parent_widget=None, viewer=None):
        self.parent_widget = parent_widget
        self.config = {}
        self.world_viewer = viewer

    def load(self):
        print("Open")
        pass

    def new_project(self):
        print("New")
        pass

    def save(self):
        print("Save")
        pass

    def on_exit(self):
        print("exit")
        _msg = "Are you sure you want to exit the app?"
        reply = QMessageBox.question(self.parent_widget, 'Question', _msg)
        if reply == QMessageBox.StandardButton.Yes:
            sys.exit(0)
        pass

    def help(self):
        print("Help")


class Articulate(CustomConfig):
    def __init__(self, viewer=None):
        super().__init__(viewer)


class PCASSM(CustomConfig):
    def __init__(self, viewer=None):
        super().__init__(viewer)
        print(PCASSM)

    def load(self):
        print("Open")
        op = OpenFiles(title="Open Gias3 Shape Model Directory")
        c = op.get_dir()
        print(c)
        if c is not None:
            self.new_project()
            print("Note Shape model mesh must end with {*}mesh.ply")
            mean_mesh = [f for f in os.listdir(c) if f.endswith('mean.ply')]
            pcs = [f for f in os.listdir(c) if f.endswith('.pc.npz')]
            print(mean_mesh[0])
            self.world_viewer.add_mesh("{0}/{1}".format(c, mean_mesh[0]))

        pass

    def new_project(self):
        print("New")
        self.world_viewer.clear_view()
        self.world_viewer.add_global_axis()
        self.world_viewer.reset_view()
        pass


class MainMenuBar(QMenuBar):
    debug = False

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        print("MainMenuBar")
        self.par.par.qw.on_focus()

    def __init__(self, parent=None, view=None, default_menus=True, splash=None, custom_view=None):
        super().__init__(parent)
        self.config_me = custom_view
        if self.config_me is None:
            self.config_me = CustomConfig(view)
        self.par: Optional[MainWidget, None] = parent
        self.view = view
        self.save_action = None
        self.open_file = None
        self.splash = splash

        self.view3d = False
        if default_menus:
            self.default_menus()

        self.sty = BasicIO.read_as_block("./defaults/menu.qss")

    def set_view(self, view):
        self.view = view
        self.config_me.world_viewer = self.view

    def add_save_action(self, save):
        self.save_action.triggered.connect(save)

    def add_open_action(self, open_func):
        self.open_file.triggered.connect(open_func)

    def default_menus(self):
        action_file = self.addMenu("File")
        new_file = action_file.addAction("New")
        new_file.setIcon(QIcon('./icons/add-document.png'))
        new_file.triggered.connect(self.config_me.new_project)
        self.open_file = action_file.addAction("Open")
        self.open_file.setIcon(QIcon('./icons/folder-open.png'))
        self.open_file.triggered.connect(self.config_me.load)
        self.save_action = action_file.addAction("Save")
        self.save_action.setIcon(QIcon('./icons/diskdark.png'))
        self.save_action.triggered.connect(self.config_me.save)
        action_file.addSeparator()
        quit_action = action_file.addAction("Quit")
        quit_action.setIcon(QIcon('./icons/power.png'))
        quit_action.triggered.connect(self.config_me.on_exit)
        action_edit = self.addMenu("Edit")
        prefer = action_edit.addAction("Preferences")
        prefer.setIcon(QIcon('../MVP_gui2/icons/slider.png'))
        action_view = self.addMenu("View")
        view3 = action_view.addAction("Reset Zoom")
        view3.triggered.connect(self.reset_view)
        action_help = self.addMenu("Help")
        about = action_help.addAction("About")
        about.setIcon(QIcon('./icons/info.png'))
        about.triggered.connect(self.config_me.help)

    def run(self):
        pass

    def reset_view(self):
        self.par.par.qw.reset_view()

    def open_splash(self):
        if self.splash is not None:
            self.splash.show()


class O3dHelperApp(QMainWindow):
    def closeEvent(self, event):
        self.qw.on_close()

    def __init__(self, screen, splash=None):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.title = 'Shape Model Viewer'
        self.splash = splash
        size: QSize = screen.size()
        self.width = int(0.8 * size.width())
        self.height = int(0.8 * size.height())
        self.left = int((size.width()-self.width)/2)
        self.top = int((size.height()-self.height)/2)
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.main_widget = MainWidget(self)
        self.main_widget.no_3d = [self.width, self.height]
        self.main_widget.with_3d = [int(0.8 * size.width()), self.height]
        self.qw = WorldView(self.main_widget, self)

        self.main_widget.add(self.qw)
        self.main_widget.setObjectName('world_qw')

        self.setCentralWidget(self.main_widget)
        self.setStyleSheet(BasicIO.read_as_block("./defaults/main_window.qss"))
        q = Thread(target=self.start_world)
        q.start()


    def start_world(self):
        time.sleep(0.5)
        print("start_world")
        self.main_widget.menu_bar.set_view(self.qw)
        print("start_world")
        self.qw.reset_view()
        print("start_world")
        self.update()

    def resizeEvent(self, event):
        self.qw.resize_ev(self.size())
        print("size")


    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        """
        Drop File locations, stored in files
        :param e:
        :return:
        """
        if e.mimeData().hasUrls:
            e.setDropAction(Qt.DropAction.CopyAction)
            e.accept()
            files = []
            count = 0
            self.qw.clear_view()
            for url in e.mimeData().urls():
                filename = str(url.toLocalFile())
                if filename.endswith(".ply") or filename.endswith(".stl"):
                    self.qw.add_mesh(filename)
                files.append(filename)
                count += 1
                print(filename)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    current_screen = app.primaryScreen()
    ex = O3dHelperApp(current_screen)
    ex.show()
    sys.exit(app.exec())
    pass
