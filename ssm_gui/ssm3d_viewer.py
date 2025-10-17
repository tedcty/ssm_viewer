import sys
import os
from typing import Optional
import time

import numpy as np
from PySide6.QtWidgets import (QMainWindow, QApplication, QMenuBar, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox)
from PySide6.QtGui import QIcon, QColor
from PySide6.QtCore import QSize, Qt

from ssm_gui.defaults.viewer import WorldView
from ssm_gui.defaults.widgets import SSMInfoWidget, CameraWidget
from ssm_gui.defaults.tools import BasicIO
from ssm_gui.util.dialogs import NewSSM
from ssm_gui.models.shape import ShapeModel

from ptb.util.io.helper import JSONSUtl
from ptb.util.io.opendialog import OpenFiles
from ptb.util.data import VTKMeshUtl

from threading import Thread


class MainWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.par = parent
        self.layout = QVBoxLayout()
        self.menu_bar = MainMenuBar(parent=self)
        #self.config = CustomConfig(self)
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

    def set_preferences(self, handle):
        self.menu_bar.add_preferences(handle)

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

class SSMConfig(CustomConfig):
    def __init__(self, parent_widget=None, viewer=None, main=None):
        super().__init__(parent_widget, viewer)
        self.new_project_window = None
        self.shape_model = None
        self.geo = None
        self.model_connector:ModelConnector = None
        self.root = main
        self.current_file = None

    def update_model_connector(self):
        self.model_connector.shape_model = self.shape_model
        self.model_connector.mean_mesh_file = self.geo
        self.model_connector.update_world(True)

    def save(self):
        try:
            ret = {'pc': self.new_project_window.current_pc_file,
                   'mean_mesh': self.new_project_window.current_mean_file}
        except AttributeError:
            print("nothing to save")
            return
        op = OpenFiles()

        save = op.get_save_file(file_filter=("SSM (*.ssm);;All Files (*.*)"))
        if save is not None:
            if not save.endswith('.ssm'):
                save = save+'.ssm'
            if os.path.exists(save):
                return
            JSONSUtl.write_json(save, ret)
        pass

    def new_project(self):
        print("New")
        if self.new_project_window is None:
            self.new_project_window = NewSSM(self)
            self.new_project_window.show()
        elif self.new_project_window.isVisible():
            self.new_project_window.activateWindow()
            return
        else:
            self.new_project_window.reset_form()
            self.new_project_window.show()
        pass

    def load(self, in_file=None):
        op = OpenFiles()
        self.current_file = in_file
        if in_file is None or not in_file:
            self.current_file = op.get_file(file_filter=("SSM (*.ssm);;All Files (*.*)"))
        if self.current_file is not None and os.path.exists(self.current_file):
            file_paths = JSONSUtl.load_json(self.current_file)
            if os.path.exists(file_paths['pc']) and os.path.exists(file_paths['mean_mesh']):
                self.root.par.qw.clear_view()
                self.root.par.qw.world.reset_view()
                self.new_project_window = NewSSM(self)
                self.new_project_window.current_pc_file = file_paths['pc']
                self.new_project_window.current_mean_file = file_paths['mean_mesh']
                self.shape_model = ShapeModel(file_paths['pc'])
                self.geo = file_paths['mean_mesh']
                self.update_model_connector()
                self.root.par.ssm_panel.reset_number_pc(self.shape_model.weights.shape[0])
            else:
                if not os.path.exists(file_paths['pc']):
                    print("PC file not found: {0}".format(file_paths['pc']))
                if not os.path.exists(file_paths['mean_mesh']):
                    print("Mean Mesh file not found: {0}".format(file_paths['mean_mesh']))


class ModelConnector:
    def __init__(self, qw):
        self.shape_model: ShapeModel = None
        self.mean_mesh_file = None
        self.qw:WorldView = qw
        self.mean_mesh_actor = None
        self.mean_mesh_poly = None
        self.model_name = None

    def update_world(self, onload = False):
        model_path = os.path.split(self.mean_mesh_file)
        self.model_name = model_path[1][: model_path[1].rindex('.')]
        self.mean_mesh_actor = self.qw.world.add_actor(filename=self.mean_mesh_file)
        self.mean_mesh_poly = self.mean_mesh_actor.GetMapper().GetInput()
        self.qw.refresh_model_name(self.model_name)
        self.qw.reset_zoom(onload)

    def update_actor(self, points):
        self.mean_mesh_poly = VTKMeshUtl.update_poly_w_points(points, self.mean_mesh_poly)
        p = VTKMeshUtl.extract_points(self.mean_mesh_actor)
        self.qw.world.update_view()

