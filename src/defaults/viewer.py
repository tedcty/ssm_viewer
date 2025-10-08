import copy
import platform

import pandas as pd
import vtk
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from scipy.spatial.transform import Rotation
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PySide6.QtWidgets import (QLabel, QPushButton, QGraphicsOpacityEffect, QSlider)
from PySide6.QtGui import QIcon, QPainterPath, QRegion, QPainter, QPixmap, QColor
from PySide6.QtCore import QPoint, Qt

from ptb.util.io.helper import BasicIO
from ptb.util.io.opendialog import OpenFiles
from ptb.util.data import VTKMeshUtl, TRC
from ptb.util.math.transformation import Trig, PCAModel, Cloud
from ptb.util.lang import CommonSymbols
import os
import numpy as np
import random
from src.defaults.widgets import MeshInfoWidget, InfoWidget, AngleInfoWidget
from scipy.optimize import minimize


class WorldPolyDataHelper:
    def __init__(self, world):
        self.world = world

    def __getitem__(self, arg):
        return self.world.actors[arg].GetMapper().GetInput()


class World:
    @property
    def origin_actor(self):
        return ['Origin', [self.actors['Origin']]]

    def __init__(self, frame, main_win):
        self.poly_data = WorldPolyDataHelper(self)
        self.__key_mods__ = []
        self.__other_keys__ = []
        self.control_pressed = False
        self.shift_pressed = False

        self.frame = frame
        self.central_widget = QWidget()
        # self.central_widget.setStyleSheet("border-radius: 10px;")
        self.vl = QVBoxLayout()
        self.central_widget.setLayout(self.vl)
        self.vtk_widget = QVTKRenderWindowInteractor(main_win)
        self.vl.addWidget(self.vtk_widget)
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0.25, 0.25, 0.25)
        self.vtk_widget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.vtk_widget.AddObserver(vtk.vtkCommand.KeyPressEvent, self.key_pressed)
        self.vtk_widget.AddObserver(vtk.vtkCommand.KeyReleaseEvent, self.keyrelease)
        self.vtk_widget.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, self.mouse_pressed) # here for later


        self.actors = {}
        self.axes = vtk.vtkAxesActor()
        self.axes.SetTotalLength(100, 100, 100)
        self.axes.SetNormalizedTipLength(0.2, 0.2, 0.2)

        self.axesw = vtk.vtkOrientationMarkerWidget()
        self.axesw.SetOrientationMarker(self.axes)
        self.axesw.SetInteractor(self.iren)
        self.axesw.SetViewport(0.8, 0.8, 1, 1)
        self.axesw.EnabledOn()
        self.axesw.InteractiveOff()

        self.txt = vtk.vtkTextActor()
        self.txt.SetDisplayPosition(20, 20)

        txtprop = self.txt.GetTextProperty()
        txtprop.SetFontSize(20)
        txtprop.BoldOn()
        txtprop.SetColor(0.80, 0.80, 0.80)

        self.picker = vtk.vtkPropPicker()
        self.origin = vtk.vtkAxesActor()
        self.origin.SetTotalLength(50, 50, 50)
        self.origin.SetNormalizedTipLength(0.2, 0.2, 0.2)
        self.add_actor(actor_name='Origin', actor=self.origin)

        self.style_interactor = vtk.vtkInteractorStyleTrackballCamera()
        self.vtk_widget.SetInteractorStyle(self.style_interactor)

        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

    def reset_view(self):
        self.ren.ResetCamera()
        self.vtk_widget.update()
        self.vtk_widget.focusWidget()

    def remove_actor(self, actor_name):
        try:
            a = self.actors.pop(actor_name)
            self.ren.RemoveActor(a)
            self.vtk_widget.update()
        except KeyError:
            pass

    def remove_all(self):
        keys = [a for a in self.actors]
        for a in keys:
            self.ren.RemoveActor(self.actors[a])
            self.actors.pop(a)
        self.vtk_widget.update()


    def add_actor(self, actor_name: str = None, actor: vtk.vtkActor = None, filename: str = None):
        if actor_name is not None and actor is not None:
            self.actors[actor_name] = actor
            self.ren.AddActor(self.actors[actor_name])
        elif filename is not None:
            path_elements = filename.split("\\")
            if len(path_elements) == 1:
                path_elements = filename.split("/")

            polydata = VTKMeshUtl.load(filename)
            mapper = vtk.vtkPolyDataMapper()
            if vtk.VTK_MAJOR_VERSION <= 5:
                mapper.SetInput(polydata)
            else:
                mapper.SetInputData(polydata)
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0, 100/255, 200/255)
            actor_name = path_elements[-1][:path_elements[-1].rindex(".")]
            self.actors[actor_name] = actor
            self.ren.AddActor(self.actors[actor_name])
        else:
            print("Class World > Method Add Actor > No Actor added")
        self.vtk_widget.update()
        return actor

    def start_world(self):
        self.ren.AddActor(self.txt)
        self.ren.ResetCamera()

    def mouse_pressed(self, iren, event):
        print("mouse_pressed")
        pass

    def key_pressed(self, iren, event):
        key = iren.GetKeySym()
        print("Pressed " + key)
        if key == 'Control_L' or key == 'Control_R':
            self.control_pressed = True
            self.__key_mods__.append('Control')

        elif key == 'Shift_L' or key == 'Shift_R':
            self.shift_pressed = True
            self.__key_mods__.append("Shift")
        else:
            if key not in self.__other_keys__:
                self.__other_keys__.append(key)
                print(self.__other_keys__)
        str_list = ""
        if len(self.__key_mods__) > 0:
            for i in self.__key_mods__:
                str_list += i + " + "
            str_list = str_list[:-3]
        if len(self.__other_keys__) > 0:
            str_list += ""
            if len(self.__key_mods__) > 0:
                str_list += " + "
            for i in range(0, len(self.__other_keys__)):
                str_list += self.__other_keys__[i] + " + "
            str_list = str_list[:-3]
        self.txt.SetInput(str_list)
        self.vtk_widget.update()

    def keyrelease(self, iren, event):
        key = iren.GetKeySym()
        print("Released " + key)
        try:
            if key == 'Control_L' or key == 'Control_R':
                self.control_pressed = False
                self.__key_mods__.remove("Control")

            elif key == 'Shift_L' or key == 'Shift_R':
                self.shift_pressed = False
                self.__key_mods__.remove("Shift")
            else:
                if key in self.__other_keys__:
                    self.__other_keys__.remove(key)
        except ValueError:
            pass
        str_list = ""
        if len(self.__key_mods__) > 0:
            for i in self.__key_mods__:
                str_list += i + " + "
            str_list = str_list[:-3]
        if len(self.__other_keys__) > 0:
            str_list += " + "
            for i in self.__other_keys__:
                str_list += i + " + "
            str_list = str_list[:-3]
        self.txt.SetInput(str_list)
        self.vtk_widget.update()



