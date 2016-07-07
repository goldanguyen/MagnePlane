"""
Group for Pod components containing the following components:
Cycle Group, Pod Mach (Aero), DriveTrain group, Geometry, Levitation group, and Pod Mass
"""
from openmdao.api import Component, Group, Problem
from hyperloop.Python.pod.pod_mass import PodMass
from hyperloop.Python.pod.drivetrain.drivetrain import Drivetrain
from hyperloop.Python.pod.pod_mach import PodMach
from hyperloop.Python.pod.cycle.cycle_group import Cycle
from hyperloop.Python.pod.pod_geometry import PodGeometry
from hyperloop.Python.pod.magnetic_levitation.levitation_group import LevGroup

class PodGroup(Group):
    def __init__(self):
        super(PodGroup, self).__init__()

        self.add('pod_mass', PodMass())
        self.add('drivetrain', Drivetrain())
        self.add('levitation_group', LevGroup(), promotes=['w_track', 'mag_drag', 'cost', 'w_track', 'mag_drag'])
        self.add('pod_mach', PodMach(), promotes=['p_tube', 'M_pod', 'A_tube'])
        self.add('cycle', Cycle())
        self.add('pod_geometry', PodGeometry(), promotes=['BF', 'A_payload', 'p_tunnel', 'M_diff', 'M_duct', 'T_tunnel', 'S'])

        self.connect('pod_geometry.A_pod', 'pod_mach.A_pod')
        self.connect('pod_geometry.L_pod', ['pod_mach.L', 'pod_mass.pod_len'])
        self.connect('drivetrain.motor_mass', 'pod_mass.motor_mass')
        self.connect('drivetrain.battery_mass', 'pod_mass.battery_mass')
        self.connect('drivetrain.??', 'pod_geometry.L_bat')
        self.connect('drivetrain.??', 'pod_geometry.L_motor')
        self.connect('pod_mass.pod_mass', 'levitation_group.m_pod')
        self.connect('pod_geometry.L_pod', 'levitation_group.l_pod')
        self.connect('levitation_group.mag_drag', 'pod_mass.mag_drag')
        self.connect('pod_geometry.D_pod', 'pod_mass.podgeo_d')
        self.connect('cycle.comp_mass', 'pod_mass.comp_mass')

if __name__ == "__main__":

    prob = Problem()
    root = prob.root = Group()
    root.add('Pod', PodGroup())

    params = (('p_tube', ??),
             ('M_pod', ??),
             ('BF', ??),
             ('A_payload', ??),
             ('p_tunnel', ??),
             ('M_diff', ??),
             ('M_duct', ??),
             ('T_tunnel', ??),
             ('w_track', ??))

    prob.root.add('des_vars', IndepVarComp(params))
    prob.root.connect('des_vars.p_tube', 'Pod.pod_mach.p_tube')
    prob.root.connect('des_vars.M_pod', ['Pod.pod_mach.M_pod', 'Pod.pod_geometry.M_pod'])
    prob.root.connect('des_vars.BF', 'Pod.pod_geometry.BF')
    prob.root.connect('des_vars.A_payload', 'Pod.pod_geometry.A_payload')
    prob.root.connect('des_vars.p_tunnel', 'Pod.pod_geometry.p_tunnel')
    prob.root.connect('des_vars.M_diff', 'Pod.pod_geometry.M_diff')
    prob.root.connect('des_vars.M_duct', 'Pod.pod_geometry.M_duct')
    prob.root.connect('des_vars.T_tunnel', 'Pod.pod_geometry.T_tunnel')
    prob.root.connect('des_vars.w_track', 'Pod.levitation_group.w_track')

    prob.setup()
    prob.root.list_connections()
    prob.run()

    print('Tube Temperature: %f' % prob['Tube.Thermal.tubetemp'])
    print(':%f' % prob['Cycle.'])
    print(':%f' % prob['Aero.'])
    print('%f' % prob['Geometry.'])
    print('%f' % prob['LevGroup.'])
    print('%f' % prob['Weight.'])