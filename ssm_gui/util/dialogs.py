import os

from PySide6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton)
from PySide6.QtGui import QIcon
from ptb.util.io.opendialog import OpenFiles
from ptb.util.io.helper import BasicIO
from ssm_gui.models.shape import ShapeModel



class Preference(QWidget):

    def __init__(self, root):
        super().__init__()
        self.root = root
        layout = QVBoxLayout()
        self.setFixedWidth(500)
        self.setFixedHeight(600)
        self.setWindowTitle("Preferences")
        self.setStyleSheet(BasicIO.read_as_block("./defaults/dialog.qss"))


class NewSSM(QWidget):

    def __init__(self, root):
        super().__init__()
        self.root = root
        layout = QVBoxLayout()
        self.setFixedWidth(500)
        self.setWindowTitle("New SSM Config")
        self.setStyleSheet(BasicIO.read_as_block("./defaults/dialog.qss"))

        self.pc_widget = QWidget()
        pc_lay = QHBoxLayout()
        self.pc_file = QLabel("PC File (*.npz or *.pc): ")
        self.pc_path = QLineEdit("PC File Path")
        self.pc_path.setObjectName('text_box')
        self.pc_button = QPushButton('', self)
        self.pc_button.setIcon(QIcon("icons/add-document.png"))
        self.pc_button.clicked.connect(self.open_file_pc)

        self.mesh = QWidget()
        mesh_layout = QHBoxLayout()
        self.mean_mesh_label = QLabel("Mean Mesh (support *.ply only): ")
        self.mean_mesh = QLineEdit("Mean Mesh Path")
        self.mean_mesh.setObjectName('text_box')
        self.mean_mesh_button = QPushButton('', self)
        self.mean_mesh_button.setIcon(QIcon("icons/add-document.png"))
        self.mean_mesh_button.clicked.connect(self.open_file_mesh)

        pc_lay.addWidget(self.pc_file)
        pc_lay.addWidget(self.pc_path)
        pc_lay.addSpacing(5)
        pc_lay.addWidget(self.pc_button)
        self.pc_widget.setLayout(pc_lay)

        mesh_layout.addWidget(self.mean_mesh_label)
        mesh_layout.addWidget(self.mean_mesh)
        pc_lay.addSpacing(5)
        mesh_layout.addWidget(self.mean_mesh_button)
        self.mesh.setLayout(mesh_layout)

        self.control = QWidget()
        con_hor = QHBoxLayout()
        con_hor.addStretch(5)
        self.ok_button = QPushButton("OK")
        self.cancel = QPushButton("Cancel")
        con_hor.addWidget(self.ok_button)
        con_hor.addWidget(self.cancel)
        self.control.setLayout(con_hor)
        self.ok_button.clicked.connect(self.on_ok_click)
        self.cancel.clicked.connect(self.on_cancel_click)

        layout.addWidget(self.pc_widget)
        layout.addWidget(self.mesh)
        layout.addStretch(5)
        layout.addWidget(self.control)
        self.setLayout(layout)
        self.current_pc_file = None
        self.current_mean_file = None

    def reset_form(self):
        self.mean_mesh.setText("Mean Mesh Path")
        self.pc_path.setText("PC File Path")

    def on_cancel_click(self):
        self.close()

    def open_file_pc(self):
        op = OpenFiles()
        self.current_pc_file = op.get_file(file_filter=("PC File (*.npz *.pc);;All Files (*.*)"))
        if self.current_pc_file is not None:
            self.pc_path.setText(self.current_pc_file)
        else:
            self.pc_path.setText("PC File Path")

    def open_file_mesh(self):
        op = OpenFiles()
        self.current_mean_file = op.get_file(file_filter=("Mean Mesh (*.ply);;All Files (*.*)"))
        self.mean_mesh.setText(self.current_mean_file)
        if self.current_mean_file is not None:
            self.mean_mesh.setText(self.current_mean_file)
        else:
            self.mean_mesh.setText("Mean Mesh Path")

    def on_ok_click(self):
        print("ok")
        print("Checking")
        if self.current_pc_file is not None and self.current_mean_file is not None:
            if os.path.exists(self.current_pc_file) and os.path.exists(self.current_mean_file):
                if self.root is not None:
                    self.root.shape_model = ShapeModel(self.current_pc_file)
                    self.root.geo = self.current_mean_file
                    self.root.update_model_connector()
                    self.root.root.par.ssm_panel.reset_number_pc(self.root.shape_model.weights.shape[0])



        self.close()