class ModelConnector:

    def __init__(self, world):
        self.world = world
        self.labels = {}
        self.model_name = "Model Name"


# class ForearmTest(ModelConnector):
#     def label_landmark(self, p_name, p):
#         caption_actor = vtk.vtkCaptionActor2D()
#         caption_actor.SetCaption(p_name[:-4])
#         caption_actor.SetAttachmentPoint(p)
#         caption_actor.SetPadding(20)
#         caption_actor.BorderOff()
#         text_property = caption_actor.GetTextActor().GetTextProperty()
#         text_property.SetFontSize(16)
#         caption_actor.GetTextActor().SetTextScaleModeToNone()
#         caption_actor.GetTextActor().GetTextProperty().SetColor(235.0/255.0, 223.0/255.0, 195.0/255.0)
#         self.labels[p_name+"_l"] = [caption_actor, p]
#         return p_name+"_l", caption_actor
#
#     def find_landmark(self, lm_name: str):
#         match (lm_name.lower()):
#             case self.hum_trochlea:
#                 return self.hum_trochlea
#             case self.hum_capitulum:
#                 return self.hum_capitulum
#             case self.ulna_cir:
#                 return self.ulna_cir
#             case self.ulna_carpal_art:
#                 return self.ulna_carpal_art
#             case self.ulna_styloid_process:
#                 return self.ulna_styloid_process
#             case self.ulna_trochlear_notch:
#                 return self.ulna_trochlear_notch
#         return None
#
#
#     def create_general_landmark_map(self, landmarks):
#         landmarks_maps = {}
#         files = [f for f in os.listdir(landmarks) if f.endswith('.ply') or f.endswith('.stl')]
#         for f in files:
#             landmark_name = f[:-4]
#             mesh = None
#             if landmark_name.lower().startswith('hum'):
#                 mesh = self.world.poly_data['humerus']
#             elif landmark_name.lower().startswith('rad'):
#                 mesh = self.world.poly_data['radius']
#             elif landmark_name.lower().startswith('ulna'):
#                 mesh = self.world.poly_data['ulna']
#             print(landmark_name)
#             if mesh is None:
#                 print("Mesh is none")
#                 continue
#             landmark = VTKMeshUtl.load("{0}{1}.ply".format(landmarks, landmark_name))
#             landmark_points = VTKMeshUtl.extract_points(landmark)
#
#             ht = VTKMeshUtl.closest_point_set(landmark_points, mesh)
#             ht.to_csv("{0}../maps/{1}_map.csv".format(landmarks, landmark_name), index=False)
#             landmarks_maps[landmark_name] = ht
#         return landmarks_maps
#
#     def read_landmark_map(self, landmarks):
#         da_maps = "{0}../maps/".format(landmarks)
#         landmarks_maps = {}
#         files = [f for f in os.listdir(da_maps) if f.endswith('.csv')]
#         for f in files:
#             landmark_name = f[:-4]
#             lmd = self.find_landmark(landmark_name[:-4])
#             mesh = None
#             act = None
#             if landmark_name.lower().startswith('hum'):
#                 mesh = self.world.poly_data['humerus']
#                 act = self.world.actors['humerus']
#             elif landmark_name.lower().startswith('rad'):
#                 mesh = self.world.poly_data['radius']
#                 act = self.world.actors['radius']
#             elif landmark_name.lower().startswith('ulna'):
#                 mesh = self.world.poly_data['ulna']
#                 act = self.world.actors['ulna']
#             lndmrk_dp = pd.read_csv("{0}../maps/{1}".format(landmarks, f))
#
#             lndmrk_mesh = VTKMeshUtl.sub_mesh(lndmrk_dp['idm'].to_list(), mesh)
#             mapper = vtk.vtkPolyDataMapper()
#             if vtk.VTK_MAJOR_VERSION <= 5:
#                 mapper.SetInput(lndmrk_mesh)
#             else:
#                 mapper.SetInputData(lndmrk_mesh)
#             lndmrk_actor = vtk.vtkActor()
#             lndmrk_actor.SetMapper(mapper)
#             rgb = []
#             for r in range(0, 3):
#                 rgb.append(np.round(random.random(), 3))
#
#             lndmrk_actor.GetProperty().SetColor(252/255.0, 186/255.0, 3/255.0)
#             lndmrk_mesh_points = VTKMeshUtl.extract_points(lndmrk_mesh)
#             lndmrk_mesh_point = np.mean(lndmrk_mesh_points, axis=0)
#             lndmrk_dp_mean, sphereSource0 = VTKMeshUtl.make_sphere(lndmrk_mesh_point, 10)
#             lndmrk_dp_mean.GetProperty().SetColor(152/255.0, 255/255.0, 79/255.0)
#             p_name, caption_actor = self.label_landmark(landmark_name, lndmrk_mesh_point)
#             ret = {'map': lndmrk_dp, 'poly': lndmrk_mesh, 'actor': lndmrk_actor,
#                    'points': lndmrk_mesh_points, 'sphere': lndmrk_dp_mean, "point": lndmrk_mesh_point,
#                    'label': [p_name, caption_actor], 'sphereSource': sphereSource0}
#             landmarks_maps[landmark_name] = ret
#         return landmarks_maps
#
#     @property
#     def ulna_trochlear_notch(self):
#         ret = {"label": "ulna_trochlear_notch"}
#         try:
#             ret['map'] = self.landmark_maps["ulna_trochlear_notch"]
#         except AttributeError:
#             pass
#         except KeyError:
#             pass
#         return ret
#
#     @property
#     def ulna_cir(self):
#         return {"label": "ulna_cir"}
#
#     @property
#     def ulna_styloid_process(self):
#         return {"label": "ulna_styloid_process"}
#
#     @property
#     def ulna_carpal_art(self):
#         return {"label": "ulna_carpal_art"}
#
#     @property
#     def rad_head_art_disk(self):
#         return {"label": "rad_head_art_disk"}
#
#     @property
#     def rad_ulna_notch(self):
#         return {"label": "rad_ulna_notch"}
#
#     @property
#     def rad_styloid_process(self):
#         return {"label": "rad_styloid_process"}
#
#     @property
#     def rad_carpal_art(self):
#         return {"label": "rad_carpal_art"}
#
#     @property
#     def hum_trochlea(self):
#         return {"label": "hum_trochlea"}
#
#     @property
#     def humeral_head(self):
#         return {"label": "humeral_head"}
#
#     @property
#     def hum_capitulum(self):
#         return {"label": "hum_capitulum"}
#
#     @staticmethod
#     def closest_point_on_line(point1, point2, point):
#         # Convert points to numpy arrays
#         p1 = np.array(point1)
#         p2 = np.array(point2)
#         p0 = np.array(point)
#
#         # Calculate the vector from p1 to p2
#         line_vec = p2 - p1
#
#         # Calculate the vector from p1 to p0
#         point_vec = p0 - p1
#
#         # Project point_vec onto line_vec
#         line_len = np.dot(line_vec, line_vec)
#         if line_len == 0:
#             raise ValueError("The two points defining the line cannot be the same.")
#
#         projection = np.dot(point_vec, line_vec) / line_len
#
#         # Calculate the closest point on the line
#         closest_point = p1 + projection * line_vec
#
#         return closest_point
#
#     def current_forearm_angle(self):
#         a = self.links[2]
#         b = self.links[-1]
#
#         line = self.links[1]
#         v0a = self.landmark_maps[line[0]]["point"]
#         v0b = self.landmark_maps[line[1]]["point"]
#         v1a = self.landmark_maps[a[0]]["point"]
#         v2b = self.landmark_maps[b[1]]["point"]
#         try:
#             v1p = self.closest_point_on_line(v0a, v0b, v1a)
#             v2p = self.closest_point_on_line(v0a, v0b, v2b)
#         except ValueError:
#             return
#         d0 = (v1a - v1p) / np.linalg.norm(v1a - v1p)
#         d1 = (v2b - v2p) / np.linalg.norm(v2b - v2p)
#         angle = Trig.angle_between_2_vectors(d0, d1)
#         print(angle*(180/np.pi))
#         return angle
#
#     def forearm_angle(self, x):
#         a = self.links[2]
#         b = self.links[-1]
#
#         line = self.links[1]
#         v0a = x
#         v0b = self.landmark_maps[line[1]]["point"]
#         v1a = self.landmark_maps[a[0]]["point"]
#         v2b = self.landmark_maps[b[1]]["point"]
#         v1p = self.closest_point_on_line(v0a, v0b, v1a)
#         v2p = self.closest_point_on_line(v0a, v0b, v2b)
#         d0 = (v1a - v1p) / np.linalg.norm(v1a - v1p)
#         d1 = (v2b - v2p) / np.linalg.norm(v2b - v2p)
#         angle = Trig.angle_between_2_vectors(d0, d1)
#         print(angle * (180 / np.pi))
#         return angle
#
#     def cost(self, x, target):
#         a = self.links[2]
#         b = self.links[4]
#         c = self.links[3]
#         d = self.links[5]
#
#         v1 = a[2]
#         v1b = self.landmark_maps[a[1]]["point"]
#         v2b = self.landmark_maps[b[0]]["point"]
#         diff1 = np.linalg.norm(self.landmark_maps[a[0]]["point"] - v2b)
#
#         v3 = c[2]
#         v3b = self.landmark_maps[c[1]]["point"]
#         e0 = np.linalg.norm(x - v1b) - v1   # ru
#         e1 = np.linalg.norm(x - v3b) - v3   # rr
#         e2 = np.linalg.norm(x - v2b) - diff1 # rt
#         e3 = np.linalg.norm(self.landmark_maps[d[0]]["point"] - self.landmark_maps[d[1]]["point"]) - d[2]
#         angle = self.current_forearm_angle()
#         dangle = np.abs(-angle - target)
#         er0 = (((1000*e0 + 10*e1 + 100*(e2)) / (v1 + v3 + diff1)) * np.pi)
#         err = np.sqrt(er0*er0) + dangle/np.pi
#
#         print(err)
#         return err
#
#
#
#     def __init__(self, world):
#         super().__init__(world)
#         self.model_name = 'Forearm Four-bar Model'
#         self.bone_landmark = {'radius': [self.rad_carpal_art,
#                                          self.rad_head_art_disk,
#                                          self.rad_ulna_notch,
#                                          self.rad_styloid_process],
#                               'ulna': [self.ulna_carpal_art,
#                                        self.ulna_cir,
#                                        self.ulna_styloid_process,
#                                        self.ulna_trochlear_notch]
#                               }
#         # root = 'D:/upper_limb/posed/'
#         c = os.getcwd()
#         root = '{0}/{1}'.format(c,'example/')
#         if platform.system() == 'Linux':
#             root = '/home/tree/RepoLib/sand/shapetoolsrepo/src/gui/forearm/example/'
#         # root = 'D:/Work/upper_limb/posed/'
#
#         files = [m for m in os.listdir(root) if m.endswith('.ply') or m.endswith('.stl')]
#         self.mesh_names = []
#         for f in files:
#             fid = f[:-4]
#             p = VTKMeshUtl.load(root + f)
#             mapper = vtk.vtkPolyDataMapper()
#             if vtk.VTK_MAJOR_VERSION <= 5:
#                 mapper.SetInput(p)
#             else:
#                 mapper.SetInputData(p)
#             actor = vtk.vtkActor()
#             actor.SetMapper(mapper)
#             actor.GetProperty().SetColor(224/ 255.0, 212 / 255, 168 / 255)
#             self.world.add_actor(actor_name=fid, actor=actor)
#             self.mesh_names.append([fid, fid, actor])
#
#         landmarks = "{0}landmarks/".format(root)
#         # self.create_general_landmark_map(landmarks)
#         self.landmark_maps = self.read_landmark_map(landmarks)
#
#         self.joint_landmarks_centres = ["{0}_map".format(self.hum_trochlea["label"]),
#                                         "{0}_map".format(self.rad_carpal_art["label"]),
#                                         "{0}_map".format(self.ulna_carpal_art["label"]),
#                                         "{0}_map".format(self.rad_head_art_disk["label"]),
#                                         "{0}_map".format(self.humeral_head["label"])]
#         for lm in self.landmark_maps:
#             self.world.add_actor(actor_name=lm, actor=self.landmark_maps[lm]['actor'])
#             #self.world.add_actor(actor_name=lm, actor=self.landmark_maps[lm]['label'][1])
#             if lm in self.joint_landmarks_centres:
#                 self.world.add_actor(actor_name=lm+"_sphere", actor=self.landmark_maps[lm]['sphere'])
#                 pass
#         self.links = [
#             ["{0}_map".format(self.hum_trochlea["label"]), "{0}_map".format(self.humeral_head["label"])],
#             ["{0}_map".format(self.hum_trochlea["label"]),  "{0}_map".format(self.ulna_carpal_art["label"])],
#             ["{0}_map".format(self.rad_carpal_art["label"]), "{0}_map".format(self.ulna_carpal_art["label"])],
#             ["{0}_map".format(self.rad_carpal_art["label"]), "{0}_map".format(self.rad_head_art_disk["label"])],
#             ["{0}_map".format(self.hum_trochlea["label"]), "{0}_map".format(self.rad_head_art_disk["label"])],
#             ["{0}_map".format(self.hum_capitulum["label"]), "{0}_map".format(self.rad_head_art_disk["label"])]
#         ]
#         count = 0
#         for l in self.links:
#             a = VTKMeshUtl.draw_line_between_two_points(self.landmark_maps[l[0]]["point"], self.landmark_maps[l[1]]["point"])
#             count += 1
#             d = np.linalg.norm(self.landmark_maps[l[0]]["point"] - self.landmark_maps[l[1]]["point"])
#             #print("{0} - {1}: {2}".format(l[0], l[1], d))
#             l.append(d)
#             l.append(a)
#             self.world.add_actor(actor_name="a{0}".format(count), actor=a)
#
#         self.previous_elbow_angle = self.elbow_angle()
#         self.update_landmark(['ulna', 'radius'])
#
#         self.anchor = copy.deepcopy(self.landmark_maps['{0}_map'.format(self.rad_head_art_disk['label'])]['point'])
#         # self.update_elbow(-self.previous_elbow_angle)
#
#     def update_landmark(self, bone_moved):
#         for b in bone_moved:
#             bone = self.world.actors[b].GetMapper().GetInput()
#             mesh_points = VTKMeshUtl.extract_points(bone)
#             for l in self.bone_landmark[b]:
#                 landmark = self.landmark_maps["{0}_map".format(l["label"])]
#                 try:
#                     lnkpoints = mesh_points[landmark['map']['idm'].to_list(), :]
#                 except IndexError:
#                     print(l)
#                     k = landmark['map']['idm'].to_list()
#                     ko = [l for l in k if l < mesh_points.shape[0]]
#                     lnkpoints = mesh_points[ko, :]
#                     pass
#                 lndmrk_mesh_point = np.mean(lnkpoints, axis=0)
#                 landmark["point"] = lndmrk_mesh_point
#                 landmark['label'][1].SetAttachmentPoint(lndmrk_mesh_point)
#                 VTKMeshUtl.update_poly_w_points(lnkpoints, landmark['poly'])
#                 sphereSource = vtk.vtkSphereSource()
#                 sphereSource.SetCenter(lndmrk_mesh_point[0], lndmrk_mesh_point[1], lndmrk_mesh_point[2])
#                 sphereSource.SetRadius(10)
#                 sphereSource.Update()
#                 landmark["sphereSource"] = sphereSource
#                 mapper = vtk.vtkPolyDataMapper()
#                 mapper.SetInputConnection(sphereSource.GetOutputPort())
#                 landmark["sphere"].SetMapper(mapper)
#
#     def update_sup_pro_angle(self, angle):
#         elbow = copy.deepcopy(self.previous_elbow_angle)
#         self.update_elbow(90*(np.pi/180), refresh=False)
#         angle = -angle
#         point = self.landmark_maps["{0}_map".format(self.ulna_carpal_art["label"])]['point']
#         points = np.zeros([3, 3])
#         points[:, 0] = self.landmark_maps["{0}_map".format(self.ulna_carpal_art["label"])]['point']
#         points[:, 1] = self.landmark_maps["{0}_map".format(self.rad_carpal_art["label"])]['point']
#         points[:, 2] = self.landmark_maps["{0}_map".format(self.hum_trochlea["label"])]['point']
#         old = copy.deepcopy(points)
#         #old[:, 2] = self.landmark_maps["{0}_map".format(self.rad_head_art_disk["label"])]['point']
#         old[:, 2] = self.anchor
#         points_ones = np.ones([4, 3])
#         for i in range(0, 3):
#             points_ones[:3, i] = points[:3, i] - point
#
#         norms = [np.linalg.norm(points_ones[:3, 0]), np.linalg.norm(points_ones[:3, 1]),
#                  np.linalg.norm(points_ones[:3, 2])]
#         norms[0] = 1
#
#         points_ones[:3, 0] = points_ones[:3, 0] / norms[0]
#         points_ones[:3, 1] = points_ones[:3, 1] / norms[1]
#         points_ones[:3, 2] = points_ones[:3, 2] / norms[2]
#         ref = np.array([[0, 0, 0], [0, -1, 0], [-1, 0, 0]]).T
#
#         tr = Cloud.rigid_body_transform(points_ones[:3, :3], ref)
#         points_ones0 = np.matmul(tr, points_ones)
#         r = Rotation.from_euler('xyz', [angle, 0, 0])
#         points_ones1 = np.matmul(r.as_matrix(), points_ones0[:3, :])
#         points_ones2 = copy.deepcopy(points_ones0)
#         points_ones2[:3, :] = points_ones1
#
#         x = points_ones2[:3, 1] * norms[1] + point
#         result = minimize(self.cost, x, args=(angle,), method='Powell')
#         x1 = result.x
#         # x1 = x
#         points_ones2[:3, 1] = copy.deepcopy(x1)
#         points_ones2[:3, 0] = old[:3, 2]
#         points_ones2[:3, 2] = old[:3, 0]
#         ref_0ld = copy.deepcopy(old[:3, 2])
#         old[:3, 0] = points_ones2[:3, 0]
#         old[:3, 2] = points_ones2[:3, 2]
#         points_ones2 = (points_ones2[:3, :].T - ref_0ld).T
#
#         old = (old.T - ref_0ld).T
#         tr = Cloud.rigid_body_transform(old, points_ones2[:3, :])
#         c = VTKMeshUtl.extract_points(self.world.actors["radius"])
#         cT = (c - ref_0ld).T
#         co = np.ones([4, cT.shape[1]])
#         co[:3, :] = c.T
#         co1 = np.matmul(tr[:3, :3], cT).T + ref_0ld
#         VTKMeshUtl.update_poly_w_points(co1, self.world.actors["radius"].GetMapper().GetInput())
#         self.update_landmark(['radius'])
#
#         for i in self.links:
#             v1 = i[0]
#             v2 = i[1]
#             line_source = vtk.vtkLineSource()
#             p1 = self.landmark_maps[v1]["point"]
#             p2 = self.landmark_maps[v2]["point"]
#             line_source.SetPoint1(p1[0], p1[1], p1[2])
#             line_source.SetPoint2(p2[0], p2[1], p2[2])
#             line_source.Update()
#
#             # Create a mapper
#             mapper = vtk.vtkPolyDataMapper()
#             mapper.SetInputConnection(line_source.GetOutputPort())
#             i[3].SetMapper(mapper)
#
#         self.update_elbow(elbow)
#         self.world.vtk_widget.update()
#         print("angle = {0}".format(self.current_forearm_angle()))
#         return angle
#
#
#     @property
#     def bones(self):
#         return ["Bones", [i[2] for i in self.mesh_names]]
#
#     @property
#     def landmarks(self):
#         ret = [self.landmark_maps[lm]['actor'] for lm in self.landmark_maps]
#         for lm in self.landmark_maps:
#             ret.append(self.landmark_maps[lm]['label'][1])
#         return ["Landmarks", ret]
#
#     @property
#     def chain(self):
#         ret = [lm[3] for lm in self.links]
#         for lm in self.landmark_maps:
#             ret.append(self.landmark_maps[lm]['sphere'])
#
#         return ["Kinematic Chain", ret]
#
#     def elbow_angle(self):
#         v1 = self.links[0]
#         v1_norm = self.landmark_maps[v1[1]]["point"] - self.landmark_maps[v1[0]]["point"]
#         v2 = self.links[1]
#         v2_norm = self.landmark_maps[v2[1]]["point"] - self.landmark_maps[v1[0]]["point"]
#         angle = Trig.angle_between_2_vectors(v1_norm, v2_norm)
#         print(angle*(180/np.pi))
#         return angle
#
#     def four_bar(self):
#         anchor = self.hum_trochlea
#         b0 = self.rad_head_art_disk # 3Dof
#         b1 = self.rad_ulna_notch    # 1Dof
#         b2 = self.ulna_cir          # 1Dof
#
#     def arm(self):
#         pass
#
#     def update_elbow(self, a, refresh=True):
#         # rotaton about y
#         a0 = -(a - self.previous_elbow_angle)
#         matx = np.array([self.landmark_maps[i]["point"] for i in self.joint_landmarks_centres])
#         ref = matx[0, :]
#         matx = matx - ref
#
#         forearm = matx[:-1, :].T
#         r = Rotation.from_euler('xyz', [0, a0, 0])
#         forearm1 = np.matmul(r.as_matrix(), forearm)
#         matx[:-1, :] = forearm1.T
#         matx = matx + ref
#         x = 0
#         for i in self.joint_landmarks_centres:
#             self.landmark_maps[i]["point"] = matx[x, :]
#             try:
#                 p = self.landmark_maps[i]["sphere"].center
#             except AttributeError:
#                 p = self.landmark_maps[i]["sphere"].GetPosition()
#             sphereSource = vtk.vtkSphereSource()
#             sphereSource.SetCenter(matx[x, 0], matx[x, 1], matx[x, 2])
#             sphereSource.SetRadius(10)
#             sphereSource.Update()
#             self.landmark_maps[i]["sphereSource"] = sphereSource
#             mapper = vtk.vtkPolyDataMapper()
#             mapper.SetInputConnection(sphereSource.GetOutputPort())
#             self.landmark_maps[i]["sphere"].SetMapper(mapper)
#             try:
#                 q = self.landmark_maps[i]["sphere"].center
#             except AttributeError:
#                 q = self.landmark_maps[i]["sphere"].GetPosition()
#             x += 1
#         for i in self.links:
#             v1 = i[0]
#             v2 = i[1]
#             line_source = vtk.vtkLineSource()
#             p1 = self.landmark_maps[v1]["point"]
#             p2 = self.landmark_maps[v2]["point"]
#             line_source.SetPoint1(p1[0], p1[1], p1[2])
#             line_source.SetPoint2(p2[0], p2[1], p2[2])
#             line_source.Update()
#
#             # Create a mapper
#             mapper = vtk.vtkPolyDataMapper()
#             mapper.SetInputConnection(line_source.GetOutputPort())
#
#             i[3].SetMapper(mapper)
#
#             pass
#         # self.world.vtk_widget.update()
#         # self.previous_elbow_angle = a
#         tc = self.landmark_maps["{0}_map".format(self.hum_trochlea["label"])]['point']
#         r = Rotation.from_euler('xyz', [0, a0, 0])
#
#         c = VTKMeshUtl.extract_points(self.world.actors["ulna"]) - (tc + np.array([2, 0, 0]))
#         cT = np.matmul(r.as_matrix(), c.T)
#         cn = cT.T + tc + np.array([2, 0, 0])
#         VTKMeshUtl.update_poly_w_points(cn, self.world.actors["ulna"].GetMapper().GetInput())
#
#         c = VTKMeshUtl.extract_points(self.world.actors["radius"]) - (tc + np.array([2, 0, 0]))
#         cT = np.matmul(r.as_matrix(), c.T)
#         cn = cT.T + tc + np.array([2, 0, 0])
#         VTKMeshUtl.update_poly_w_points(cn, self.world.actors["radius"].GetMapper().GetInput())
#         if refresh:
#             self.update_landmark(['ulna', 'radius'])
#             self.world.vtk_widget.update()
#         self.previous_elbow_angle = a
#         pass
#
#     def update_anchor(self):
#         self.anchor = copy.deepcopy(self.landmark_maps['{0}_map'.format(self.rad_head_art_disk['label'])]['point'])





