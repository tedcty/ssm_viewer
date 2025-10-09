from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLineEdit,
QPushButton,
)

from PySide6.QtGui import QIcon

from src.defaults.widgets import MeshInfoWidget

class NewSSM(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setFixedWidth(500)
        self.setWindowTitle("New SSM Config")

        self.pc_widget = QWidget()
        pc_lay = QHBoxLayout()
        self.pc_file = QLabel("PC File (*.npz or *.pc): ")
        self.pc_path = QLineEdit("PC File Path")
        self.button0 = QPushButton('', self)
        self.button0.setIcon(QIcon("icons/add-document.png"))

        self.mesh = QWidget()
        mesh_layout = QHBoxLayout()
        self.mean_mesh_laeb = QLabel("Mean Mesh (support *.ply only): ")
        self.mean_mesh = QLineEdit("Mean Mesh Path")
        self.button = QPushButton('', self)
        self.button.setIcon(QIcon("icons/add-document.png"))

        pc_lay.addWidget(self.pc_file)
        pc_lay.addWidget(self.pc_path)
        pc_lay.addSpacing(5)
        pc_lay.addWidget(self.button0)
        self.pc_widget.setLayout(pc_lay)

        mesh_layout.addWidget(self.mean_mesh_laeb)
        mesh_layout.addWidget(self.mean_mesh)
        pc_lay.addSpacing(5)
        mesh_layout.addWidget(self.button)
        self.mesh.setLayout(mesh_layout)

        self.control = QWidget()
        con_hor = QHBoxLayout()
        con_hor.addStretch(5)
        self.ok_button = QPushButton("OK")
        self.cancel = QPushButton("Cancel")
        con_hor.addWidget(self.ok_button)
        con_hor.addWidget(self.cancel)
        self.control.setLayout(con_hor)
        self.cancel.clicked.connect(self.on_cancel_click)

        layout.addWidget(self.pc_widget)
        layout.addWidget(self.mesh)
        layout.addStretch(5)
        layout.addWidget(self.control)
        self.setLayout(layout)

    def reset_form(self):
        self.mean_mesh.setText("Mean Mesh Path")
        self.pc_path.setText("PC File Path")

    def on_cancel_click(self):
        self.close()