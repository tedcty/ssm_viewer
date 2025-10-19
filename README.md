# ssm_viewer
Due to the difficulties in getting Mayavi Visualiser to run with GIAS3, a new, simpler visualiser was developed using PySide6 and VTK to visualise SSM from GIAS3.

![ssm viewer beta 0.1.0](https://github.com/tedcty/mmg-doco/blob/main/Resources/Images/Screenshot%202025-10-20%20093206(ssm_viewer_beta_0.1.0).png)

# Requirements
* Python >= 3.12
* MMG's PTB package
  
This viewer can be built using pyinstaller using the provided ssm3d_viewer.spec file

# Build issue
* Currently, pymeshlab has build issues with pyinstaller, which causes warnings on program start, but these can be ignored as the visualiser does not use pymeshlab at the moment. 
