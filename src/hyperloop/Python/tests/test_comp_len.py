import pytest
from hyperloop.Python.pod.cycle import comp_len
import numpy as np
from openmdao.api import Group, Problem

def create_problem(component):
    root = Group()
    prob = Problem(root)
    prob.root.add('comp', component)
    return prob

class TestCompressorLength(object):

    def test_case1(self):

        component  =  comp_len.CompressorLen()
        prob = create_problem(component)
        prob.setup()

        prob['comp.h_in'] = 0.0
        prob['comp.h_out'] = 207.
        prob['comp.comp_inletArea'] = 1.287
        prob['comp.h_stage'] = 58.2
        prob.run()

        assert np.isclose(prob['comp.comp_len'], 1.562, rtol = 0.1)