class WorldView(QWidget):

    def __init__(self, parent, main_win):
        super().__init__()
        self.sheet = BasicIO.read_as_block("./defaults/drop_button.qss")
        self.setStyleSheet(self.sheet)
        self.app_win = main_win
        self.world = World(parent, main_win)
        vh = QVBoxLayout()
        vh.addWidget(self.world.vtk_widget)
        self.current_model = ModelConnector(self.world)
        self.setLayout(vh)

        # self.button_loc = QPoint(25, 30)
        # self.button = QPushButton("", parent=self)
        # self.button.setObjectName('drop_button')
        # self.button.setIcon(QIcon("icons/cubes.png"))
        # self.button.setFixedSize(40, 35)
        # self.button.move(self.button_loc)
        # self.button.setCheckable(True)
        # self.button.clicked.connect(self.menu_trigger)
        #
        # self.button_loc2 = QPoint(25, 70)
        # self.button2 = QPushButton("", parent=self)
        # self.button2.setObjectName('drop_button')
        # self.button2.setIcon(QIcon("icons/slider.png"))
        # self.button2.setFixedSize(40, 35)
        # self.button2.move(self.button_loc2)
        # self.button2.setCheckable(True)
        # self.button2.clicked.connect(self.menu_trigger2)
        #
        # self.button_loc3 = QPoint(25, 110)
        # self.button3 = QPushButton("", parent=self)
        # self.button3.setObjectName('drop_button')
        # self.button3.setIcon(QIcon("icons/add.png"))
        # self.button3.setFixedSize(40, 35)
        # self.button3.move(self.button_loc3)
        # self.button3.setCheckable(True)
        # self.button3.clicked.connect(self.menu_trigger3)
        #
        # self.expanded_button = WorldMenuWidget(None, self)
        # self.expanded_button.updated_meshes(self.current_model.mesh_names)
        # self.expanded_button.move(QPoint(60, 25))
        # self.expanded_button.setVisible(True)
        #
        # self.expanded_button1 = WorldMenuWidgetAngles(None, self)
        # self.expanded_button1.move(QPoint(60, 25))
        # self.expanded_button1.setVisible(True)
        # self.expanded_button1.set_angle()
        #
        # self.expanded_button2 = WorldMenuWidgetOptions(None, self)
        # self.expanded_button2.updated_meshes([self.current_model.bones, self.current_model.landmarks,
        #                                       self.world.origin_actor, self.current_model.chain])
        # self.expanded_button2.move(QPoint(60, 25))
        # self.expanded_button2.setVisible(True)

        # Create a QPixmap with the same size as the window, filled with a transparent color
        # mask = QPixmap(self.button.size())
        # mask.fill(Qt.GlobalColor.transparent)
        #
        # # Create a QPainter to draw onto the QPixmap
        # painter = QPainter(mask)
        # painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # path = QPainterPath()
        # rect_butt = self.button.rect()
        # rect_butt.setRect(2,2, 36, 33)
        # path.addRoundedRect(rect_butt, 8, 8)  # radius of the corners
        # # Draw the path onto the QPixmap
        # color = QColor()
        # color.setRgb(255, 255, 255, 255)
        # painter.fillPath(path, color)
        # painter.end()

        self.model_name_widget = HoverLabel(self, self, self.current_model.model_name)
        self.model_name_widget.setObjectName('modelnamewidget')


        # Set the QPixmap as the mask for the window
        # self.button.setMask(mask.createMaskFromColor(Qt.GlobalColor.transparent))
        # self.button2.setMask(mask.createMaskFromColor(Qt.GlobalColor.transparent))
        # self.button3.setMask(mask.createMaskFromColor(Qt.GlobalColor.transparent))
        #
        # self.menu_boo = False
        # self.closed = False
        #
        # self.expanded_button.setVisible(False)
        # self.expanded_button1.setVisible(False)
        # self.expanded_button2.setVisible(False)

        self.world.start_world()

    def make_mask(self, my_widget):
        # Create a QPixmap with the same size as the window, filled with a transparent color
        mask = QPixmap(my_widget.size())
        mask.fill(Qt.GlobalColor.transparent)

        # Create a QPainter to draw onto the QPixmap
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        rect_butt = my_widget.rect()
        radius = 8
        rect_butt.setRect(2, 2, rect_butt.width()-6, rect_butt.height()-6)
        path.addRoundedRect(rect_butt, radius, radius)  # radius of the corners
        painter.fillPath(path, Qt.GlobalColor.white)
        painter.end()
        return mask.createMaskFromColor(Qt.GlobalColor.transparent)


    def on_close(self):
        print("on closed")
        pass

    def clear_view(self):
        self.current_model = None
        self.world.remove_all()

    def add_mesh(self, file_name):
        self.world.add_actor(filename=file_name)
        self.world.reset_view()

    def reset_view(self):
        self.world.reset_view()

    def resize_ev(self, k):
        self.model_name_widget.update_pos(k)
        # p = self.model_name_widget.text()
        # print(p)
        # sizing = self.model_name_widget.get_size()
        # print(self.app_win.width)
        # w = int(sizing.width())
        # h = int(sizing.height())+50
        # print(w)
        #
        # self.model_name_widget.setFixedWidth(w)
        # self.model_name_widget.setFixedHeight(h)
        # self.button_loc4 = QPoint(int((self.app_win.width / 2)-int(w/2)), 30)
        # self.model_name_widget.move(self.button_loc4)
        #
        # self.model_name_widget.update()
        pass


    def on_focus(self):
        print("on_focus")
        self.closed = False
        self.menu_boo = False
        # self.button.setChecked(False)
        # self.button.setCheckable(True)
        # self.button.update()
        # self.button2.setChecked(False)
        # self.button2.setCheckable(True)
        # self.button2.update()
        # self.button3.setChecked(False)
        # self.button3.setCheckable(True)
        # self.button3.update()

    def menu_trigger(self):
        if self.closed:
            print("menu tigger closed")
            self.closed = False
            self.button.setChecked(False)
            return
        print(self.button.mapToGlobal(self.button.pos()))
        self.menu_boo = not self.menu_boo
        self.button.setChecked(self.menu_boo)
        p = self.button.mapToGlobal(self.button.pos())
        self.expanded_button.move(p.x() + 18, p.y() - 30)
        self.expanded_button.setVisible(self.menu_boo)
        self.model_name_widget.setVisible(True)

        print("pressed - trigger {0}".format(self.button.isChecked()))

    def menu_trigger2(self):
        if self.closed:
            print("menu tigger closed")
            self.closed = False
            self.button2.setChecked(False)
            return
        print(self.button2.mapToGlobal(self.button2.pos()))
        self.menu_boo = not self.menu_boo
        self.button2.setChecked(self.menu_boo)
        p = self.button.mapToGlobal(self.button.pos())
        self.expanded_button1.move(p.x() + 18, p.y() - 30)
        self.expanded_button1.setVisible(self.menu_boo)

        print("pressed - trigger {0}".format(self.button2.isChecked()))

    def menu_trigger3(self):
        if self.closed:
            print("menu tigger closed")
            self.closed = False
            self.button3.setChecked(False)
            return
        print(self.button.mapToGlobal(self.button.pos()))
        self.menu_boo = not self.menu_boo
        self.button3.setChecked(self.menu_boo)
        p = self.button.mapToGlobal(self.button.pos())
        self.expanded_button2.move(p.x() + 18, p.y() - 30)
        self.expanded_button2.setVisible(self.menu_boo)

        print("pressed - trigger {0}".format(self.button2.isChecked()))

    @staticmethod
    def label_landmark(p_name, p):
        caption_actor = vtk.vtkCaptionActor2D()
        caption_actor.SetCaption(p_name)
        caption_actor.SetAttachmentPoint(p)
        caption_actor.BorderOff()
        text_property = caption_actor.GetTextActor().GetTextProperty()
        text_property.SetFontSize(12)
        caption_actor.GetTextActor().SetTextScaleModeToNone()
        caption_actor.GetTextActor().GetTextProperty().SetColor(235.0 / 255.0, 223.0 / 255.0, 195.0 / 255.0)
        return p_name + "_l", caption_actor


