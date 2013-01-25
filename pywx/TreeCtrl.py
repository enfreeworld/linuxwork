
import  string
import  wx
import  images
import re
import posixpath as pathutil

def get_sub_class_component(parent,subject):
    sub_component = re.compile('^%s/[^/]+$' % parent)
    ret = sub_component.search(subject)
    if ret is None:
        return None
    else:
        return re.search('[^/]+$', subject).group(0)

def IsNotSubClass(parent, subject):
    subs = re.compile('%s/.+' % parent)
    ret = subs.match(subject)
    return ret is None

class TreeItemSelectEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id, data):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.data = data

    def GetData(self):
        return self.data
# create a new event type
MyEVT_TREE_SELECT = wx.NewEventType()
# create a bind object
EVT_TREE_SELECT = wx.PyEventBinder(MyEVT_TREE_SELECT, 1)
#---------------------------------------------------------------------------

class MyTreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, id, pos, size, style, log):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
        self.log = log

    def OnCompareItems(self, item1, item2):
        t1 = self.GetItemText(item1)
        t2 = self.GetItemText(item2)
        self.log.WriteText('compare: ' + t1 + ' <> ' + t2 + '\n')
        if t1 < t2: return -1
        if t1 == t2: return 0
        return 1

#---------------------------------------------------------------------------

