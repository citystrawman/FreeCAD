# ***************************************************************************
# *   Copyright (c) 2017 Bernd Hahnebach <bernd@bimstatik.org>              *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__title__ = "FreeCAD FEM solver object CalculiX"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

## @package SolverCalculix
#  \ingroup FEM

import glob
import os

import FreeCAD

from . import tasks
from .. import run
from .. import solverbase
from femtools import femutils

if FreeCAD.GuiUp:
    import FemGui

ANALYSIS_TYPES = ["static", "frequency", "thermomech", "check"]


def create(doc, name="SolverCalculiX"):
    return femutils.createObject(
        doc, name, Proxy, ViewProxy)


class Proxy(solverbase.Proxy):
    """The Fem::FemSolver's Proxy python type, add solver specific properties
    """

    Type = "Fem::SolverCalculix"

    def __init__(self, obj):
        super(Proxy, self).__init__(obj)
        obj.Proxy = self
        ccx_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/Ccx")
        add_attributes(obj, ccx_prefs)

    def createMachine(self, obj, directory, testmode=False):
        return run.Machine(
            solver=obj, directory=directory,
            check=tasks.Check(),
            prepare=tasks.Prepare(),
            solve=tasks.Solve(),
            results=tasks.Results(),
            testmode=testmode)

    def editSupported(self):
        return True

    def edit(self, directory):
        pattern = os.path.join(directory, "*.inp")
        FreeCAD.Console.PrintMessage("{}\n".format(pattern))
        f = glob.glob(pattern)[0]
        FemGui.open(f)

    def execute(self, obj):
        return


class ViewProxy(solverbase.ViewProxy):
    pass


