import os

import numpy as np
import vtk
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QHBoxLayout,
                               QVBoxLayout, QProgressBar, QColorDialog, QSlider, QScrollArea, QMessageBox)
from ptb.util.io.opendialog import OpenFiles
from ptb.util.lang import CommonSymbols
from ptb.util.io.helper import BasicIO
from ptb.util.data import VTKMeshUtl


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
        self.root.root.world.reset_zoom(on_load=True)
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

class OpacitySlider(QWidget):
    def __init__(self, root, label, listener):
        super().__init__()
        self.root = root
        self.listener = listener
        self.setObjectName("PCSlider")
        self.label = label
        self.the_label = QLabel('{0}: '.format(label))
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.update_text_box)
        self.text_box = QLineEdit('0.0')
        self.text_box.setFixedWidth(40)
        self.hor = QHBoxLayout()
        self.hor.addWidget(self.the_label)
        self.hor.addWidget(self.slider)
        self.hor.addWidget(self.text_box)
        self.setFixedHeight(35)
        self.setLayout(self.hor)

    def set_initial_value(self, i):
        if i > 1:
            return
        self.slider.setValue(i*100)

    def update_text_box(self):
        print(self.slider.value())
        sdx = self.slider.value()/100
        self.text_box.setText("{0:0.2f}".format(sdx))
        self.listener(sdx)

    def reset(self):
        self.text_box.setText("{0:0.2f}".format(0))
        self.slider.setValue(0)


class PCSlider(QWidget):
    def __init__(self, root, label):
        super().__init__()
        self.root = root
        self.setObjectName("PCSlider")
        self.label = label
        self.the_label = QLabel('{0}: '.format(label))
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(-200, 200)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.update_text_box)
        self.text_box = QLineEdit('0.0')
        self.text_box.setFixedWidth(40)
        self.hor = QHBoxLayout()
        self.hor.addWidget(self.the_label)
        self.hor.addWidget(self.slider)
        self.hor.addWidget(self.text_box)
        self.setFixedHeight(50)
        self.setFixedWidth(280)
        self.setLayout(self.hor)

    def update_text_box(self):
        print(self.slider.value())
        sdx = self.slider.value()/100.0
        self.text_box.setText("{0:0.2f}".format(sdx))
        self.root.update_pcs(self.label, sdx)

    def update_range(self, i):
        self.slider.setRange(-i*100, i*100)

    def reset(self):
        self.text_box.setText("{0:0.2f}".format(0))
        self.slider.setValue(0)