class TestTreeCtrlPanel(wx.Panel):
    def __init__(self, parent, log, datagentor):
        self.addItems = []
        self.deleteItems = []
        self.editItems = []
        self.state = 'normal'
        self.operates = []
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.log = log
        tID = wx.NewId()

        self.tree = MyTreeCtrl(self, tID, wx.DefaultPosition, wx.DefaultSize,
                               wx.TR_DEFAULT_STYLE
                               #wx.TR_HAS_BUTTONS
                               #| wx.TR_EDIT_LABELS
                               #| wx.TR_MULTIPLE
                               #| wx.TR_HIDE_ROOT
                               , self.log)

        isz = (24,24)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        self.fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        self.smileidx    = il.Add(images.Smiles.GetBitmap())

        self.tree.SetImageList(il)
        self.il = il


        # ------------------ create tree start ------------------------------------------
        self.root = self.tree.AddRoot("Matrials")
        self.tree.SetPyData(self.root, '')
        self.tree.SetItemImage(self.root, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, self.fldropenidx, wx.TreeItemIcon_Expanded)
        self.CreateTree(self.root, datagentor)
        # ------------------ create tree end -------------------------------------------

        # ------------------ bind event -----------------------------------------------
        self.tree.Expand(self.root)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed, self.tree)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.tree)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndEdit, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivate, self.tree)

        self.tree.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.tree.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.tree.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        # ------------------ bind event end --------------------------------------------

    def CreateTree(self,parent,datagentor):
        pitem = parent
        citem = parent
        for item in datagentor(''):
            pData = self.tree.GetItemData(pitem).GetData()
            subClass = get_sub_class_component(pData,item)
            while subClass is None:
                (citem,cookie) = self.tree.GetFirstChild(pitem)
                pData = self.tree.GetItemData(citem).GetData()
                while IsNotSubClass(pData,item) and citem.IsOk():
                    (citem,cookie) = self.tree.GetNextChild(pitem, cookie)
                    pData = self.tree.GetItemData(citem).GetData()
                if not citem.IsOk():
                    break;
                pitem = citem
                subClass = get_sub_class_component(pData,item)
            
            if not citem.IsOk():
                continue;
            child = self.tree.AppendItem(pitem, "%s" % subClass)
            itemdata = item
            self.tree.SetPyData(child, itemdata)
            self.tree.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
            self.tree.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)
            pitem = parent


    def Add(self):
        pitem = self.tree.GetSelection()
        #self.tree.Expand(pitem)
        pData = self.tree.GetItemData(pitem).GetData()
        citemdata = pData + '/' + "NEW"
        citem = self.tree.AppendItem(pitem, "NEW")
        self.tree.SetPyData(citem, citemdata)
        self.tree.SetItemImage(citem, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(citem, self.fldropenidx, wx.TreeItemIcon_Expanded)

        self.addItems.append(citem)
        self.tree.Expand(pitem)
        self.tree.EditLabel(citem)
        self.state = 'Add'
        if 'Add' not in self.operates:
            self.operates.append('Add')

    def GetAdded(self):
        for item in self.addItems:
            if item is not None:
                data = self.tree.GetItemData(item).GetData()
                yield data
        self.addItems=[]
        self.state = 'normal'

    def Delete(self):
        pitem = self.tree.GetSelection()
        if pitem in self.addItems:
            self.addItems.remove(pitem)
            for item in self.GetChildrens(pitem):
                self.addItems.remove(item)
            self.tree.Delete(pitem)
            return
        pData = self.tree.GetItemData(pitem).GetData()
        self.tree.Delete(pitem)
        self.deleteItems.append(pData)
        if 'Delete' not in self.operates:
            self.operates.append('Delete')

    def GetChildrens(self, parent):
        (citem,cookie) = self.tree.GetFirstChild(parent)
        if citem is None :
            return
        cData = self.tree.GetItemData(citem).GetData()
        if cData is None:
            return
        print 'delete item %s' % cData
        yield citem
        self.GetChildrens(citem)
        (citem,cookie) = self.tree.GetNextChild(parent, cookie)
        while citem is not None:
            cData = self.tree.GetItemData(citem).GetData()
            if cData is None:
                break
            print 'delete item %s' % cData
            yield citem
            self.GetChildrens(citem)
            (citem,cookie) = self.tree.GetNextChild(parent, cookie)
        return


    def GetDeleted(self):
        for item in self.deleteItems:
            yield item
        del self.deleteItems[0:]

    def GetRenamed(self):
        for editeditem in self.editItems:
            yield editeditem
        self.editItems = []
    def Rename(self):
        pitem = self.tree.GetSelection()
        pData = self.tree.GetItemData(pitem).GetData()
        self.state = 'Rename'
        self.tree.EditLabel(pitem)

    def GetOperates(self):
        for op in self.operates :
            print op
            yield op
    def GetOpDone(self):
        return self.operates

    def ClearOperates(self):
        self.operates = []

    # update the sub-cate recursively
    def Updatefrom(self, parent):
        (citem,cookie) = self.tree.GetFirstChild(parent)
        if citem is None :
            return
        pData = self.tree.GetItemData(parent).GetData()
        cData = self.tree.GetItemData(citem).GetData()
        if cData is None:
            return
        data = pData + '/' + pathutil.basename(cData)
        self.tree.SetPyData(citem, data) 
        self.editItems.append((data,cData))
        self.Updatefrom(citem)
        (citem,cookie) = self.tree.GetNextChild(parent, cookie)
        while citem is not None:
            cData = self.tree.GetItemData(citem).GetData()
            if cData is None:
                break
            data = pData + '/' + pathutil.basename(cData)
            self.tree.SetPyData(citem, data) 
            self.editItems.append((data,cData))
            self.Updatefrom(citem)
            (citem,cookie) = self.tree.GetNextChild(parent, cookie)

        return

        

    def OnRightDown(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnRightClick: %s, %s, %s\n" %
                               (self.tree.GetItemText(item), type(item), item.__class__))
            self.tree.SelectItem(item)


    def OnRightUp(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:        
            self.log.WriteText("OnRightUp: %s (manually starting label edit)\n"
                               % self.tree.GetItemText(item))
            self.tree.EditLabel(item)



    def OnBeginEdit(self, event):
        self.log.WriteText("OnBeginEdit\n")
        # show how to prevent edit...
        item = event.GetItem()
        if self.state == 'Rename':
            return
        if item not in self.addItems:
            wx.Bell()
            event.Veto()
            return
        if item and self.tree.GetItemText(item) == "Matrials":
            wx.Bell()
            self.log.WriteText("You can't edit this one...\n")

            # Lets just see what's visible of its children
            cookie = 0
            root = event.GetItem()
            (child, cookie) = self.tree.GetFirstChild(root)

            while child.IsOk():
                self.log.WriteText("Child [%s] visible = %d" %
                                   (self.tree.GetItemText(child),
                                    self.tree.IsVisible(child)))
                (child, cookie) = self.tree.GetNextChild(root, cookie)

            event.Veto()


    def OnEndEdit(self, event):
        self.log.WriteText("OnEndEdit: %s %s\n" %
                           (event.IsEditCancelled(), event.GetLabel()) )
        if event.IsEditCancelled() :
            return
        item = event.GetItem()
        odata = self.tree.GetItemData(item).GetData()
        data = pathutil.dirname(odata)
        if data == '/' :
            data = ''
        data = data + '/' + event.GetLabel()
        self.tree.SetPyData(item, data)
        if self.state == 'Rename' and data != odata:
            print 'rename the childs'
            self.editItems.append((data, odata))
            self.Updatefrom(item)
            self.state = 'normal'
            if 'Rename' not in self.operates:
                self.operates.append('Rename')
        print 'dirname: %s' % data
        # show how to reject edit, we'll not allow any digits
#        for x in event.GetLabel():
#            if x in string.digits:
#                self.log.WriteText("You can't enter digits...\n")
#                event.Veto()
#                return


    def OnLeftDClick(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnLeftDClick: %s\n" % self.tree.GetItemText(item))
            self.tree.Expand(item)
        event.Skip()


    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0, 0, w, h)


    def OnItemExpanded(self, event):
        item = event.GetItem()
        if item:
            self.log.WriteText("OnItemExpanded: %s\n" % self.tree.GetItemText(item))

    def OnItemCollapsed(self, event):
        item = event.GetItem()
        if item:
            self.log.WriteText("OnItemCollapsed: %s\n" % self.tree.GetItemText(item))

    def OnSelChanged(self, event):
        self.item = event.GetItem()
        if self.item:
            self.log.WriteText("OnSelChanged: %s\n" % self.tree.GetItemText(self.item))
            self.log.WriteText("on selchanged: %s\n" % self.tree.GetItemData(self.item).GetData())
            if wx.Platform == '__WXMSW__':
                self.log.WriteText("BoundingRect: %s\n" %
                                   self.tree.GetBoundingRect(self.item, True))
            #items = self.tree.GetSelections()
            #print map(self.tree.GetItemText, items)
        event.Skip()
        evt = TreeItemSelectEvent(MyEVT_TREE_SELECT, self.GetId(), self.tree.GetItemData(self.item).GetData())
        self.GetEventHandler().ProcessEvent(evt)


    def OnActivate(self, event):
        if self.item:
            self.log.WriteText("OnActivate: %s\n" % self.tree.GetItemText(self.item))


#---------------------------------------------------------------------------

def runTest(frame, nb, log):
    win = TestTreeCtrlPanel(nb, log)
    return win

#---------------------------------------------------------------------------





overview = """\
A TreeCtrl presents information as a hierarchy, with items that may be 
expanded to show further items. Items in a tree control are referenced by 
wx.TreeItemId handles.

"""



if __name__ == '__main__':
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

