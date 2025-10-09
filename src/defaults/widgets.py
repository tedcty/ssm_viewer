import os

import numpy as np
import vtk
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QHBoxLayout,
                               QVBoxLayout, QProgressBar, QColorDialog, QSlider)
from ptb.util.io.opendialog import OpenFiles
from PySide6.QtCore import QPoint, Qt
from ptb.util.lang import CommonSymbols
from ptb.util.data import VTKMeshUtl
import pandas as pd


class InfoWidget(QWidget):
    def __init__(self, root, label_name="Landmarks", actors=None):
        super().__init__()
        self.root = root
        self.checker = QCheckBox()
        self.checker.setObjectName("check_box")
        self.checker.setChecked(True)
        self.the_label = QLabel(label_name)
        self.hor = QHBoxLayout()
        self.hor.addWidget(self.checker)
        self.hor.addWidget(self.the_label)
        self.hor.addStretch(5)
        self.setLayout(self.hor)
        self.actor_group = actors
        if actors is None:
            self.actor_group = []

        def checker_vis():
            if len(self.actor_group) > 0:
                if self.checker.isChecked():
                    for a in self.actor_group:
                        a.VisibilityOn()
                else:
                    for a in self.actor_group:
                        a.VisibilityOff()
                self.refresh()

        self.checker.stateChanged.connect(checker_vis)

    def refresh(self):
        self.root.world.vtk_widget.update()


class AngleInfoWidget(QWidget):
    @property
    def model(self):
        return self.root.listener.current_model

    def __init__(self, root, angle_func, label = 'default', max_angle=150):
        super().__init__()
        vl = QVBoxLayout()
        self.root = root
        vl.addWidget(QLabel(" {0}".format(label)))
        hl = QHBoxLayout()
        self.ml = QSlider(Qt.Horizontal)
        self.ml.setObjectName("mesh_q2")
        self.ml.setMinimum(0)
        self.ml.setMaximum(max_angle)
        self.ml.valueChanged.connect(self.valuechange)
        self.ml_button = QLabel('0' + CommonSymbols.Degrees.value[0])
        self.ml_button.setObjectName('ml_angle0')
        self.angle_func = angle_func
        hl.addWidget(self.ml)
        hl.addWidget(self.ml_button)
        k = QWidget()
        k.setLayout(hl)
        vl.addWidget(k)
        self.setLayout(vl)

    def valuechange(self):
        print(self.ml.value())
        self.ml_button.setText('{0}{1}'.format(self.ml.value(), CommonSymbols.Degrees.value[0]))
        vp = np.deg2rad(float(self.ml.value()))
        print(vp)
        self.angle_func(vp)

    def set_angle(self, a0):
        try:
            ad = a0*(180/np.pi)
        except TypeError:
            return
        self.ml_button.setText('{0}{1}'.format(ad, CommonSymbols.Degrees.value[0]))
        if np.isnan(ad):
            return
        else:
            try:
                self.ml.setValue(int(np.round(ad,0)))
            except OverflowError:
                pass
            except TypeError:
                pass