class SSMInfoWidget(QWidget):

    def __init__(self, parent, ssm):
        super().__init__(parent)
        self.setStyleSheet(BasicIO.read_as_block("./defaults/ssminfo.qss"))
        self.root = parent
        self.model = ssm
        self.number_pc = 9
        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(QLabel("Principal components (SD)"))
        self.vlayout.addSpacing(5)
        self.vlayout_scroll = QVBoxLayout()
        self.pc_control = {}
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedWidth(300)
        self.scroll.setMinimumHeight(550)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.box = QWidget()
        self.box.setObjectName('box')
        self.box.setFixedWidth(300)
        for i in range(0, self.number_pc):
            pc_label = 'PC {0}'.format(i+1)
            self.pc_control[pc_label] = PCSlider(self, pc_label)
            self.vlayout_scroll.addWidget(self.pc_control[pc_label])
        self.vlayout_scroll.addStretch(5)
        self.box.setLayout(self.vlayout_scroll)
        self.scroll.setWidget(self.box)

        self.vlayout.addWidget(self.scroll)
        #self.vlayout.addStretch(5)
        self.export_button = QPushButton("Export")
        self.export_button.setFixedHeight(35)
        self.export_button.clicked.connect(self.export)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedHeight(35)
        self.reset_button.clicked.connect(self.reset)
        self.vlayout.addWidget(self.export_button)
        self.vlayout.addWidget(self.reset_button)
        self.setLayout(self.vlayout)
        self.setFixedWidth(320)
        self.sd = [0 for i in range(0, self.number_pc)]


    def as_inp(self, model_name, data):
        ret = "*Heading\n"
        ret += "** Job name: {0}\n".format(model_name)
        ret += "** Generated by: {0}\n".format('gias3_ssm_viewer')
        ret += "*Part, name = {0}\n".format(model_name)

        ret += "*Node\n"
        spaces = '  '
        for i in range(0, len(str(data.GetNumberOfPoints()))):
            spaces += ' '
        for i in range(0, data.GetNumberOfPoints()):
            point = data.GetPoint(i)
            ret += "{4}{0}, {1}, {2}, {3}\n".format(i + 1, point[0], point[1], point[2], spaces)

        ret += "*Element, type=S3\n"
        spaces = ' '
        for i in range(0, len(str(data.GetNumberOfCells()))):
            spaces += ' '
        for i in range(0, data.GetNumberOfCells()):
            cell = data.GetCell(i)
            cell_type = cell.GetCellType()
            if cell_type == vtk.VTK_TRIANGLE:
                ret += "{4}{0}, {1}, {2}, {3}\n".format(i + 1,
                                                       cell.GetPointId(0) + 1,
                                                       cell.GetPointId(1) + 1,
                                                       cell.GetPointId(2) + 1,
                                                       spaces)
        return ret

    def export(self):
        op = OpenFiles()
        save = op.get_save_file(file_filter=("ply (*.ply);;stl (*.stl);;obj (*.obj);;FEBio/ Abaqus (*.inp);;All Files (*.*)"))
        filt = op.selectedNameFilter()
        boo = False
        try:
            if os.path.exists(save):
                k = QMessageBox.warning(self,
                                        "Export: File exists!",
                                        "Do you wish to override existing file?",
                                        buttons=QMessageBox.StandardButton.Yes| QMessageBox.StandardButton.No)
                if k == QMessageBox.StandardButton.Yes:
                    print("Yes! override")
                else:
                    print("No! return")
                    return
        except TypeError:
            return
        def standard_surface_mesh():
            try:
                k = self.model.qw.world.actors[self.model.model_name]
                VTKMeshUtl.write(save, k.GetMapper().GetInput())
                pass
            except KeyError:
                print("Unknown model")
                pass
            return True

        def surface_inp_file():
            try:
                k = self.model.qw.world.actors[self.model.model_name]
                poly = k.GetMapper().GetInput()
                ret_file = self.as_inp(self.model.model_name, poly)
                with open(save, "w") as s:
                    s.write(ret_file)
                return True

            except KeyError:
                print("Unknown model")
                pass
        if 'ply' in filt:
            if not save.endswith('.ply'):
                save += '.ply'
            boo = standard_surface_mesh()
        elif 'stl' in filt:
            if not save.endswith('.stl'):
                save += '.stl'
            boo = standard_surface_mesh()
        elif 'obj' in filt:
            if not save.endswith('.obj'):
                save += '.obj'
            boo = standard_surface_mesh()
        elif 'inp' in filt:
            if not save.endswith('.inp'):
                save += '.inp'
            boo = surface_inp_file()
        else:
            print("Unknown file format")

        if boo:
            QMessageBox.information(self, "Export", "Export {1} as {0} done!".format(filt, self.model.model_name))
        else:
            QMessageBox.critical(self, "Export", "Export {1} as {0} Failed!".format(filt, self.model.model_name))

        pass

    def reset_number_pc(self, n):
        print("Number of PCs")
        print(n)

        pl = [p for p in self.pc_control]
        for p in pl:
            w = self.pc_control.pop(p)
            w.deleteLater()
            self.vlayout_scroll.removeWidget(w)
        self.number_pc = n
        self.sd = [0 for i in range(0, self.number_pc)]
        idx = 0
        for i in range(0, self.number_pc):
            pc_label = 'PC {0}'.format(i+1)
            self.pc_control[pc_label] = PCSlider(self, pc_label)
            self.vlayout_scroll.insertWidget(idx, self.pc_control[pc_label])
            idx += 1
        self.box.update()
        self.update()

    def update_pc_sd_range(self, i):
        for pc_label in self.pc_control:
            self.pc_control[pc_label].update_range(i)

    def reset(self):
        print("Reset")
        try:
            self.sd = [0 for i in range(0, self.model.shape_model.weights.shape[0])]
            m = self.model.shape_model.reconstruct_diff_all(self.sd, True)
            self.model.update_actor(m)
        except AttributeError:
            pass
        pass
        for pc_label in self.pc_control:
            self.pc_control[pc_label].reset()


    def update_pcs(self, pc_label, sdx):
        # print("update pc")
        idx = int(pc_label.split(' ')[1])-1
        self.sd[idx] = sdx
        print(self.sd)
        try:
            m = self.model.shape_model.reconstruct_diff_all(self.sd, True)
            self.model.update_actor(m)
        except AttributeError:
            pass
        pass


