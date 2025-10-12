import numpy as np
from ptb.util.lang import milli
import os
import pandas as pd


class ShapeModel:
    def __init__(self, pc: str = None):
        st = milli()
        if pc is not None and pc.endswith(".pc.npz") or pc.endswith(".pc"):
            s = np.load(pc, encoding='bytes', allow_pickle=True)
        else:
            return
        self.mean = s['mean']
        self.weights = s['weights']  # PC weights are variance
        self.modes = s['modes']
        self.SD = None      # Not always present
        try:
            self.SD = s['SD']
        except ValueError:
            pass

        self.projectedWeights = None # Not always present
        try:
            self.projectedWeights = s['projectedWeights']
        except ValueError:
            pass

        en = milli()
        print("time to for mapping pcs: {0} msec".format(en - st))
        print()

    def reconstruct_diff_all(self, sd, add_mean=False):
        w = np.atleast_2d(sd * np.sqrt(self.weights))
        m = np.dot(w, self.modes.T)
        me = m.T
        if add_mean:
            me = m + self.mean
        mesh = np.reshape(me, [int(self.mean.shape[0] / 3), 3])
        return mesh

    def reconstruct_diff(self, pc, sd=0, part=None, debug=False, add_mean=False):
        if part is None:
            return None
        w = sd * np.sqrt(self.weights[pc])
        m = w * self.modes[:, pc]
        me = m
        if add_mean:
            me = m + self.mean
        mesh = np.reshape(me, [int(self.mean.shape[0] / 3), 3])
        export = mesh[part["idm"].to_list(), :]
        if debug:
            if not os.path.exists("./meshes/temp/"):
                os.makedirs("./meshes/temp/")
            ms = pd.DataFrame(data=export, columns=["x", "y", "z"])
            ms.to_csv("./default_meshes/temp/part_cloud.csv", index=False)

        return export



    # def create_part(self, color, force_build, mean_mesh, part_map):
    #     mesh = np.reshape(self.mean, [int(self.mean.shape[0] / 3), 3])
    #     part = mesh[part_map, :]
    #     new_shape = None
    #     if force_build or not os.path.exists(mean_mesh):
    #         new_shape = self.extract_parts(part_map)
    #         # Write the mesh to file "*.ply"
    #         w = vtk.vtkPLYWriter()
    #         w.SetInputData(new_shape[0])
    #         w.SetFileName(mean_mesh)
    #         w.Write()
    #     if force_build:
    #         polydata = new_shape[0]
    #     else:
    #         reader = vtk.vtkPLYReader()
    #         reader.SetFileName(mean_mesh)
    #         reader.Update()
    #         polydata = reader.GetOutput()
    #     mapper = vtk.vtkPolyDataMapper()
    #     if vtk.VTK_MAJOR_VERSION <= 5:
    #         # mapper.SetInput(reader.GetOutput())
    #         mapper.SetInput(polydata)
    #     else:
    #         mapper.SetInputData(polydata)
    #     actor = vtk.vtkActor()
    #     actor.SetMapper(mapper)
    #     actor.GetProperty().SetColor(color[0], color[1], color[2])
    #     return {Keywords.actor: actor, Keywords.polydata: polydata, Keywords.vertices: part}
    #
    # @staticmethod
    # def clean_poly_data(polydata):
    #
    #     # Create a vtkCleanPolyData filter
    #     clean_filter = vtk.vtkCleanPolyData()
    #     clean_filter.SetInputData(polydata)
    #
    #     # Update the filter to remove duplicate points
    #     clean_filter.Update()
    #
    #     # Get the cleaned polydata output
    #     cleaned_polydata = clean_filter.GetOutput()
    #
    #     return cleaned_polydata
    #
    # def extract_parts(self, node_id_list, export_vert=True):
    #     mesh_data_copy = vtk.vtkPolyData()
    #     mesh_org = self.mean_mesh['polydata']
    #     mesh_data_copy.DeepCopy(mesh_org)
    #     cell_data = mesh_data_copy.GetPolys()
    #     vertices = None
    #     if export_vert:
    #         # Get the point data and cell data of the mesh
    #         points_l = []
    #         for i in range(len(node_id_list)):
    #             p = mesh_data_copy.GetPoint(node_id_list[i])
    #             points_l.append(p)
    #         vertices = np.array(points_l)
    #
    #     for i in range(cell_data.GetNumberOfCells()):
    #         cell = mesh_data_copy.GetCell(i)
    #         p1 = cell.GetPointId(0)
    #         p2 = cell.GetPointId(1)
    #         p3 = cell.GetPointId(2)
    #         if not (p1 in node_id_list and p2 in node_id_list and p3 in node_id_list):
    #             mesh_data_copy.DeleteCell(i)
    #     mesh_data_copy.RemoveDeletedCells()
    #
    #     return [mesh_data_copy, vertices]