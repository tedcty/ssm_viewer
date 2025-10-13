# ssm_viewer
Due to the difficulties in getting Mayavi Visualiser to run with GIAS3, a new, simpler visualiser was developed using PySide6 and VTK to visualise SSM from GIAS3.

# Requirements
* Python >= 3.12
* MMG's PTB package
  
This viewer can be built using pyinstaller using the provided ssm3d_viewer.spec file

# Build issue
* Currently, pymeshlab has build issues with pyinstaller, which causes warnings on program start, but these can be ignored as the visualiser does not use pymeshlab at the moment. 
