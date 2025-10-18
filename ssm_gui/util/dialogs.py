import os

from PySide6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton, QColorDialog,
                               QCheckBox, QComboBox)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFontMetrics, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QRect

from ptb.util.io.opendialog import OpenFiles
from ptb.util.io.helper import BasicIO

from ssm_gui.models.shape import ShapeModel
from ssm_gui.defaults.widgets import OpacitySlider


class CustomCheckbox(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.checked_pixmap = QPixmap("./icons/checkbox1.png")  # Replace with your checked image path
        self.unchecked_pixmap = QPixmap("./icons/square1.png")  # Replace with your unchecked image path
        self.indicator_size = 15  # Adjust as needed

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Determine which pixmap to draw
        current_pixmap = self.checked_pixmap if self.isChecked() else self.unchecked_pixmap

        # Calculate position for the indicator
        indicator_rect = QRect(0, (self.height() - self.indicator_size) // 2,
                               self.indicator_size, self.indicator_size)

        # Draw the indicator image
        painter.drawPixmap(indicator_rect, current_pixmap)

        # Draw the text label
        font_metrics = QFontMetrics(self.font())
        text_rect = QRect(self.indicator_size + 5, 0,
                          self.width() - self.indicator_size - 5, self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())

class Preference(QWidget):

    def update_connections(self):
        self.view = self.root.qw
        self.ssm = self.root.ssm_panel
        self.mesh_name.setText(self.ssm.model.model_name)
        self.old_name = self.ssm.model.model_name
        self.pc_sd_text_box.setCurrentIndex(1)
        self.update()

    def reset(self):
        self.view = self.root.qw
        self.ssm = self.root.ssm_panel
        self.mesh_name.setText(self.old_name)
        self.mean_color = [242, 238, 220]
        self.current_colour = [242, 238, 220]
        self.color_button.setStyleSheet(Preference.button_background(self.mean_color))
        self.color_button_current.setStyleSheet(Preference.button_background(self.current_colour))

        self.opacity_mean.set_initial_value(1)
        self.opacity_current.set_initial_value(1)
        self.pc_sd_text_box.setCurrentIndex(1)
        self.show_mesh.setChecked(False)

        try:
            actor = self.view.world.actors["static_mean"]
            actor.GetProperty().SetColor(242 / 255.0, 238 / 255.0, 220 / 255.0)
            self.view.world.update_view()
        except KeyError:
            pass

        try:
            actor = self.view.world.actors[self.ssm.model.model_name]
            actor.GetProperty().SetColor(242 / 255.0, 238 / 255.0, 220 / 255.0)

            self.view.world.update_view()
        except KeyError:
            pass
        self.update()

    @staticmethod
    def button_background(color):
        def rgb_to_hex(r, g, b):
            """
            Converts RGB color values (0-255) to a hexadecimal color string.
            """
            return f'#{r:02x}{g:02x}{b:02x}'
        rgb = rgb_to_hex(color[0], color[1], color[2])
        ret = "QPushButton {"
        ret += "background-color: {0}; /* sets background of the menu */ \n".format(rgb)
        ret += "border: 0px;\n"
        ret += "border-width: 0px;\n"
        ret += "border-style: Transparent;\n"
        ret += "border-color: {0};\n".format(rgb_to_hex(color[0], color[1], color[2]))
        ret += "color: \"#dbdbd9\";\n"
        ret += "padding: 5px;\n"
        ret += "border-radius: 8px;\n "
        ret += "min-height: 0.86em;\n"
        ret += "font: bold 16px;}\n\n"
        ret += "QPushButton:hover { /* when user selects item using mouse or keyboard */\n"
        ret += "background-color: \"#dbdbd9\";\n"
        ret += "color: \"#3B3838\";\n"
        ret += "}"
        return ret


    def __init__(self, root):
        super().__init__()
        self.root = root
        self.view = self.root.qw
        self.ssm = self.root.ssm_panel
        self.old_name = self.ssm.model.model_name
        layout = QVBoxLayout()
        self.setFixedWidth(450)
        self.setFixedHeight(500)
        self.setWindowTitle("Preferences")
        self.setStyleSheet(BasicIO.read_as_block("./defaults/dialog.qss"))
        self.mean_color = [242, 238, 220]


        self.mean_mesh_label = QLabel("Mean Mesh")
        self.color_indicater_mean = QLabel("Mean Mesh")
        self.color_indicater_mean.setPixmap(self.draw_rounded_square())

        self.mesh_name = QLineEdit("Mesh Name")
        self.mesh_name.setObjectName('text_box')
        self.mesh_name.setText(self.ssm.model.model_name)
        self.color_button = QPushButton('', self)
        self.color_button.setStyleSheet(Preference.button_background(self.mean_color))
        self.color_button.setIcon(QIcon("icons/palette.png"))
        self.color_button.clicked.connect(self.choose_color)

        line1 = QWidget()
        hv = QHBoxLayout()
        # hv.addWidget(self.color_indicater_mean)
        hv.addWidget(self.mesh_name)
        hv.addWidget(self.color_button)
        line1.setLayout(hv)

        self.show_mesh = CustomCheckbox("Show Mean Mesh", self)
        self.show_mesh.setChecked(False)  # Initial state: unchecked
        self.show_mesh.stateChanged.connect(self.on_checkbox_state_changed)

        self.opacity_mean = OpacitySlider(self, 'Opacity Mean Mesh', self.update_mean_mesh_opacity)
        self.opacity_mean.set_initial_value(1)
        line2 = QWidget()
        hv = QHBoxLayout()
        hv.addWidget(self.opacity_mean)
        hv.addWidget(self.show_mesh)
        line2.setLayout(hv)

        self.ssm_mesh_label = QLabel("Current Mesh")
        self.current_colour = [242, 238, 220]

        line3 = QWidget()
        hv = QHBoxLayout()
        self.color_indicater_current = QLabel("Current Mesh")
        self.color_indicater_current.setPixmap(self.draw_rounded_square())
        self.opacity_current = OpacitySlider(self, 'Opacity Current Mesh', self.update_current_mesh_opacity)
        self.opacity_current.set_initial_value(1)
        self.color_button_current = QPushButton('', self)
        self.color_button_current.setIcon(QIcon("icons/palette.png"))
        self.color_button_current.setStyleSheet(Preference.button_background(self.current_colour))
        self.color_button_current.clicked.connect(self.choose_color_current)

        # hv.addWidget(self.color_indicater_current)
        hv.addWidget(self.opacity_current)
        hv.addWidget(self.color_button_current)
        line3.setLayout(hv)

        self.pc_setting = QLabel("Principal Components Setting")
        line5 = QWidget()
        hv = QHBoxLayout()
        self.pc_sd_label = QLabel("Maximum Standard Deviation:")
        self.pc_sd_text_box = QComboBox()

        # Add items to the QComboBox
        self.pc_sd_text_box.addItem("1.0")
        self.pc_sd_text_box.addItem("2.0")
        self.pc_sd_text_box.addItem("3.0")
        self.pc_sd_text_box.setCurrentIndex(1)
        self.pc_sd_text_box.currentIndexChanged.connect(self.pc_sd_changed)
        hv.addWidget(self.pc_sd_label)
        hv.addSpacing(5)
        hv.addWidget(self.pc_sd_text_box)
        hv.addStretch(5)
        line5.setLayout(hv)

        line6 = QWidget()
        hv = QHBoxLayout()
        self.reset_button = QPushButton('Reset', self)
        self.reset_button.clicked.connect(self.reset)
        hv.addWidget(self.reset_button)
        hv.addStretch()
        line6.setLayout(hv)

        layout.addWidget(self.mean_mesh_label)
        layout.addWidget(line1)
        layout.addWidget(line2)
        layout.addWidget(self.ssm_mesh_label)
        layout.addWidget(line3)
        layout.addWidget(self.pc_setting)
        layout.addWidget(line5)
        layout.addStretch(5)
        layout.addWidget(line6)
        self.setLayout(layout)

    def pc_sd_changed(self):
        selected = self.pc_sd_text_box.currentText()
        sd = float(selected)
        self.root.ssm_panel.update_pc_sd_range(sd)
        pass

    def on_checkbox_state_changed(self):
        try:
            b = self.show_mesh.isChecked()
            actor = self.view.world.actors["static_mean"]
            actor.SetVisibility(b)
            self.view.world.update_view()
        except KeyError:
            pass

    def choose_color(self):
        cl = QColorDialog()
        color = cl.getColor()
        if color.isValid():
            colour = color.getRgb()
            r = colour[0]
            g = colour[1]
            b = colour[2]
            self.mean_color=[r, g, b]
            try:
                actor = self.view.world.actors["static_mean"]
                actor.GetProperty().SetColor(r / 255.0, g / 255.0, b / 255.0)
                self.view.world.update_view()
            except KeyError:
                pass
            self.color_button.setStyleSheet(Preference.button_background(self.mean_color))
            self.color_indicater_mean.setPixmap(self.draw_rounded_square(self.mean_color))


    def update_current_mesh_opacity(self, i):
        try:
            actor = self.view.world.actors[self.ssm.model.model_name]
            actor.GetProperty().SetOpacity(i)
            self.view.world.update_view()
        except KeyError:
            pass

    def update_mean_mesh_opacity(self, i):
        try:
            actor = self.view.world.actors["static_mean"]
            actor.GetProperty().SetOpacity(i)
            self.view.world.update_view()
        except KeyError:
            pass

    def choose_color_current(self):
        cl = QColorDialog()
        color = cl.getColor()
        if color.isValid():
            colour = color.getRgb()
            r = colour[0]
            g = colour[1]
            b = colour[2]
            self.current_colour=[r, g, b]
            try:
                actor = self.view.world.actors[self.ssm.model.model_name]
                actor.GetProperty().SetColor(r / 255.0, g / 255.0, b / 255.0)

                self.view.world.update_view()
            except KeyError:
                pass
            self.color_button_current.setStyleSheet(Preference.button_background(self.current_colour))
            self.color_indicater_current.setPixmap(self.draw_rounded_square(self.current_colour))

    def draw_rounded_square(self, color=None):
        # Define the size of the pixmap and the rounded square
        pixmap_size = 24
        square_size = 20
        corner_radius = 3  # Adjust for more or less rounded corners

        # Create a transparent pixmap
        pixmap = QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(QColor(Qt.GlobalColor.transparent))

        # Create a QPainter to draw on the pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # For smoother edges

        # Set the brush (fill color) and pen (border) for the square
        if color is None:
            c = QColor(self.mean_color[0], self.mean_color[1], self.mean_color[2])
        else:
            c = QColor(color[0], color[1], color[2])
        painter.setBrush(QBrush(c))
        painter.setPen(QPen(c, 2))  # Blue border with thickness 2

        # Calculate the position to center the square
        x = (pixmap_size - square_size) // 2
        y = (pixmap_size - square_size) // 2

        # Draw the rounded rectangle (square)
        painter.drawRoundedRect(QRect(x, y, square_size, square_size), corner_radius, corner_radius)

        # End the painter
        painter.end()

        return pixmap


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
                    self.root.root.par.qw.clear_view()
                    self.root.shape_model = ShapeModel(self.current_pc_file)
                    self.root.geo = self.current_mean_file
                    self.root.update_model_connector()
                    self.root.root.par.ssm_panel.reset_number_pc(self.root.shape_model.weights.shape[0])



        self.close()