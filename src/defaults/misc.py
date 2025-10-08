from PySide6.QtWidgets import (QFileDialog, QComboBox)


class OpenFiles(QFileDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open Files")
        options = QFileDialog.Options()
        options |= QFileDialog.Option.DontUseNativeDialog
        self.setOption(options)
        comb0 = self.findChild(QComboBox, "lookInCombo")
        comb0.setEditable(True)
        line0 = comb0.lineEdit()
        line0.returnPressed.connect(lambda:
                                    self.setDirectory(line0.text()))

    def get_files(self, file_filter='Text (*.txt)'):
        self.setNameFilter(file_filter)
        self.setFileMode(QFileDialog.FileMode.ExistingFiles)
        return self.__open__up__()

    def __open__up__(self):
        if self.exec():
            file_names = self.selectedFiles()
            self.close()
            return file_names
        return None

    def get_file(self, file_filter='Text (*.txt)'):
        self.setNameFilter(file_filter)
        self.setFileMode(QFileDialog.FileMode.ExistingFile)
        ret = self.__open__up__()
        if ret is not None:
            return ret[0]
        return ret