class WorldMenuWidgetAngles(QWidget):
    def closeEvent(self, event):
        self.listener.on_focus()
        print("closed")

    def __init__(self, parent, listener):
        super().__init__(parent)
        self.listener = listener
        self.setWindowOpacity(0.65)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.blank = QLabel(self)
        self.w = 350
        self.h = 300
        self.blank.setFixedHeight(self.h)
        self.blank.setFixedWidth(self.w)
        self.setFixedWidth(self.w)
        self.setFixedHeight(self.h)
        vl = QVBoxLayout()

        self.title = QLabel(" Joint Angle {0}".format(CommonSymbols.set_square.value[0]))
        vl.addWidget(self.title)
        vl.addSpacing(5)
        self.elbow = AngleInfoWidget(self, self.listener.current_model.update_elbow, 'Elbow')
        vl.addWidget(self.elbow)
        self.forearm = AngleInfoWidget(self, self.listener.current_model.update_sup_pro_angle, 'Forearm', max_angle=180)
        vl.addWidget(self.forearm)

        vl.addStretch(5)
        self.setLayout(vl)
        self.sheet = BasicIO.read_as_block("./defaults/drop_menu.qss")
        self.setStyleSheet(self.sheet)

        # Create a QPixmap with the same size as the window, filled with a transparent color
        mask = QPixmap(self.size())
        mask.fill(Qt.transparent)

        # Create a QPainter to draw onto the QPixmap
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 16, 16)  # radius of the corners
        # Draw the path onto the QPixmap
        painter.fillPath(path, Qt.white)
        painter.end()

        # Set the QPixmap as the mask for the window
        self.setMask(mask.createMaskFromColor(Qt.transparent))
        pass


    def set_angle(self):
        self.elbow.set_angle(self.listener.current_model.elbow_angle())
        self.forearm.set_angle(self.listener.current_model.current_forearm_angle())



