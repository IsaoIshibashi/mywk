# -*- coding: utf-8 -*-
import sys
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui


class CountDownWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent=parent)
        self.interval = 10
        self.setup_ui()


    def update_display(self):
        self.lcd_number.display("%6.2f" % (self.count / 100))
        self.lcd_number.update()


    def do_countdown(self):
        self.count -= 1
        self.update_display()
        if self.count <= 0:
            self.stop_countdown()


    def start_countdown(self):
        if self.count > 0.0:
            self.timer.start()


    def stop_countdown(self):
        self.timer.stop()


    def reset_count(self):
        self.count = 18000
        self.update_display()


    def setup_ui(self):
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        self.timer = QtCore.QTimer(parent=self)
        self.timer.setInterval(self.interval)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.do_countdown)

        self.lcd_number = QtGui.QLCDNumber(parent=self)
        self.lcd_number.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)

        self.lcd_number.setFrameStyle(QtGui.QFrame.NoFrame)
        self.lcd_number.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.lcd_number.setDigitCount(6)
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.lcd_number)
        self.setLayout(layout)

        self.reset_count()


class ButtonBoxWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent=parent)
        self.setup_ui()


    def setup_ui(self):
        self.start_button = QtGui.QPushButton("STRAT", parent=self)
        self.stop_button = QtGui.QPushButton("STOP", parent=self)
        self.reset_button = QtGui.QPushButton("RESET", parent=self)
        self.quit_button = QtGui.QPushButton("QUIT", parent=self)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.start_button, 0, 0)
        layout.addWidget(self.stop_button, 0, 1)
        layout.addWidget(self.reset_button, 1, 0)
        layout.addWidget(self.quit_button, 1, 1)

        self.setLayout(layout)
        
        

def main():
    app = QtGui.QApplication(sys.argv)

    panel = QtGui.QWidget()

    countdown_widget = CountDownWidget(parent=panel)
    button_box_widget = ButtonBoxWidget(parent=panel)

    panel_layout = QtGui.QVBoxLayout()
    panel_layout.addWidget(countdown_widget)
    panel_layout.addWidget(button_box_widget)
    panel.setLayout(panel_layout)
    panel.setFixedSize(320, 200)

    main_window = QtGui.QMainWindow()
    main_window.setWindowTitle("Ramen Timer")
    main_window.setCentralWidget(panel)

    main_window.show()

    button_box_widget.start_button.clicked.connect(
        countdown_widget.start_countdown)
    
    button_box_widget.stop_button.clicked.connect(
        countdown_widget.stop_countdown)
    
    button_box_widget.reset_button.clicked.connect(
        countdown_widget.reset_count)

    button_box_widget.quit_button.clicked.connect(
        app.quit)
    
    app.exec_()


if __name__ == "__main__":
    main()
    
    
