#!/usr/bin/env python
import wx
import os
import sys

def importmodule(modulename):
    """
    import a module
    """
    originalDir = os.getcwd()
    if sys.modules.has_key(modulename):
        del sys.modules[modulename]
    if originalDir:
        sys.path.insert(0, originalDir)
    mod = __import__(modulename)
    if originalDir:
        del sys.path[0]
    return mod

modDb = importmodule('db')
myDb = modDb.erpdb()
modTree = importmodule('TreeCtrl')
modGrid = importmodule('GridCustTable')

class MyLog(wx.PyLog):
    def __init__(self, textCtrl, logTime=0):
        wx.PyLog.__init__(self)
        self.tc = textCtrl
        self.logTime = logTime

    def DoLogString(self, message, timeStamp):
        #print message, timeStamp
        #if self.logTime:
        #    message = time.strftime("%X", time.localtime(timeStamp)) + \
        #              ": " + message
        if self.tc:
            self.tc.AppendText(message + '\n')

def TreeData():
    yield '/standard'
    yield '/analyer'
    yield '/semi-product'
    yield '/standard/screw'
    yield '/standard/pad'
    yield '/analyer/ultrared'
    yield '/semi-product/shihua'
    yield '/semi-product/huanbao'

class MainFrame(wx.Frame):
    ''' main frame 
            menu
            notebook
            info text
    '''
    def __init__(self,parent,title):
        wx.Frame.__init__(self,parent, title=title, size=(200,200))
        # Set up a log window
        self.log = wx.TextCtrl(self, -1,
                              style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL
                              ,size = (200, 80)
                              )
        if wx.Platform == "__WXMAC__":
            self.log.MacCheckSpelling(False)

        # Set the wxWindows log target to be this textctrl
        #wx.Log_SetActiveTarget(wx.LogTextCtrl(self.log))

        # But instead of the above we want to show how to use our own wx.Log category
        wx.Log_SetActiveTarget(MyLog(self.log))

        self.CreateStatusBar()
        filemenu = wx.Menu()
        menuAbout = filemenu.Append(wx.ID_ABOUT, "&About", "Information about programe")
        filemenu.AppendSeparator()
        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit"," Terminate")
        menubar = wx.MenuBar()
        menubar.Append(filemenu,"&File")
        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

        # add button
        button_event_table = [
                ("Add",self.OnClickAdd),
                ("Rename",self.OnClickRename),
                ("Delete",self.OnClickDelete),
                ("Save",self.OnClickSave),
                ("ClearLog",self.OnClickClear)
                ]
        self.button_dict = dict()
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        for (bName, bHander) in button_event_table:
            button = wx.Button(self, -1, bName, (30, 20))
            self.Bind(wx.EVT_BUTTON, bHander, button)
            buttonSizer.Add(button, 0, wx.EXPAND)
            self.button_dict[bName] = button

        # add categories tree view
        self.categoriesview = modTree.TestTreeCtrlPanel(self, self.log,myDb.get_categories_name)
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(buttonSizer, 0, wx.EXPAND)
        leftSizer.Add(self.categoriesview, 1, wx.EXPAND)

        self.grid = modGrid.CustTableGrid(self, self.log)
        centralSizer = wx.BoxSizer(wx.HORIZONTAL)
        centralSizer.Add(leftSizer, 0, wx.EXPAND)
        centralSizer.AddSpacer(15)
        centralSizer.Add(self.grid, 1, wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(centralSizer, 1, wx.EXPAND)
        self.sizer.Add(self.log, 0, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.Show(True)

    def OnAbout(self,e):
        self.log.WriteText("click about menu %s\n" % str(e))
        dlg = wx.MessageDialog(self, "Simple Erp", "About Simple Erp"
                , wx.OK
                )
        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self,e):
        self.Close(True)

    def OnClickAdd(self,e):
        self.categoriesview.Add()
        self.ModifyButton('Add')

    def ModifyButton(self, exceptme):
        opDone = self.categoriesview.GetOpDone()
        print opDone
        for bName in self.button_dict.keys() :
            if bName != exceptme and bName in opDone:
                print 'disable %s\n" % bName'
                b = self.button_dict[bName]
                b.Disable()


    def OnClickRename(self,e):
        self.categoriesview.Rename()
        self.ModifyButton('Rename')

    def OnClickDelete(self,e):
        self.categoriesview.Delete()
        self.ModifyButton('Delete')

    def OnClickSave(self,e):
        opDone = self.categoriesview.GetOpDone()
        print opDone
        for op in opDone:
            if op == 'Add':
                print 'save add'
                for catename in self.categoriesview.GetAdded():
                    myDb.insert_fullcategory(catename)
                print 'save add end'
            elif op == 'Rename':
                print 'save Rename'
                for catetuple in self.categoriesview.GetRenamed():
                    myDb.update_categories_by_name(*catetuple)
            elif op == 'Delete':
                print 'save Delete'
                for catename in self.categoriesview.GetDeleted():
                    myDb.delete_categories(catename)
                print 'save Delete end'
        self.categoriesview.ClearOperates()

        for bName in self.button_dict.keys() :
            b = self.button_dict[bName]
            b.Enable()


    def OnClickClear(self,e):
        self.log.Clear()


if __name__ == '__main__':
    app = wx.App(False)
    frame = MainFrame(None,  "Simple Erp")
    app.MainLoop()

