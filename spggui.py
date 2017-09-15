
import wx
import select
import socket
import threading
from threading import Thread
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub as Publisher

# GUI
class MainFrame(wx.Frame):
    title = 'Test GUI'

    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title, size=(600, 600))

        panel = wx.Panel(self)
        notebook = wx.Notebook(panel)

        # start ipc server
        self.ipc = IPCThread()

        # Pages
        firstPage = FirstPage(notebook)
        notebook.AddPage(firstPage, 'First Page')
        self.first = notebook.GetPage(0)


        # Menu
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        exit_file = file_menu.Append(wx.ID_EXIT, 'Quit' + 'CTRL+Q', 'Quit application')
        exitId = wx.NewId()
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('Q'), exitId)])
        menubar.Append(file_menu, 'File')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.OnQuit, exit_file)
        self.Bind(wx.EVT_MENU, self.OnQuit, id=exitId)
        self.SetAcceleratorTable(accel_tbl)

        # Status Bar
        self.statusbar = self.CreateStatusBar(2)
        self.statusbar.SetStatusWidths([300, 300])
        self.statusbar.SetStatusText('Update:')

        # Subscriptions
        Publisher.subscribe(self.updateStatusBar, 'statusbar.update')

        # Sizing
        sizer = wx.BoxSizer()
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL)
        panel.SetSizer(sizer)
        panel.Layout()

        self.Show()

#------------------------------------------------------------------------------------
    def updateStatusBar(self, status):
        self.statusbar.SetStatusText('Update: ' + status.data)

#------------------------------------------------------------------------------------
    def OnQuit(self, event):
        self.Close()
#------------------------------------------------------------------------------------

class FirstPage(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER | wx.STB_DEFAULT_STYLE)
        self.parent = parent

        self.label1 = wx.StaticText(self, -1, label='Unnecessary Label')
        self.textreceive = wx.StaticText(self, -1, label = u'Show received text here.')
        self.TextEntry1 = wx.TextCtrl(self, -1, value=u'Enter text here.', style= wx.TE_MULTILINE, size=(400, 300))
        self.SendButton = wx.Button(self, -1, label='Send')
        self.Bind(wx.EVT_BUTTON, self.OnSendButton, self.SendButton)
        logbutton = wx.Button(self, label='Open Log')
        logbutton.Bind(wx.EVT_BUTTON, self.popupLog)

        # Subscriptions
        Publisher.subscribe(self.updateText, 'update')

        # Sizing
        self.vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.label1, 0, wx.CENTER, 5)
        self.hbox2.Add(self.TextEntry1, 0, wx.CENTER, wx.EXPAND)
        self.hbox3.Add(self.SendButton, 0, wx.CENTER, 5)
        self.hbox4.Add(self.textreceive, 0, wx.CENTER, 5)
        self.vbox1.Add(self.hbox1, 10, wx.CENTER)
        self.vbox1.Add(self.hbox2, 0, wx.CENTER, wx.EXPAND)
        self.vbox1.Add(self.hbox3, 10, wx.CENTER)
        self.vbox1.Add(self.hbox4, 5, wx.CENTER)
        self.SetSizer(self.vbox1)

        self.Show(True)

#------------------------------------------------------------------------------------
    def OnSendButton(self, event):
        self.TextEntry1.SetFocus()  # to auto select the entry
        self.TextEntry1.SetSelection(-1, -1)

        message = self.TextEntry1.GetValue()
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', 8080))
            client.send(message)
            client.shutdown(socket.SHUT_RDWR)
            client.close()
        except Exception, msg:
            print msg

        self.textreceive.SetLabel(message)
        Publisher.sendMessage('openlog', message)

#------------------------------------------------------------------------------------
    def updateText(self, msg):
        if str(msg.data) == self.TextEntry1.GetValue():
            Publisher.sendMessage('statusbar.update', data='Received')
        else:
            Publisher.sendMessage('statusbar.update', data='Failed')

    def popupLog(self, event):
        window = PopoutLog(self.GetTopLevelParent(), wx.SIMPLE_BORDER)
        thread.start_new_thread(self.PopoutLog, ())
        logbutton = event.GetEventObject()
        window.Show(True)

#------------------------------------------------------------------------------------
class PopoutLog(wx.PopupWindow):
    title = 'Log'

    def __init__(self, parent, style):
        wx.PopupWindow.__init__(self, parent, style)

        panel = wx.Panel(self)
        self.panel = panel

        # Sizing
        sizer = wx.BoxSizer()
        panel.SetSizer(sizer)
        panel.Layout()

    def OnQuit(self, event):
        self.Close()

    def OpenLog(self, event):
        self.Show(True)

#------------------------------------------------------------------------------------
class IPCThread(Thread):
    def __init__(self):

        Thread.__init__(self)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.bind(('127.0.0.1', 8080))
        self.socket.listen(5)
        self.setDaemon(True)
        self.start()

# ------------------------------------------------------------------------------------
    def run(self):

        while True:
            try:
                client, addr = self.socket.accept()

                ready = select.select([client,], [], [], 2)
                if ready[0]:
                    received = client.recv(4096)
                    print received
                    wx.CallAfter(Publisher.sendMessage, 'update', received)

            except socket.error, msg:
                print 'Socket error %s' % msg
                break

        try:
            self.socket.shutdown(socket.SHUT.RDWR)
        except:
            pass

        self.socket.close()
#------------------------------------------------------------------------------------

if __name__ == '__main__':
    app = wx.App()
    app.frame = MainFrame()
    app.frame.Show()
    app.MainLoop()