# -*- coding: utf-8 -*-
"""
Created on Tue May  5 09:33:00 2026

@author: Etienne
"""

from CPR_GUI_Handler import GUI_handler as handler
from CPR_GUI import CPR_GUI

GUI_handler = handler()
GUI = CPR_GUI(GUI_handler)
GUI.mainloop()  