class MainMenuBar(QMenuBar):
    debug = False

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        print("MainMenuBar")
        self.par.par.qw.on_focus()

    def set_model_connector(self, model_connector):
        self.config_me.model_connector = model_connector

    def __init__(self, parent=None, view=None, default_menus=True, splash=None):
        super().__init__(parent)
        self.config_me = SSMConfig(view, main=parent)
        self.par: Optional[MainWidget, None] = parent
        self.view = view
        self.save_action = None
        self.open_file = None
        self.splash = splash
        self.new_project = None
        self.preferences = None

        self.view3d = False
        if default_menus:
            self.default_menus()

        self.sty = BasicIO.read_as_block("./defaults/menu.qss")

    def set_view(self, view):
        self.view = view

    def add_save_action(self, save):
        self.save_action.triggered.connect(save)

    def add_open_action(self, open_func):
        self.open_file.triggered.connect(open_func)

    def add_preferences(self, prefer):
        self.preferences.triggered.connect(prefer)
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
        self.preferences = action_edit.addAction("Preferences")
        self.preferences.setIcon(QIcon('./icons/slider.png'))
        action_view = self.addMenu("View")
        view2 = action_view.addAction("Toggle Origin")
        view2.triggered.connect(self.toggle_origin)
        view2.setIcon(QIcon('./icons/model-cube-arrows.png'))

        view3 = action_view.addAction("Reset Zoom")
        view3.triggered.connect(self.reset_view)
        view3.setIcon(QIcon('./icons/zoom_reset.png'))

        view4 = action_view.addAction("Reset Orientation")
        view4.triggered.connect(self.reset_view_orientation)
        view4.setIcon(QIcon('./icons/refresh.png'))

        action_help = self.addMenu("Help")
        about = action_help.addAction("About")
        about.setIcon(QIcon('./icons/info.png'))
        about.triggered.connect(self.config_me.help)

    def run(self):
        pass

    def reset_view(self):
        self.par.par.qw.reset_zoom()

    def reset_view_orientation(self):
        self.par.par.qw.reset_view_orientation()

    def toggle_origin(self):
        v = self.par.par.qw.world.actors['Origin'].GetVisibility()
        self.par.par.qw.world.actors['Origin'].SetVisibility(not v)
        self.par.par.qw.world.update_view()
        pass

    def open_splash(self):
        if self.splash is not None:
            self.splash.show()


class O3dHelperApp(QMainWindow):
    def closeEvent(self, event):
        self.qw.on_close()

    def __init__(self, screen, splash=None):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.title = 'SSM Viewer'
        self.splash = splash
        size: QSize = screen.size()
        self.width = int(np.round(0.8 * size.width(), 0))
        self.height = int(np.round(0.8 * size.height(), 0))
        self.left = int(np.round((size.width()-self.width)/2.0, 0))
        self.top = int(np.round((size.height()-self.height)/2.0, 0))
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon('./icons/vector-alt.png'))
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.main_widget = MainWidget(self)
        self.main_widget.no_3d = [self.width, self.height]
        self.main_widget.with_3d = [int(np.round(0.8 * size.width(), 0)), self.height]
        self.qw = WorldView(self.main_widget, self)
        self.model_connector = ModelConnector(self.qw)
        self.main_widget.menu_bar.set_model_connector(self.model_connector)
        self.ssm_panel = SSMInfoWidget(self, self.model_connector)
        self.camera_widget = CameraWidget(self, self.qw)

        q = QWidget()
        l = QHBoxLayout()
        l.addWidget(self.qw)
        l.addWidget(self.camera_widget)
        l.addWidget(self.ssm_panel)
        q.setLayout(l)

        self.main_widget.add(q)
        self.main_widget.setObjectName('world_qw')

        self.setCentralWidget(self.main_widget)
        self.setStyleSheet(BasicIO.read_as_block("./defaults/main_window.qss"))
        q = Thread(target=self.start_world)
        q.start()


    def start_world(self):
        time.sleep(0.5)
        print("Connect menubar to view")
        self.main_widget.menu_bar.set_view(self.qw)
        print("Reset Camera View")
        self.qw.reset_zoom()
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