class WorldMenuWidgetOptions(QWidget):
    def closeEvent(self, event):
        self.listener.on_focus()
        print("closed")

    @property
    def world(self):
        return self.listener.world

    def __init__(self, parent, listener):
        super().__init__(parent)
        self.listener = listener
        self.setWindowOpacity(0.65)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.blank = QLabel(self)
        self.w = 350
        self.h = 300
        self.blank.setFixedHeight(self.h)
        self.blank.setFixedWidth(self.w)
        self.setFixedWidth(self.w)
        self.setFixedHeight(self.h)
        self.vl = QVBoxLayout()

        self.mesh_button = QPushButton("")
        self.mesh_button.setIcon(QIcon("icons/folder-open.png"))
        self.mesh_button.setFixedWidth(30)
        self.mesh_list = []
        self.vl.addWidget(QLabel(" Options {0}".format(CommonSymbols.command.value[0])))

        self.vl.addStretch(5)
        self.setLayout(self.vl)
        self.sheet = BasicIO.read_as_block("./defaults/drop_menu.qss")
        self.setStyleSheet(self.sheet)

        # Create a QPixmap with the same size as the window, filled with a transparent color
        mask = QPixmap(self.size())
        mask.fill(Qt.transparent)

        # Create a QPainter to draw onto the QPixmap
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 16, 16)  # radius of the corners
        # Draw the path onto the QPixmap
        painter.fillPath(path, Qt.white)
        painter.end()

        # Set the QPixmap as the mask for the window
        self.setMask(mask.createMaskFromColor(Qt.transparent))
        pass

    def updated_meshes(self, mesh_list, append=False):
        if not append:
            for i in self.mesh_list:
                self.vl.removeWidget(i)

        self.mesh_list = []
        for m in mesh_list:
            self.mesh_list.append(InfoWidget(self, m[0], m[1]))
        ixd = 1
        for i in self.mesh_list:
            self.vl.insertWidget(ixd, i)
            ixd += 1



