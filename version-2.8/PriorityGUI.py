# -*- coding: utf-8 -*-

import wx
import os.path

from sys import maxint

import DragList

class PriorityGUI(wx.Frame):

	def __init__(self, parent, id, title, priorityList):
		wx.Frame.__init__(self, parent, id, title, size = (250, 300), style = wx.FRAME_NO_WINDOW_MENU|wx.DEFAULT_FRAME_STYLE|wx.CLOSE_BOX| wx.STAY_ON_TOP)

		icon = wx.EmptyIcon()
		icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, "priority.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(icon)

		panel = wx.Panel(self, -1)
		
		### ------------------------------------------------------------------
		#self.listCtrl = DragList.DragList(panel, style = wx.LC_ICON|wx.LC_AUTOARRANGE)
		
		#il = wx.ImageList(16, 16, True)
		#il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16)))

		#self.listCtrl.AssignImageList(il, wx.IMAGE_LIST_NORMAL)
		
		self.listCtrl = DragList.DragList(panel, style = wx.LC_LIST)
		
		# append to list
		for item in priorityList:
			#self.listCtrl.InsertImageStringItem(maxint,item,0)
			self.listCtrl.InsertStringItem(maxint, item)
		
		self.listCtrl.SetToolTipString(_('Drag and drop a model in order to define its priority'))
		
		### id list not empty, first item is slelected
		if self.listCtrl.GetItemCount():
			self.listCtrl.Select(0,1)
		
		### -------------------------------------------------------------------
		
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		
		up_btn = wx.Button(panel, wx.ID_UP)
		down_btn = wx.Button(panel, wx.ID_DOWN)
		apply_btn = wx.Button(panel, wx.ID_APPLY)
		
		up_btn.Enable(self.listCtrl.GetItemCount() != 0)
		down_btn.Enable(self.listCtrl.GetItemCount() != 0)
		
		hbox.Add(up_btn,1)
		hbox.Add(down_btn,1)
		hbox.Add(apply_btn,1)
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.listCtrl, 1, wx.EXPAND | wx.ALL , 5)
		vbox.Add(hbox, 0, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, 5)
		
		panel.SetSizer(vbox)

		self.Bind(wx.EVT_BUTTON, self.OnApply, id=wx.ID_APPLY)
		self.Bind(wx.EVT_BUTTON, self.OnUp, id=wx.ID_UP)
		self.Bind(wx.EVT_BUTTON, self.OnDown, id=wx.ID_DOWN)
		
		self.Center()
		
	def OnApply(self, evt):
		self.Close()
	
	def GetSelectedItems(self):
		"""    Gets the selected items for the list control.
		Selection is returned as a list of selected indices,
		low to high.
		"""
		selection = []
		index = self.listCtrl.GetFirstSelected()
		if index != -1:
			selection.append(index)
			
		while len(selection) != self.listCtrl.GetSelectedItemCount():
			index = self.listCtrl.GetNextSelected(index)
			selection.append(index)

		return selection
          
	def OnUp(self, evt):
		""" Allow up moving for selected items.
		"""
		
		for pos in self.GetSelectedItems():
			item = self.listCtrl.GetItem(pos)
			current_item = item
			
			new_pos = pos-1 if pos != 0 else self.listCtrl.GetItemCount()-1
	
			current_item.SetId(new_pos)
			self.listCtrl.DeleteItem(pos)
			self.listCtrl.InsertItem(item)
			self.listCtrl.SetItemState(new_pos, 1, wx.LIST_STATE_SELECTED)
			self.listCtrl.Select(new_pos,1)
				
	def OnDown(self, evt):
		""" Allow down moving for selected items.
		"""
		
		for pos in self.GetSelectedItems():
			item = self.listCtrl.GetItem(pos)
			current_item = item
			
			new_pos = pos+1 if pos != self.listCtrl.GetItemCount()-1 else 0
				
			current_item.SetId(new_pos)
			self.listCtrl.DeleteItem(pos)
			self.listCtrl.InsertItem(item)
			self.listCtrl.SetItemState(new_pos, 1, wx.LIST_STATE_SELECTED)
			self.listCtrl.Select(new_pos,1)

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""
	
	def OnInit(self):
		
		
		import __builtin__
		import gettext
		
		__builtin__.__dict__['ICON_PATH_16_16']=os.path.join('icons','16x16')
		__builtin__.__dict__['_'] = gettext.gettext
		
		frame = PriorityGUI(None, -1, "Test", ['TOTO', 'TITI'])
		frame.Show()
		return True
	
	def OnQuit(self, event):
		self.Close()
		
if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()	