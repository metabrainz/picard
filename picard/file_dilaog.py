from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import os,sys
if os.name == 'nt':
    import win32api, win32con
from datetime import datetime

def Is_hidden(file_temp):
    if os.name== 'nt':
        attribute = win32api.GetFileAttributes(file_temp)
        return attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
    else:
        return file_temp.startswith('.')

class ImgWidget1(QLabel):
    """
    Class used to show picture on Table Row
    """
    def __init__(self, imagePath,parent=None):
        super(ImgWidget1, self).__init__(parent)
        pic = QPixmap(imagePath)
        self.setPixmap(pic)

class File_dialog(QDialog):
    """
    Main class used for the dialog
    """
    def __init__(self,wi,he,path,parent=None):
        self.path = path
        self.formats=["MP3","FLAC","OGG","M4A","WMA","WAV","MP4","AAC","flv"]
        self.formats_lower=[]
        for i in self.formats:self.formats_lower.append(i.lower())
        self.formats_show=["MP3","FLAC","OGG","M4A","WMA","WAV","MP4","AAC","flv"]
        super(File_dialog,self).__init__(parent)
        self.initUI(wi,he)

    def initUI(self,wi,he):
        self.moveBack = QPushButton(self)
        self.moveBack.resize(35,30)
        self.moveBack.setIcon(QIcon('../resources/img-src/moveBack24_24.png'))
        self.moveBack.setIconSize(QSize(35,30))
        self.moveBack.move(.17*wi,10)
        self.moveBack.clicked.connect(self.moveBack_action)
        self.moveNext = QPushButton(self)
        self.moveNext.resize(35,30)
        self.moveNext.setIcon(QIcon('../resources/img-src/moveNext24_24.png'))
        self.moveNext.setIconSize(QSize(35,30))
        self.moveNext.move(.17*wi+35,10)
        self.moveNext.clicked.connect(self.moveNext_action)

        self.selectBtn = QPushButton("Select It",self)
        self.selectBtn.resize(100,30)
        self.selectBtn.move(wi-0.09*wi,10)
        self.selectBtn.clicked.connect(lambda:self.select_action(True))

        self.selectBtn1 = QPushButton("Open Folder",self)
        self.selectBtn1.resize(150,30)
        self.selectBtn1.move(wi-.219*wi,10)
        self.selectBtn1.clicked.connect(lambda:self.open_action(True))

        self.lineedit = QLineEdit("Search here",self)
        self.lineedit.resize(250,30)
        self.lineedit.move(wi-.51*wi,10)
        #self.lineedit.hide()
        self.helpbtn = QPushButton(self)
        self.helpbtn.resize(40,30)
        self.helpbtn.setIcon(QIcon('../resources/img-src/search24_24.png'))
        self.helpbtn.setIconSize(QSize(40,30))
        self.helpbtn.move(wi-.32*wi,10)
        #self.helpbtn.clicked.connect(self.lineedit.show)
        self.helpbtn.clicked.connect(self.search_update)

        self.lw=int(.15*wi)
        self.l1w=wi-self.lw
        self.listWidget = QListWidget(self)
        self.listWidget.resize(self.lw,he-.195*he)
        self.listWidget.move(0,0)

        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(("Name;Size;Modified").split(";"))
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        cw=int(.7*self.l1w)
        cw1=int(.143*self.l1w)
        cw2=int(.143*self.l1w)
        self.table.setColumnWidth(0,cw)
        self.table.setColumnWidth(1,cw1)
        self.table.setColumnWidth(2,cw2)
        self.show_files(False)
        self.table.resize(self.l1w,he-.26*he)
        self.table.move(self.lw,50)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(self.default_setting)

        self.checkBox = QCheckBox("Show hidden files/folders",self)
        self.checkBox.resize(200,30)
        self.checkBox.move(wi-.365*wi,he-.17*he)
        self.checkBox.toggled.connect(lambda:self.show_hidden(self.checkBox))

        self.cb = QComboBox(self)
        self.cb.addItem("All Supported Formats")
        self.cb.addItems(self.formats_show)
        self.cb.resize(200,30)
        self.cb.move(wi-.183*wi,he-.17*he)
        self.cb.currentIndexChanged.connect(self.format_modifier)

        self.resize(wi,he)
        sys.exit(self.exec_())

    def format_modifier(self,i):

        self.formats.clear()
        self.formats_lower.clear()
        if not self.cb.itemText(i) == "All Supported Formats":
            self.formats = [self.cb.itemText(i)]
        else:
            self.formats=["MP3","FLAC","OGG","M4A","WMA","WAV","MP4","AAC","flv"]

        for i in self.formats:self.formats_lower.append(i.lower())

        self.show_files(False)

    def default_setting(self):
        indexes = self.table.selectionModel().selectedRows()
        if len(indexes) == 1:
            #for index in (indexes):
            if os.path.isdir(os.path.join(self.path,self.table.item(indexes[0].row(),0).text()[6:])):
                self.open_action(indexes)
            else:
                self.select_action(indexes)
        else :
            self.select_action(indexes)

    def open_action(self,indexes):
        if indexes == True:
            indexes = self.table.selectionModel().selectedRows()
        if len(indexes) == 1:
            if os.path.isdir(os.path.join(self.path,self.table.item(indexes[0].row(),0).text()[6:])):
                hola = (self.table.item(indexes[0].row(),0)).text()[6:]
                self.path = os.path.join(self.path,hola)
                self.show_files(False)

    def select_action(self,indexes):
        if indexes == True:
            indexes = self.table.selectionModel().selectedRows()
        self.send_things = []
        for index in (indexes):
            hola = (self.table.item(index.row(),0)).text()[6:]
            if os.path.isdir(os.path.join(self.path,hola)):
                self.recu_folder(self.send_things,os.path.join(self.path,hola))
            else:
                self.send_things.append(os.path.join(self.path,hola))
        for  i in self.send_things:
            print(i)
        #print(self.send_things)
        sys.exit()

    def recu_folder(self,lis,path):
       temp = os.listdir(path)
       for i in temp:
            if os.path.isfile(os.path.join(path,i)):
                for j in self.formats_lower:
                    if i.endswith('.'+j):
                        lis.append(os.path.join(path,i))
            else:
                self.recu_folder(lis,os.path.join(path,i))

    def moveBack_action(self):
        self.path = os.path.dirname((os.path.abspath(self.path)))
        self.show_files(False)

    def moveNext_action(self):
        indexes = self.table.selectionModel().selectedRows()
        if len(indexes) == 1:
            if os.path.isdir(os.path.join(self.path,self.table.item(indexes[0].row(),0).text()[6:])):
                self.path = os.path.join(self.path,self.table.item(indexes[0].row(),0).text()[6:])
                self.show_files(False)
        if len(indexes) == 0:
            temp_name = []
            for i in os.listdir(self.path) :
                if os.path.isdir(os.path.join(self.path,i)):
                    temp_name.append(i)
            if len(temp_name) >0:
                #sort(temp_name)
                self.path=os.path.join(self.path,temp_name[0])
                self.show_files(False)

    def show_files(self,hidden):
        self.hidden_items = 0
        self.files_to_show()
        if hidden == False :
            self.table.setRowCount(len(self.dirs)+len(self.files)-self.hidden_items)
        else:
            self.table.setRowCount(len(self.dirs)+len(self.files))
        start,pos,j=0,0,0
        while start < len(self.dirs):
            if hidden == False :
                if Is_hidden(self.dirs[start]) == True:
                    start=start+1
                    continue
            self.table.setItem(pos,0,QTableWidgetItem("      "+self.dirs[start]))
            self.table.setItem(pos,1,QTableWidgetItem(self.dirs_size[start]))
            self.table.setItem(pos,2,QTableWidgetItem(self.dirs_modi_time[start]))
            self.table.setCellWidget(pos, 0, ImgWidget1("../resources/img-src/folder24_24.png"))
            pos,start=pos+1,start+1

        while j < len(self.files):
            if hidden == False :
                if Is_hidden(self.files[j]) == True:
                    j=j+1
                    continue
            self.table.setItem(pos,0,QTableWidgetItem("      "+self.files[j]))
            self.table.setItem(pos,1,QTableWidgetItem(self.files_size[j]))
            self.table.setItem(pos,2,QTableWidgetItem(self.files_modi_time[j]))
            self.table.setCellWidget(pos, 0, ImgWidget1("../resources/img-src/music24_24.png"))
            pos,j=pos+1,j+1

    def search_update(self):
        print(self.lineedit.text())
        self.lineedit.setText("")

    def show_hidden(self,cb):
        if cb.isChecked() == True:
            self.show_files(True)
        else:
            self.show_files(False)

    def files_to_show(self):
        self.files = []
        self.files_size = []
        self.files_modi_time = []
        self.dirs = []
        self.dirs_size = []
        self.dirs_modi_time = []
        def converter(num):
            for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                if num < 1024.0:
                    return "%3.1f %s" % (num, x)
                num /= 1024.0

        for i in os.listdir(self.path):
            file_info = os.stat(os.path.join(self.path,i))
            if Is_hidden(i):
                if os.path.isfile(os.path.join(self.path,i)):
                    for j in self.formats_lower:
                        if i.endswith('.'+j):
                            self.hidden_items=self.hidden_items+1
                else:
                    self.hidden_items=self.hidden_items+1
            date_= str((datetime.fromtimestamp(file_info.st_mtime)).date())
            if os.path.isdir(os.path.join(self.path,i)):
                self.dirs.append(i)
                self.dirs_size.append("NA")
                self.dirs_modi_time.append(date_)
            else:
                for j in self.formats_lower:
                    if i.endswith('.'+j) == True:
                        self.files.append(i)
                        self.files_size.append(converter(file_info.st_size))
                        self.files_modi_time.append(date_)
                        break

if __name__ == '__main__':

    app = QApplication(sys.argv)
    screen_resolution = app.desktop().screenGeometry()
    width, height = screen_resolution.width(), screen_resolution.height()
    path=os.getcwd()
    ex=File_dialog(width,height,path)
    sys.exit(app.exec_())
