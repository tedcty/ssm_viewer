import giaspcreg3
from enum import Enum
import numpy as np


class GiasArgs(Enum):
    mean = 0,
    ssm = 1,
    target = 2,
    init_rot = 3,
    fit_mode = 4,
    fit_comps = 5,
    mweight = 6,
    sample = 7,
    points_only = 8,
    fit_scale = 9,
    out = 10,
    auto_align = 11,
    view = 12,
    reg = 13,
    rms = 14


class Gias3PCFit(object):
    # This class is an object that setup the gias3 pc fit and save out the registration
    def __init__(self, mean, ssm, target, fit_mode, fit_comps, init_rot=None, mw=0.1, sample=None,
                 pts_only=False, fit_scale=False, out=None, auto_align=True, view=False):
        if init_rot is None:
            init_rot = np.deg2rad((0, 0, 0))
        self.args = {
            GiasArgs.mean: mean,
            GiasArgs.ssm: ssm,
            GiasArgs.target: target,
            GiasArgs.init_rot: init_rot,
            GiasArgs.fit_mode: fit_mode,
            GiasArgs.fit_comps: fit_comps,
            GiasArgs.mweight: mw,
            GiasArgs.sample: sample,
            GiasArgs.points_only: pts_only,
            GiasArgs.fit_scale: fit_scale,
            GiasArgs.out: out,
            GiasArgs.auto_align: auto_align,
            GiasArgs.view: view,
        }

    def fit(self):
        """
        This script skips of the command line read and parse and go directly to register
        :return: a dictionary of the reg(mesh) and rms
        """
        reg, rms = giaspcreg3.register(self.args[GiasArgs.mean], self.args[GiasArgs.ssm], self.args[GiasArgs.target],
                                       self.args[GiasArgs.init_rot], self.args[GiasArgs.fit_mode],
                                       self.args[GiasArgs.fit_comps], mw=self.args[GiasArgs.mweight],
                                       sample=self.args[GiasArgs.sample], pts_only=self.args[GiasArgs.points_only],
                                       fit_scale=self.args[GiasArgs.fit_scale], out=self.args[GiasArgs.out],
                                       auto_align=self.args[GiasArgs.auto_align], view=self.args[GiasArgs.view])
        ret = {
            GiasArgs.reg: reg,
            GiasArgs.rms: rms
               }

        return ret
