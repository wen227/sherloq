import cv2 as cv
import numpy as np
from PySide2.QtCore import Qt
from PySide2.QtGui import QColor
from PySide2.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QRadioButton)
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

from tools import ToolWidget
from utility import compute_hist, modify_font, ParamSlider


class HistWidget(ToolWidget):
    def __init__(self, image, parent=None):
        super(ToolWidget, self).__init__(parent)

        self.rgb_radio = QRadioButton(self.tr('RGB'))
        self.rgb_radio.setChecked(True)
        self.last_radio = self.rgb_radio
        self.red_radio = QRadioButton(self.tr('Red'))
        self.green_radio = QRadioButton(self.tr('Green'))
        self.blue_radio = QRadioButton(self.tr('Blue'))
        self.value_radio = QRadioButton(self.tr('Value'))
        self.log_check = QCheckBox(self.tr('Log scale'))
        self.grid_check = QCheckBox(self.tr('Show grid'))
        self.marker_check = QCheckBox(self.tr('Show markers'))
        self.marker_check.setToolTip(self.tr('Show plot markers for min(--), avg(-), max(-.)'))
        self.start_slider = ParamSlider([0, 255], 8, 0, label='Start:', bold=True)
        self.end_slider = ParamSlider([0, 255], 8, 255, label='End:', bold=True)

        channels = cv.split(cv.cvtColor(image, cv.COLOR_BGR2RGB))
        channels.append(cv.cvtColor(image, cv.COLOR_BGR2GRAY))
        self.hist = [compute_hist(c) for c in channels]
        rows, cols, chans = image.shape
        pixels = rows * cols
        unique = np.unique(np.reshape(image, (pixels, chans)), axis=0).shape[0]
        unique_ratio = unique / pixels * 100
        unique_label = QLabel(self.tr(
            'total pixels = {}, unique colors = {} ({:.2f}%) '.format(pixels, unique, unique_ratio)))
        modify_font(unique_label, italic=True)

        self.rgb_radio.clicked.connect(self.redraw)
        self.red_radio.clicked.connect(self.redraw)
        self.green_radio.clicked.connect(self.redraw)
        self.blue_radio.clicked.connect(self.redraw)
        self.value_radio.clicked.connect(self.redraw)
        self.log_check.stateChanged.connect(self.redraw)
        self.grid_check.stateChanged.connect(self.redraw)
        self.marker_check.stateChanged.connect(self.redraw)
        self.start_slider.valueChanged.connect(self.redraw)
        self.end_slider.valueChanged.connect(self.redraw)

        self.table_widget = QTableWidget(8, 2)
        self.table_widget.setHorizontalHeaderLabels([self.tr('Property'), self.tr('Value')])
        self.table_widget.setItem(0, 0, QTableWidgetItem(self.tr('Least frequent')))
        self.table_widget.setItem(1, 0, QTableWidgetItem(self.tr('Most frequent')))
        self.table_widget.setItem(2, 0, QTableWidgetItem(self.tr('Average level')))
        self.table_widget.setItem(3, 0, QTableWidgetItem(self.tr('Median level')))
        self.table_widget.setItem(4, 0, QTableWidgetItem(self.tr('Deviation')))
        self.table_widget.setItem(5, 0, QTableWidgetItem(self.tr('Pixel count')))
        self.table_widget.setItem(6, 0, QTableWidgetItem(self.tr('Percentile')))
        self.table_widget.setItem(7, 0, QTableWidgetItem(self.tr('Smoothness')))
        for i in range(self.table_widget.rowCount()):
            modify_font(self.table_widget.item(i, 0), bold=True)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.resizeColumnsToContents()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setMaximumWidth(200)

        figure = Figure()
        plot_canvas = FigureCanvas(figure)
        self.axes = plot_canvas.figure.subplots()
        self.redraw()
        figure.set_tight_layout(True)

        right_layout = QVBoxLayout()
        table_label = QLabel(self.tr('Range properties'))
        modify_font(table_label, bold=True)
        table_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(table_label)
        right_layout.addWidget(self.table_widget)
        right_layout.addWidget(self.marker_check)
        right_layout.addWidget(self.start_slider)
        right_layout.addWidget(self.end_slider)

        center_layout = QHBoxLayout()
        center_layout.addWidget(plot_canvas)
        center_layout.addLayout(right_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(QLabel(self.tr('Channel:')))
        bottom_layout.addWidget(self.rgb_radio)
        bottom_layout.addWidget(self.red_radio)
        bottom_layout.addWidget(self.green_radio)
        bottom_layout.addWidget(self.blue_radio)
        bottom_layout.addWidget(self.value_radio)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.log_check)
        bottom_layout.addWidget(self.grid_check)
        bottom_layout.addStretch()
        bottom_layout.addWidget(unique_label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(center_layout)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def redraw(self):
        x = np.arange(256)
        alpha = 0.25
        rgb = self.rgb_radio.isChecked()
        red = self.red_radio.isChecked()
        green = self.green_radio.isChecked()
        blue = self.blue_radio.isChecked()
        value = self.value_radio.isChecked()
        grid = self.grid_check.isChecked()
        log = self.log_check.isChecked()
        try:
            self.axes.clear()
        except RecursionError:
            return
        y = None
        if value:
            y = self.hist[3]
            self.axes.step(x, y, 'k', where='mid')
            self.axes.fill_between(x, y, alpha=alpha, facecolor='k', step='mid')
        else:
            # TODO: Ottimizzare facendo un ciclo senza ripetere le istruzioni
            if red or rgb:
                y = self.hist[0]
                self.axes.step(x, y, 'r', where='mid')
                self.axes.fill_between(x, y, alpha=alpha, facecolor='r', step='mid')
            if green or rgb:
                y = self.hist[1]
                self.axes.step(x, y, 'g', where='mid')
                self.axes.fill_between(x, y, alpha=alpha, facecolor='g', step='mid')
            if blue or rgb:
                y = self.hist[2]
                self.axes.step(x, y, 'b', where='mid')
                self.axes.fill_between(x, y, alpha=alpha, facecolor='b', step='mid')
        if log:
            self.axes.set_yscale('log')
            self.axes.set_ylim(bottom=1)
        else:
            self.axes.set_yscale('linear')
            self.axes.set_ylim(bottom=0)
        self.axes.set_xlim([-1, 256])
        self.axes.set_xlabel(self.tr('intensity value'))
        self.axes.set_ylabel(self.tr('pixel count'))
        self.axes.set_xticks([0, 64, 128, 192, 255])
        self.axes.grid(grid, which='both')

        if rgb:
            self.table_widget.setEnabled(False)
            self.marker_check.setEnabled(False)
            self.start_slider.setEnabled(False)
            self.end_slider.setEnabled(False)
            for i in range(self.table_widget.rowCount()):
                if self.table_widget.item(i, 1) is not None:
                    self.table_widget.item(i, 1).setText('')
                    self.table_widget.item(i, 1).setBackgroundColor(QColor('white'))
        else:
            self.table_widget.setEnabled(True)
            self.marker_check.setEnabled(True)
            self.start_slider.setEnabled(True)
            self.end_slider.setEnabled(True)
            start = self.start_slider.value()
            end = self.end_slider.value()
            if end <= start:
                end = start + 1
            elif start >= end:
                start = end - 1
            total = np.sum(y)
            x = x[start:end+1]
            y = y[start:end+1]
            count = np.sum(y)
            if count != 0:
                argmin = np.argmin(y) + start
                argmax = np.argmax(y) + start
                mean = np.round(np.sum(x * y) / count, 2)
                stddev = np.round(np.sqrt(np.sum(((x - mean)**2) * y) / count), 2)
                median = np.argmax(np.cumsum(y) > count / 2) + start
                percent = np.round(count / total * 100, 2)
                y = y / np.max(y)
                sweep = len(y)
                smooth = 0
                if sweep > 2:
                    for i in range(1, sweep - 1):
                        h0 = y[i - 1]
                        h1 = y[i]
                        h2 = y[i + 1]
                        smooth += abs((h0 + h2) / 2 - h1)
                    smooth = np.round((1 - (smooth / (sweep - 2))) * 100, 2)
                if self.marker_check.isChecked():
                    self.axes.axvline(argmin, linestyle='--', color='m')
                    self.axes.axvline(mean, linestyle='-', color='m')
                    self.axes.axvline(argmax, linestyle='-.', color='m')
            else:
                argmin = argmax = mean = stddev = median = percent = smooth = 0
            self.table_widget.setItem(0, 1, QTableWidgetItem(str(argmin)))
            self.table_widget.setItem(1, 1, QTableWidgetItem(str(argmax)))
            self.table_widget.setItem(2, 1, QTableWidgetItem(str(mean)))
            self.table_widget.setItem(3, 1, QTableWidgetItem(str(median)))
            self.table_widget.setItem(4, 1, QTableWidgetItem(str(stddev)))
            self.table_widget.setItem(5, 1, QTableWidgetItem(str(count)))
            self.table_widget.setItem(6, 1, QTableWidgetItem(str(percent) + '%'))
            self.table_widget.setItem(7, 1, QTableWidgetItem(str(smooth) + '%'))
            if smooth <= 80:
                self.table_widget.item(7, 1).setBackgroundColor(QColor.fromHsv(0, 96, 255))
            elif smooth <= 90:
                self.table_widget.item(7, 1).setBackgroundColor(QColor.fromHsv(30, 96, 255))
            elif smooth <= 95:
                self.table_widget.item(7, 1).setBackgroundColor(QColor.fromHsv(60, 96, 255))
            else:
                self.table_widget.item(7, 1).setBackgroundColor(QColor.fromHsv(90, 96, 255))
            self.table_widget.resizeColumnsToContents()
            if start != 0 or end != 255:
                self.axes.axvline(start, linestyle=':', color='k')
                self.axes.axvline(end, linestyle=':', color='k')
                _, top = self.axes.get_ylim()
                self.axes.fill_between(np.arange(start, end + 1), top, facecolor='y', alpha=alpha*2)
        self.axes.figure.canvas.draw()