class WorldMenuWidget(QWidget):
    def closeEvent(self, event):
        self.listener.on_focus()
        print("closed")

    @property
    def world(self):
        return self.listener.world

    def __init__(self, parent, listener):
        super().__init__(parent)
        self.listener = listener
        self.setWindowOpacity(0.65)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.blank = QLabel(self)
        self.w = 350
        self.h = 300
        self.blank.setFixedHeight(self.h)
        self.blank.setFixedWidth(self.w)
        self.setFixedWidth(self.w)
        self.setFixedHeight(self.h)
        self.vl = QVBoxLayout()

        self.mesh_button = QPushButton("")
        self.mesh_button.setIcon(QIcon("icons/folder-open.png"))
        self.mesh_button.setFixedWidth(30)
        self.mesh_list = []
        self.vl.addWidget(QLabel(" Mesh {0}".format(CommonSymbols.hammer.value[0])))
        for i in self.mesh_list:
            self.vl.addWidget(i)

        self.marker_button = QPushButton("")
        self.marker_button.setIcon(QIcon("icons/folder-open.png"))
        self.marker_button.setFixedWidth(30)

        self.vl.addStretch(5)
        self.setLayout(self.vl)
        self.sheet = BasicIO.read_as_block("./defaults/drop_menu.qss")
        self.setStyleSheet(self.sheet)
        self.mesh_button.clicked.connect(self.mesh_load_trigger)

        # Create a QPixmap with the same size as the window, filled with a transparent color
        mask = QPixmap(self.size())
        mask.fill(Qt.transparent)

        # Create a QPainter to draw onto the QPixmap
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 16, 16)  # radius of the corners
        # Draw the path onto the QPixmap
        painter.fillPath(path, Qt.white)
        painter.end()

        # Set the QPixmap as the mask for the window
        self.setMask(mask.createMaskFromColor(Qt.transparent))
        pass

    def valuechange(self):
        print(self.ml.value())
        self.ml_button.setText('{0}{1}'.format(self.ml.value(), CommonSymbols.Degrees.value[0]))
        vp = np.deg2rad(float(self.ml.value()))
        print(vp)
        self.listener.current_model.update_elbow(vp)

    def updated_meshes(self, mesh_list, append=False):
        if not append:
            for i in self.mesh_list:
                self.vl.removeWidget(i)

        self.mesh_list = []
        for m in mesh_list:
            self.mesh_list.append(MeshInfoWidget(self, m[0], m[1], m[2]))
        ixd = 1
        for i in self.mesh_list:
            self.vl.insertWidget(ixd, i)
            ixd += 1

    def mesh_load_trigger(self):
        print("load mesh")
        of = OpenFiles()
        file_filter = 'Mesh (*.stl *.ply);; All File (*.*)'
        the_mesh = of.get_file(file_filter)
        print(the_mesh)
        if the_mesh is not None:
            self.listener.clear_view()
            self.listener.add_mesh(the_mesh)
            mesh_name = os.path.split(the_mesh)
            self.mhl.setText("Mesh: {0}".format(mesh_name[1]))