# helper add properties, this is outside of the class to be able
# to use the attribute setter from framework solver and ccxtools solver
def add_attributes(obj, ccx_prefs):

    obj.addProperty(
        "App::PropertyEnumeration",
        "AnalysisType",
        "Fem",
        "Type of the analysis"
    )
    obj.AnalysisType = ANALYSIS_TYPES
    analysis_type = ccx_prefs.GetInt("AnalysisType", 0)
    obj.AnalysisType = ANALYSIS_TYPES[analysis_type]

    choices_geom_nonlinear = ["linear", "nonlinear"]
    obj.addProperty(
        "App::PropertyEnumeration",
        "GeometricalNonlinearity",
        "Fem",
        "Set geometrical nonlinearity"
    )
    obj.GeometricalNonlinearity = choices_geom_nonlinear
    nonlinear_geom = ccx_prefs.GetBool("NonlinearGeometry", False)
    if nonlinear_geom is True:
        obj.GeometricalNonlinearity = choices_geom_nonlinear[1]  # nonlinear
    else:
        obj.GeometricalNonlinearity = choices_geom_nonlinear[0]  # linear

    choices_material_nonlinear = ["linear", "nonlinear"]
    obj.addProperty(
        "App::PropertyEnumeration",
        "MaterialNonlinearity",
        "Fem",
        "Set material nonlinearity (needs geometrical nonlinearity)"
    )
    obj.MaterialNonlinearity = choices_material_nonlinear
    obj.MaterialNonlinearity = choices_material_nonlinear[0]

    obj.addProperty(
        "App::PropertyIntegerConstraint",
        "EigenmodesCount",
        "Fem",
        "Number of modes for frequency calculations"
    )
    noem = ccx_prefs.GetInt("EigenmodesCount", 10)
    obj.EigenmodesCount = (noem, 1, 100, 1)

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "EigenmodeLowLimit",
        "Fem",
        "Low frequency limit for eigenmode calculations"
    )
    ell = ccx_prefs.GetFloat("EigenmodeLowLimit", 0.0)
    obj.EigenmodeLowLimit = (ell, 0.0, 1000000.0, 10000.0)

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "EigenmodeHighLimit",
        "Fem",
        "High frequency limit for eigenmode calculations"
    )
    ehl = ccx_prefs.GetFloat("EigenmodeHighLimit", 1000000.0)
    obj.EigenmodeHighLimit = (ehl, 0.0, 1000000.0, 10000.0)

    help_string_IterationsThermoMechMaximum = (
        "Maximum Number of thermo mechanical iterations "
        "in each time step before stopping jobs"
    )
    obj.addProperty(
        "App::PropertyIntegerConstraint",
        "IterationsThermoMechMaximum",
        "Fem",
        help_string_IterationsThermoMechMaximum
    )
    niter = ccx_prefs.GetInt("AnalysisMaxIterations", 200)
    obj.IterationsThermoMechMaximum = niter

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "TimeInitialStep",
        "Fem",
        "Initial time steps"
    )
    ini = ccx_prefs.GetFloat("AnalysisTimeInitialStep", 1.0)
    obj.TimeInitialStep = ini

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "TimeEnd",
        "Fem",
        "End time analysis"
    )
    eni = ccx_prefs.GetFloat("AnalysisTime", 1.0)
    obj.TimeEnd = eni

    obj.addProperty(
        "App::PropertyBool",
        "ThermoMechSteadyState",
        "Fem",
        "Choose between steady state thermo mech or transient thermo mech analysis"
    )
    sted = ccx_prefs.GetBool("StaticAnalysis", True)
    obj.ThermoMechSteadyState = sted

    obj.addProperty(
        "App::PropertyBool",
        "IterationsControlParameterTimeUse",
        "Fem",
        "Use the user defined time incrementation control parameter"
    )
    use_non_ccx_iterations_param = ccx_prefs.GetInt("UseNonCcxIterationParam", False)
    obj.IterationsControlParameterTimeUse = use_non_ccx_iterations_param

    obj.addProperty(
        "App::PropertyBool",
        "SplitInputWriter",
        "Fem",
        "Split writing of ccx input file"
    )
    split = ccx_prefs.GetBool("SplitInputWriter", False)
    obj.SplitInputWriter = split

    ccx_default_time_incrementation_control_parameter = {
        # iteration parameter
        "I_0": 4,
        "I_R": 8,
        "I_P": 9,
        "I_C": 200,  # ccx default = 16
        "I_L": 10,
        "I_G": 400,  # ccx default = 4
        "I_S": None,
        "I_A": 200,  # ccx default = 5
        "I_J": None,
        "I_T": None,
        # cutback parameter
        "D_f": 0.25,
        "D_C": 0.5,
        "D_B": 0.75,
        "D_A": 0.85,
        "D_S": None,
        "D_H": None,
        "D_D": 1.5,
        "W_G": None}
    p = ccx_default_time_incrementation_control_parameter
    p_iter = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}".format(
        p["I_0"],
        p["I_R"],
        p["I_P"],
        p["I_C"],
        p["I_L"],
        p["I_G"],
        "",
        p["I_A"],
        "",
        ""
    )
    p_cutb = "{0},{1},{2},{3},{4},{5},{6},{7}".format(
        p["D_f"],
        p["D_C"],
        p["D_B"],
        p["D_A"],
        "",
        "",
        p["D_D"],
        ""
    )
    obj.addProperty(
        "App::PropertyString",
        "IterationsControlParameterIter",
        "Fem",
        "User defined time incrementation iterations control parameter"
    )
    obj.IterationsControlParameterIter = p_iter
    obj.addProperty(
        "App::PropertyString",
        "IterationsControlParameterCutb",
        "Fem",
        "User defined time incrementation cutbacks control parameter"
    )
    obj.IterationsControlParameterCutb = p_cutb

    stringIterationsUserDefinedIncrementations = (
        "Set to True to switch off the ccx automatic incrementation completely "
        "(ccx parameter DIRECT). Use with care. Analysis may not converge!"
    )
    obj.addProperty(
        "App::PropertyBool",
        "IterationsUserDefinedIncrementations",
        "Fem",
        stringIterationsUserDefinedIncrementations
    )
    obj.IterationsUserDefinedIncrementations = False

    help_string_IterationsUserDefinedTimeStepLength = (
        "Set to True to use the user defined time steps. "
        "The time steps are set with TimeInitialStep and TimeEnd"
    )
    obj.addProperty(
        "App::PropertyBool",
        "IterationsUserDefinedTimeStepLength",
        "Fem",
        help_string_IterationsUserDefinedTimeStepLength
    )
    obj.IterationsUserDefinedTimeStepLength = False

    known_ccx_solver_types = [
        "default",
        "spooles",
        "iterativescaling",
        "iterativecholesky"
    ]
    obj.addProperty(
        "App::PropertyEnumeration",
        "MatrixSolverType",
        "Fem",
        "Type of solver to use"
    )
    obj.MatrixSolverType = known_ccx_solver_types
    solver_type = ccx_prefs.GetInt("Solver", 0)
    obj.MatrixSolverType = known_ccx_solver_types[solver_type]

    obj.addProperty(
        "App::PropertyBool",
        "BeamShellResultOutput3D",
        "Fem",
        "Output 3D results for 1D and 2D analysis "
    )
    dimout = ccx_prefs.GetBool("BeamShellOutput", False)
    obj.BeamShellResultOutput3D = dimout


"""
Should there be some equation object for Calculix too.

Necessarily yes! The properties GeometricalNonlinearity,
MaterialNonlinearity, ThermoMechSteadyState might be moved
to the appropriate equation.

Furthermore the material Category should not be used in writer.
See common materila object for more information. The equation
should used instead to get this information needed in writer.
"""
