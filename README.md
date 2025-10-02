# 'multip_wins_bpc' project 
The boilerplate code for creation of GUI-based programs for image acquisition / displaying
is hosted on this repository. For making GUIs responsive, acquisition is implemented as 
threaded / lifted on the another Process script. Image update (refresh display) achieved 
commonly through asynchronous task of a main window thread.    
***'multip_wins_bpc'*** - stands for 'multiprocessing windows boilerplate code'.    

Primary used GUI library *tkinter* that is embedded in the standard Python distribution 
with the standard licensing terms for it (PSF license).      
Alternatives to *tkinter* are:   
*PyQt5* (GPL license) - in the "qt_based_ui" subfolder bundled with *pyqtgraph* for fast 
image refreshing (much faster than standard *matplotlib* update image method).     
*wxPython* (wxWindows Licence) - in the "wxpy_based_ui" subfolder.   

### Run script
For open UI, run in a console the command: ***python main_ui_mwpc.py***, 
assuming that command ***python*** launches Python console.   
Same is applicable for scripts stored in subfolders.  