class CameraWidget(QWidget):

    def __init__(self, parent, view):
        super().__init__(parent)
        self.view = view
        self.setStyleSheet(BasicIO.read_as_block("./defaults/world_control.qss"))
        self.root = parent
        self.vlayout = QVBoxLayout()
        labe = QWidget()
        hv = QHBoxLayout()
        pixmap = QPixmap('./icons/globe-alt.png')
        scaled_pixmap = pixmap.scaled(
            35, 35, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        label = QLabel()
        label.setPixmap(scaled_pixmap)
        hv.addWidget(label)
        labe.setLayout(hv)
        self.x = QPushButton('X')
        self.x.setObjectName('x_button')
        self.x.clicked.connect(self.on_x_clicked)
        self.y = QPushButton('Y')
        self.y.setObjectName('y_button')
        self.y.clicked.connect(self.on_y_clicked)
        self.z = QPushButton('Z')
        self.z.setObjectName('z_button')
        self.z.clicked.connect(self.on_z_clicked)

        self.x_neg = QPushButton('-X')
        self.x_neg.setObjectName('x_button')
        self.x_neg.clicked.connect(self.on_x_neg_clicked)

        self.y_neg = QPushButton('-Y')
        self.y_neg.setObjectName('y_button')
        self.y_neg.clicked.connect(self.on_y_neg_clicked)

        self.z_neg = QPushButton('-Z')
        self.z_neg.setObjectName('z_button')
        self.z_neg.clicked.connect(self.on_z_neg_clicked)

        self.snap_button = QPushButton('', self)
        self.snap_button.setIcon(QIcon("./icons/camera.png"))
        self.snap_button.setToolTip("Take a snapshot of the current view.")
        self.snap_button.clicked.connect(self.snapshot)

        self.vlayout.addWidget(labe)
        self.vlayout.addSpacing(5)
        self.vlayout.addWidget(self.x)
        self.vlayout.addWidget(self.y)
        self.vlayout.addWidget(self.z)
        self.vlayout.addSpacing(15)
        self.vlayout.addWidget(self.x_neg)
        self.vlayout.addWidget(self.y_neg)
        self.vlayout.addWidget(self.z_neg)
        self.vlayout.addSpacing(15)
        self.vlayout.addWidget(self.snap_button)
        self.vlayout.addStretch(10)
        self.setLayout(self.vlayout)

    def on_x_clicked(self):
        self.view.world.to_x_view()

    def on_x_neg_clicked(self):
        self.view.world.to_x_view(-1)

    def on_y_clicked(self):
        self.view.world.to_y_view()

    def on_y_neg_clicked(self):
        self.view.world.to_y_view(-1)

    def on_z_clicked(self):
        self.view.world.to_z_view()

    def on_z_neg_clicked(self):
        self.view.world.to_z_view(-1)

    def snapshot(self):
        w2if = vtk.vtkWindowToImageFilter()
        w2if.SetInput(self.view.world.vtk_widget.GetRenderWindow())
        w2if.SetInputBufferTypeToRGB()
        w2if.ReadFrontBufferOff()
        w2if.SetScale(2, 2)
        w2if.Update()

        op = OpenFiles()

        save = op.get_save_file(file_filter=("snapshot (*.png);;All Files (*.*)"))
        if save is not None:
            if not save.endswith('.png'):
                save = save + '.png'

            writer = vtk.vtkPNGWriter()
            writer.SetFileName(save)
            writer.SetInputConnection(w2if.GetOutputPort())
            writer.Write()
        w2if.SetScale(1, 1)
        w2if.Update()
        #self.view.world.update_view()