class MeshInfoWidget(QWidget):
    def __init__(self, root, mesh_path="mesh_path", actor_name="", actor=None, check=True):
        super().__init__()
        self.root = root
        self.the_label = QLabel('New Mesh:')
        self.text_box = QLineEdit(mesh_path)
        self.text_box.setObjectName("text_box")
        self.text_box.resize(50, 30)
        self.text_box.setMinimumHeight(30)
        self.button = QPushButton('', self)
        self.button.setIcon(QIcon("icons/add-document.png"))

        self.delete_button = QPushButton('', self)
        self.delete_button.setIcon(QIcon("icons/trash.png"))

        self.setting_button = QPushButton('', self)
        self.setting_button.setIcon(QIcon("icons/slider.png"))

        self.checker = QCheckBox()
        self.checker.setObjectName("check_box")
        self.checker.setChecked(check)

        self.hor = QHBoxLayout()
        self.hor.addWidget(self.checker)
        self.hor.addSpacing(10)
        self.hor.addWidget(self.text_box)
        self.hor.addWidget(self.button)
        self.hor.addWidget(self.setting_button)
        self.hor.addWidget(self.delete_button)

        self.setLayout(self.hor)
        self.button.clicked.connect(self.on_click)
        self.setting_button.clicked.connect(self.choose_color)
        self.delete_button.clicked.connect(self.delete_mesh)
        self.file_path = ""
        self.actor = actor
        self.actor_name = actor_name

        def checker_vis():
            if self.actor is not None:
                if self.checker.isChecked():
                    self.actor.VisibilityOn()
                else:
                    self.actor.VisibilityOff()
                self.refresh()

        self.checker.stateChanged.connect(checker_vis)

    def reset(self):
        self.delete_actor()
        self.text_box.setText('')
        self.checker.setChecked(False)

    def choose_color(self):
        cl = QColorDialog()
        color = cl.getColor()
        if color.isValid():
            colour = color.getRgb()
            r = colour[0]/256.0
            g = colour[1]/256.0
            b = colour[2]/256.0
            if self.actor is not None:
                self.actor.GetProperty().SetColor(r, g, b)
                self.refresh()

    def load_mesh(self, filename):
        rng = np.random.default_rng()
        c = rng.uniform(0.5, 1.0, 3)
        color = [c[0], c[1], c[2]]
        # color = [1.0, 0.5, 0.5]
        reader = vtk.vtkSTLReader()
        if filename.endswith('.ply'):
            reader = vtk.vtkPLYReader()
        reader.SetFileName(filename)
        reader.Update()
        polydata = reader.GetOutput()
        mapper = vtk.vtkPolyDataMapper()
        if vtk.VTK_MAJOR_VERSION <= 5:
            # mapper.SetInput(reader.GetOutput())
            mapper.SetInput(polydata)
        else:
            mapper.SetInputData(polydata)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(color[0], color[1], color[2])
        elements = filename.split("\\")
        if len(elements) <= 1:
            elements = filename.split("/")

        self.actor_name = elements[-1][:elements[-1].rindex(".")]
        self.the_label.setText(self.actor_name)
        self.root.root.world.add_actor(self.actor_name, self.actor)
        self.root.root.world.reset_view()
        pass

    def refresh(self):
        self.root.world.vtk_widget.update()

    def set_checked(self, c):
        self.checker.setChecked(c)

    def delete_mesh(self):
        self.delete_actor()
        self.refresh()

    def delete_actor(self):
        self.root.world.remove_actor(self.actor_name)

    def on_click(self):
        self.button.setIcon(QIcon("icons/add-document.png"))
        dialog = OpenFiles()
        file_names = dialog.get_file('Mesh (*.stl *.ply);; All File (*.*)')
        if file_names is not None:
            paths = os.path.split(file_names[0])
            print("open", file_names)
            if len(file_names[0]) == 0:
                return
            self.button.setIcon(QIcon("icons/add-document.png"))
            if len(file_names[0]) > 0:
                self.checker.setChecked(True)
            self.text_box.setText(file_names[0])
            if self.actor is not None:
                self.delete_actor()
            self.file_path = file_names[0]
            self.load_mesh(self.file_path)


class ProgressWidget(QWidget):
    def __init__(self, root, step_name):
        super().__init__()
        self.root = root
        self.pbar = QProgressBar(self)
        self.progress = 0
        self.pbar.setValue(self.progress)
        self.resize(300, 100)
        self.step_name = step_name
        self.step_label = QLabel(self.step_name)
        self.hor = QHBoxLayout()
        self.hor.addWidget(self.step_label)
        self.hor.addWidget(self.pbar)
        self.setLayout(self.hor)


class PCSlider(QWidget):
    def __init__(self, label):
        super().__init__()
        self.label = label
        self.the_label = QLabel('{0}: '.format(label))
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(-100, 100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.update_text_box)
        self.text_box = QLineEdit('0.0')
        self.text_box.setFixedWidth(40)
        self.hor = QHBoxLayout()
        self.hor.addWidget(self.the_label)
        self.hor.addWidget(self.slider)
        self.hor.addWidget(self.text_box)
        self.setLayout(self.hor)

    def update_text_box(self):
        print(self.slider.value())
        self.text_box.setText("{0:0.2f}".format(self.slider.value()/50.0))


class SSMInfoWidget(QWidget):

    def __init__(self, parent, ssm):
        super().__init__(parent)
        self.root = parent
        self.shape_model = ssm
        self.number_pc = 9
        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(QLabel("Principal components (SD)"))
        self.vlayout.addSpacing(5)
        self.pc_control = {}
        for i in range(0, self.number_pc):
            pc_label = 'PC {0}'.format(i+1)
            self.pc_control[pc_label] = PCSlider(pc_label)
            self.vlayout.addWidget(self.pc_control[pc_label])
        self.vlayout.addStretch(5)
        self.setLayout(self.vlayout)
        self.setFixedWidth(320)

    def update_pcs(self):
        pass
