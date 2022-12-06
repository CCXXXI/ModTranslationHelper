import math

from PyQt5 import QtWidgets, QtGui, QtCore

import sys
from pathlib import Path

from PyQt5.QtCore import pyqtSlot

from custom_dialog_test1 import Ui_Dialog
from main import Prepper, Performer
from test1 import Ui_MainWindow
from deep_translator import GoogleTranslator


class MyWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent=parent)
        self.__ui = Ui_MainWindow()
        self.__ui.setupUi(self)
        MyWindow.setFixedSize(self, self.size())
        self.__running_thread = None

        self.__last_selected_directory = '/'
        self.__ui.run_pushButton.setText('Start')
        self.__ui.run_pushButton.setEnabled(False)
        for language in GoogleTranslator.get_supported_languages():
            self.__ui.selector_original_language_comboBox.addItem(language)
            self.__ui.selector_target_language_comboBox.addItem(language)
        self.__ui.selector_original_language_comboBox.setCurrentText('english')
        self.__ui.selector_target_language_comboBox.setCurrentText('russian')

        self.__ui.game_directory_pushButton.clicked.connect(self.__select_game_directory)
        self.__ui.original_directory_pushButton.clicked.connect(self.__select_original_directory)
        self.__ui.previous_directory_pushButton.clicked.connect(self.__select_previous_directory)
        self.__ui.target_directory_pushButton.clicked.connect(self.__select_target_directory)
        self.__ui.need_translation_checkBox.stateChanged.connect(self.__need_translate_changed)
        self.__ui.check_all_pushButton.clicked.connect(self.__check_all_checkboxes)
        self.__ui.uncheck_all_pushButton.clicked.connect(self.__unchecked_all_checkboxes)
        self.__ui.run_pushButton.clicked.connect(self.__run)
        self.__ui.game_directory_lineEdit.editingFinished.connect(self.__game_directory_changed)
        self.__ui.original_directory_lineEdit.editingFinished.connect(self.__original_directory_changed)
        self.__ui.previous_directory_lineEdit.editingFinished.connect(self.__previous_directory_changed)
        self.__ui.target_directory_lineEdit.editingFinished.connect(self.__target_directory_changed)

        self.__prepper = Prepper()
        self.__performer: Performer | None = None

    def __select_game_directory(self):
        chosen_path = QtWidgets.QFileDialog.getExistingDirectory(caption='Get Path',
                                                                 directory=self.__last_selected_directory)
        self.__ui.game_directory_lineEdit.setText(chosen_path)
        self.__last_selected_directory = chosen_path
        self.__game_directory_changed()

    def __game_directory_changed(self):
        self.__prepper.set_game_path(self.__ui.game_directory_lineEdit.text())
        if not self.__prepper.get_game_path_validate_result():
            self.__ui.game_directory_lineEdit.setText('')
            if not str(self.__prepper.get_game_path()) == '.':
                error = CustomDialog(parent=self.__ui.centralwidget, text='Указанная директория с игрой не найдена')
                error.show()
        self.__check_readiness()

    def __select_original_directory(self):
        chosen_path = QtWidgets.QFileDialog.getExistingDirectory(caption='Get Path',
                                                                 directory=self.__last_selected_directory)
        self.__ui.original_directory_lineEdit.setText(chosen_path)
        self.__last_selected_directory = chosen_path
        self.__original_directory_changed()

    def __original_directory_changed(self):
        self.__prepper.set_original_mode_path(self.__ui.original_directory_lineEdit.text())
        self.__form_checkbox_cascade(self.__prepper.get_original_mode_path_validate_result())
        if not self.__prepper.get_original_mode_path_validate_result():
            self.__ui.original_directory_lineEdit.setText('')
            if not str(self.__prepper.get_original_mode_path()) == '.':
                error = CustomDialog(parent=self.__ui.centralwidget, text='Указанная директория c локализацией '
                                                                        'мода не найдена')
                error.show()
        self.__check_readiness()

    def __select_previous_directory(self):
        chosen_path = QtWidgets.QFileDialog.getExistingDirectory(caption='Get Path',
                                                                 directory=self.__last_selected_directory)
        self.__ui.previous_directory_lineEdit.setText(chosen_path)
        self.__last_selected_directory = chosen_path
        self.__previous_directory_changed()

    def __previous_directory_changed(self):
        self.__prepper.set_previous_path(previous_path=self.__ui.previous_directory_lineEdit.text())
        if not self.__prepper.get_previous_path_validate_result():
            self.__ui.previous_directory_lineEdit.setText('')
            if not str(self.__prepper.get_previous_path()) == '.':
                error = CustomDialog(parent=self.__ui.centralwidget, text='Указанная директория с предыдущей версией '
                                                                        'перевода не найдена')
                error.show()

    def __select_target_directory(self):
        chosen_path = QtWidgets.QFileDialog.getExistingDirectory(caption='Get Path',
                                                                 directory=self.__last_selected_directory)
        self.__ui.target_directory_lineEdit.setText(chosen_path)
        self.__last_selected_directory = chosen_path
        self.__target_directory_changed()

    def __target_directory_changed(self):
        self.__prepper.set_target_path(self.__ui.target_directory_lineEdit.text())
        if not self.__prepper.get_target_path_validate_result():
            error = CustomDialog(parent=self.__ui.centralwidget,
                                 text='Невозможно получить доступ к диску. Проверьте путь к папке, в которую '
                                      'собираетесь записать перевод')
            error.show()
        self.__check_readiness()

    def __need_translate_changed(self):
        if self.__ui.need_translation_checkBox.isChecked():
            self.__ui.need_translate_scrollArea.setEnabled(True)
        else:
            self.__ui.need_translate_scrollArea.setEnabled(False)

    def __check_readiness(self):
        if self.__prepper.get_original_mode_path_validate_result() and self.__prepper.get_game_path_validate_result()\
               and self.__prepper.get_target_path_validate_result():
            self.__ui.run_pushButton.setEnabled(True)
        else:
            self.__ui.run_pushButton.setEnabled(False)

    def __form_checkbox_cascade(self, validate_result: bool):
        match validate_result:
            case True:
                files = self.__prepper.get_file_hierarchy()
                vertical_layout_widget = QtWidgets.QWidget()
                vertical_layout = QtWidgets.QVBoxLayout(vertical_layout_widget)
                for file_name in files:
                    file_name: Path
                    check_box = QtWidgets.QCheckBox(str(file_name))
                    check_box.setObjectName(str(file_name))
                    check_box.setChecked(True)
                    vertical_layout.addWidget(check_box)
                vertical_layout_widget.setLayout(vertical_layout)
                self.__ui.need_translate_scrollArea.setWidget(vertical_layout_widget)
            case False:
                info_label = QtWidgets.QLabel('Указанная директория с модом\n-\nне существует')
                font = QtGui.QFont()
                font.setBold(True)
                info_label.setFont(font)
                info_label.setAlignment(QtCore.Qt.AlignHCenter)
                self.__ui.need_translate_scrollArea.setWidget(info_label)
                error = CustomDialog(parent=self.__ui.centralwidget,
                                     text='Указанная директория с модом - не существует')
                error.show()

    def __check_all_checkboxes(self):
        for checkbox in self.__ui.need_translate_scrollArea.widget().children():
            if isinstance(checkbox, QtWidgets.QCheckBox):
                checkbox.setChecked(True)

    def __unchecked_all_checkboxes(self):
        for checkbox in self.__ui.need_translate_scrollArea.widget().children():
            if isinstance(checkbox, QtWidgets.QCheckBox):
                checkbox.setChecked(False)

    def __get_all_checkboxes(self) -> list:
        enabled = []
        for checkbox in self.__ui.need_translate_scrollArea.widget().children():
            if isinstance(checkbox, QtWidgets.QCheckBox) and checkbox.isChecked():
                enabled.append(Path(checkbox.objectName()))
        return enabled

    @pyqtSlot(str)
    def add_text_in_console(self, text: str):
        self.__ui.console_textBrowser.append(text)

    @pyqtSlot(str)
    def set_info_label_new_value(self, info: str):
        self.__ui.info_label.setText(info)

    @pyqtSlot(float)
    def set_progressbar_new_value(self, progress: float):
        value = self.__ui.progressBar.value() + progress * self.__ui.progressBar.maximum()
        if value > self.__ui.progressBar.maximum():
            self.__ui.progressBar.setValue(self.__ui.progressBar.maximum())
        else:
            self.__ui.progressBar.setValue(math.ceil(value))

    @pyqtSlot()
    def stop_thread(self):
        self.__ui.run_pushButton.setEnabled(True)
        self.__running_thread.exec_()

    def __run(self):
        self.__performer = Performer(
            paths=self.__prepper,
            original_language=self.__ui.selector_original_language_comboBox.currentText(),
            target_language=self.__ui.selector_target_language_comboBox.currentText(),
            need_translate=self.__ui.need_translation_checkBox.isChecked(),
            need_translate_list=self.__get_all_checkboxes()
        )

        self.__ui.run_pushButton.setEnabled(False)

        self.__running_thread = QtCore.QThread()

        self.__performer.moveToThread(self.__running_thread)

        # Коннекты сигналов и слотов для межпоточной передачи информации
        self.__performer.info_console_value.connect(self.add_text_in_console)
        self.__performer.info_label_value.connect(self.set_info_label_new_value)
        self.__performer.progress_bar_value.connect(self.set_progressbar_new_value)
        self.__performer.finish_thread.connect(self.stop_thread)

        self.__running_thread.started.connect(self.__performer.run)

        self.__running_thread.start()


class CustomDialog(QtWidgets.QDialog):

    def __init__(self, parent=None, text=None):
        super(CustomDialog, self).__init__(parent)
        self.__ui = Ui_Dialog()
        self.__ui.setupUi(self)
        CustomDialog.setFixedSize(self, self.size())

        self.__ui.no_path_error_textBrowser.setText(text)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    application = MyWindow()
    application.show()

    sys.exit(app.exec_())