class HoverLabel(QWidget):
    def closeEvent(self, event):
        self.listener.on_focus()
        print("closed")

    @property
    def world(self):
        return self.listener.world

    def text(self):
        return self.labe.text()

    def get_size(self):
        return self.labe.fontMetrics().boundingRect(self.labe.text())

    def __init__(self, parent, listener, text):
        super().__init__(parent)
        self.listener = listener
        self.labe = QLabel(self)
        self.labe.setText(text)
        self.setObjectName("model_name123")
        k = self.size()

        s = self.labe.font()
        s.setPointSize(18)
        s.setBold(True)
        self.labe.setFont(s)
        self.labe.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )

        sizing = self.labe.fontMetrics().boundingRect(self.labe.text().strip())
        w = int(sizing.width()+k.width()/2.0)
        h = int(sizing.height()+k.height())

        self.setFixedWidth(w)
        self.setFixedHeight(h)

        self.vl = QVBoxLayout()
        self.vl.addWidget(self.labe)
        self.setLayout(self.vl)
        self.button_loc4 = QPoint(int((self.listener.app_win.width / 2.0)-w/2.0 - 0.1*w), 0)
        self.move(self.button_loc4)
        self.setMask(self.make_mask())
        self.setVisible(True)

    def update_pos(self, app_k):
        sizing = self.labe.fontMetrics().boundingRect(self.labe.text().strip())
        k = self.size()
        w = int(np.round((sizing.width() + k.width() / 2.0 + 0.15*k.width()), 0))
        h = int(sizing.height() + k.height())

        # self.setFixedWidth(w)
        # self.setFixedHeight(h)

        # self.vl = QVBoxLayout()
        # self.vl.addWidget(self.labe)
        # self.setLayout(self.vl)
        print(app_k.width() / 2)
        w0 = np.round((app_k.width() / 2.0) - (w / 2.0), 0 ) + 20
        self.button_loc4 = QPoint(int(w0), 0)
        self.move(self.button_loc4)
        self.setMask(self.make_mask())
        self.update()

    def make_mask(self):
        # Create a QPixmap with the same size as the window, filled with a transparent color
        mask = QPixmap(self.size())
        mask.fill(Qt.GlobalColor.transparent)

        # Create a QPainter to draw onto the QPixmap
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        rect_butt = self.rect()
        radius = 10
        rect_butt.setRect(10, 0, rect_butt.width()-20, rect_butt.height()-10)
        path.addRoundedRect(rect_butt, radius, radius)  # radius of the corners
        painter.fillPath(path, Qt.GlobalColor.white)
        painter.end()
        return mask.createMaskFromColor(Qt.GlobalColor.transparent)

