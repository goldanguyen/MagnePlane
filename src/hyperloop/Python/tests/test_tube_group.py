import pytest
from openmdao.api import Group, Problem

from hyperloop.Python.tube import tube_group
import numpy as np

def create_problem(GroupName):
    root = Group()
    prob = Problem(root)
    prob.root.add('comp', GroupName)
    return prob

class TestTube(object):
    def test_case1(self):

        TubeGroup = tube_group.TubeGroup()
        prob = create_problem(TubeGroup)
        prob.setup()
        # prob.root.list_connections()

        #Tube Inputs

        prob['comp.tube_area'] = 40.0
        prob['comp.tube_length'] = 482803.0
        prob['comp.tube_thickness'] = .05
        prob['comp.nozzle_air_W'] = 34.0
        prob['comp.nozzle_air_Tt'] = 34.0
        prob['comp.nozzle_air_Cp'] = 34.0
        prob['comp.num_pods'] = 34
        prob['comp.p_tunnel'] = 100.0
        prob['comp.m_pod'] = 3100.0
        prob['comp.h'] = 10.0
        prob['comp.p_tube'] = 100.0
        prob['comp.vf'] = 335.0
        prob['comp.v0'] = 324.0
        prob['comp.Cd'] = 0.2
        prob['comp.S'] = 1.4
        prob['comp.D_mag'] = 150.0
        prob['comp.nozzle_thrust'] = 3500.0
        prob['comp.ram_drag'] = 7237.6
        prob['comp.num_thrust'] = 5.0
        prob['comp.elec_price'] = 0.13
        prob['comp.time_thrust'] = 1.5


        prob.run()



        # Print Statement for debugging
        """
        print('Vacuum.weight_tot:%f' % prob['comp.Vacuum.weight_tot'])
        print('Struct.vac_weight: %f' % prob['comp.Struct.vac_weight'])
        print('Vacuum.tot_pwr %f' % prob['comp.Vacuum.tot_pwr'])
        print('TubePower.vac_power: %f' % prob['comp.TubePower.vac_power'])
        print('PropMech.pwr_req: %f' % prob['comp.PropMech.pwr_req'])
        print('Total Tube Power: %f' % prob['comp.TubePower.tot_power'])
        """

        # Test Values
        assert np.isclose(prob['comp.TubePower.tot_power'],70717.59714, rtol=.01)
        assert np.isclose(prob['comp.temp_boundary'],322.259085, rtol=.01)


        assert np.isclose(prob['comp.Vacuum.weight_tot'], 2641961.2538 , rtol=.01)
        assert np.isclose(prob['comp.Struct.vac_weight'], 2641961.2538, rtol=.01)
        assert np.isclose(prob['comp.Vacuum.pwr_tot'], 68358.4380, rtol=.01)
        assert np.isclose(prob['comp.TubePower.vac_power'], 68358.4380, rtol=.01)
        assert np.isclose(prob['comp.PropMech.pwr_req'], 471831.821693, rtol=.01)
        assert np.isclose(prob['comp.TubePower.tot_power'], 471831.821693, rtol=.01)
