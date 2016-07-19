from openmdao.api import Group, Problem, IndepVarComp, ScipyGMRES

from hyperloop.Python.tube.tube_vacuum import Vacuum
from hyperloop.Python.tube.tube_wall_temp import TubeTemp, TempBalance
from hyperloop.Python.tube.tube_and_pylon import TubeAndPylon
from hyperloop.Python.tube.propulsion_mechanics import PropulsionMechanics
from hyperloop.Python.tube.tube_power import TubePower

class TubeGroup(Group):
    """
    Group containing tube components

    Components
    ----------
    Vacuum : Vacuum
    Tube Temperature/Thermal Conditions : TempBalance, TubeWallTemp
    Structural : TubeAndPylon
    Propulsion Mechanics : PropulsionMechanics
    Tube Power Requirements : TubePower

    Params
    ------
    tube_length : float
        Total length of tube from Mission (m)
    tube_area : float
        Cross sectional area of tube from Pod Mach (m)
    pressure_initial : float
        initial Pressure before the pump down . Default value is 760.2.
    pressure_final : float
        Desired pressure within tube. Default value is 7.0.
    speed : float
        Pumping speed. Default value is 163333.3.
    pwr : float
        Motor rating. Default value is 18.5.
    electricity_price : float
        Cost of electricity per kilowatt hour. Default value is 0.13.
    time_down : float
        Desired pump down time. Default value is 300.0.
    gamma : float
        Operational percentage of the pump per day. Default value is 0.8.
    pump_weight : float
        Weight of one pump. Default value is 715.0.
    tube_thickness : float
        Thickness of tube in m. Default value is .05
    length_tube : float
        Length of the entire Hyperloop tube (m)
    num_pods : int
        Number of Pods in the Tube at a given time
    nozzle_air_W : float
        mass flow rate of the air exiting the pod nozzle (kg/s)
    nozzle_air_Cp : float
        specific heat of the air exiting the pod nozzle
    nozzle_air_T : float
        temp of the air exiting the pod nozzle (K)
    p_tunnel : float
        Pressure of air in tube.  Default value is 850 Pa.  Value will come from vacuum component
    m_pod : float
        Total weight of pod from pod_mass (kg)
    h : float
        Height of each pylon. Default value is 10 m.
    p_tube : float
        Pressure of air in tube.  Default value is 100 Pa.  Value will come from vacuum component
    R : float
        Ideal gas constant. Default valut is 287 J/(m*K).
    T_ambient : float
        Tunnel ambient temperature. Default value is 298 K.
    g : float
        Gravitational acceleration. Default value is 9.81 m/s**2
    vf : float
        Top pod speed after boosting section. Default value is 335 m/s. Value will be taken from aero module
    vo : float
        Speed of pod when it enters boosting section. Default value is 324 m/s.
    m_pod : float
        total mass of pod. Default value is 3100 kg. Value will come from weight component
    eta : float
        Efficiency of propulsion system. Default value is .8. value will come from propulsion module.
    Cd : float
        Drag coefficient of pod.  Default value is .2. More accurate results will come from CFD
    S : float
        Reference area of the pod. Default value is 1.4 m**2. Value will be pulled from geometry module
    D_mag : float
        Drag force from magnetic levitation in N. Default value is 150 N.  Value will come from levitation analysis
    nozzle_thrust : float
        Thrust produced by pod compressed air. Default value 21473.92 N. Will pull value from flow_path.py
    ram_drag : float
        Drag produced by inlet ram pressure. Default value is 7237.6
    num_thrust : float
        Number of propulsion thrusts required for trip (unitless)
    time_thrust : float
        Time required to accelerate pod to 1G (s)
    elec_price : float
        Cost of electricity per kiloWatt-hour (USD/(kW*h))

    Returns
    -------
    temp_boundary : float
        Ambient temperature inside tube (K)
    """

    def __init__(self):
        super(TubeGroup, self).__init__()

        #Adding in components to Tube Group
        self.add('Vacuum', Vacuum(), promotes=['tube_area',
                                               'tube_length',
                                               'pressure_initial',
                                               'pressure_final',
                                               'pwr',
                                               'speed',
                                               'electricity_price',
                                               'time_down',
                                               'gamma',
                                               'pump_weight'])

        self.add('Temp',TubeTemp(), promotes=['length_tube',
                                              'tube_area', #need to change radius_outer_tube
                                              'nozzle_air_W',
                                              'nozzle_air_Tt',
                                              'nozzle_air_Cp',
                                              'num_pods',
                                              'temp_boundary'
                                              ])

        #self.add('TempBalance',TempBalance(), promotes=['temp_boundary'])

        self.add('Struct', TubeAndPylon(), promotes=['p_tunnel',
                                                     'm_pod',
                                                     'tube_area',
                                                     'h'])
        self.add('PropMech', PropulsionMechanics(), promotes=['p_tube',
                                                              'vf',
                                                              'v0',
                                                              'm_pod',
                                                              'Cd',
                                                              'S',
                                                              'D_mag',
                                                              'nozzle_thrust',
                                                              'ram_drag'])
        self.add('TubePower', TubePower(), promotes=['num_thrust',
                                                     'elec_price',
                                                     'time_thrust'])

        #Connects vacuum outputs to downstream components
        self.connect('Vacuum.weight_tot', 'Struct.vac_weight')
        self.connect('Vacuum.pwr_tot', 'TubePower.vac_power')
        self.connect('Vacuum.energy_tot', 'TubePower.vac_energy_day')

        #Connects tube_wall_temp outputs to downstream components
        self.connect('temp_boundary', 'PropMech.T_ambient')
        self.connect('temp_boundary', 'TubePower.tube_temp')

        #Connects propulsion_mechanics outputs to downstream components
        self.connect('PropMech.pwr_req', 'TubePower.prop_power')

        self.ln_solver = ScipyGMRES()


if __name__ == "__main__":

    top = Problem()
    top.root = Group()
    top.root.add('TubeGroup', TubeGroup())

    params = (('tube_area', 40.0, {'units': 'm**2'}),
              ('tube_length', 482803.0, {'units': 'm'}),
              ('nozzle_air_W',1.08, {'units': 'kg/s'}),
              ('nozzle_air_Tt',1710.0, {'units': 'K'}),
              ('nozzle_air_Cp',0.24, {'units': 'kJ/kg/degK'}),
              ('num_pods',34, {'units': 'unitless'}),
              ('p_tunnel',100.0, {'units': 'Pa'}),
              ('m_pod', 3100.0, {'units': 'kg'}),
              ('h', 10.0, {'units': 'm'}),
              ('p_tube',100.0, {'units': 'Pa'}),
              ('vf',335.0, {'units': 'm/s'}),
              ('v0',324.0, {'units': 'm/s'}),
              ('Cd', 0.2, {'units': 'm'}),
              ('S', 1.4, {'units': 'm**2'}),
              ('D_mag', 150.0, {'units': 'N'}),
              ('nozzle_thrust', 3500.0, {'units': 'N'}),
              ('ram_drag',7237.6, {'units': 'N'}),
              ('num_thrust',5.0, {'units': 'unitless'}),
              ('elec_price',0.13, {'units': 'USD/kW/h'}),
              ('time_thrust',1.5, {'units': 's'}),
              )

    top.root.add('des_vars',IndepVarComp(params))
    top.root.connect('des_vars.tube_area', 'TubeGroup.tube_area')
    top.root.connect('des_vars.tube_length', 'TubeGroup.tube_length')  #to Vacuum
    top.root.connect('des_vars.tube_length','TubeGroup.length_tube')  #to TubeTemp
    top.root.connect('des_vars.nozzle_air_W', 'TubeGroup.nozzle_air_W')
    top.root.connect('des_vars.nozzle_air_Tt', 'TubeGroup.nozzle_air_Tt')
    top.root.connect('des_vars.nozzle_air_Cp', 'TubeGroup.nozzle_air_Cp')
    top.root.connect('des_vars.num_pods', 'TubeGroup.num_pods')
    top.root.connect('des_vars.p_tunnel', 'TubeGroup.p_tunnel')
    top.root.connect('des_vars.m_pod','TubeGroup.m_pod')
    top.root.connect('des_vars.h','TubeGroup.h')
    top.root.connect('des_vars.p_tube', 'TubeGroup.p_tube')
    top.root.connect('des_vars.vf', 'TubeGroup.vf')
    top.root.connect('des_vars.v0', 'TubeGroup.v0')
    top.root.connect('des_vars.Cd','TubeGroup.Cd')
    top.root.connect('des_vars.S','TubeGroup.S')
    top.root.connect('des_vars.D_mag','TubeGroup.D_mag')
    top.root.connect('des_vars.nozzle_thrust','TubeGroup.nozzle_thrust')
    top.root.connect('des_vars.ram_drag','TubeGroup.ram_drag')
    top.root.connect('des_vars.num_thrust', 'TubeGroup.num_thrust')
    top.root.connect('des_vars.elec_price', 'TubeGroup.elec_price')
    top.root.connect('des_vars.time_thrust', 'TubeGroup.time_thrust')

    top.setup()
    # from openmdao.api import view_tree
    # view_tree(top)
    # exit()
    top.root.list_connections()
    top.run()

    # print('\n')
    # print('Vacuum.weight_tot:%f' % top['TubeGroup.Vacuum.weight_tot'])
    # print('Struct.vac_weight: %f' % top['TubeGroup.Struct.vac_weight'])
    #
    # print('temp_boundary: %f' %top['TubeGroup.temp_boundary'])
    # print('PropMech.T_ambient: %f' % top['TubeGroup.PropMech.T_ambient'])
    # print('TubePower.tube_temp: %f' % top['TubeGroup.TubePower.tube_temp'])
    #
    # print('Vacuum.pwr_tot %f' % top['TubeGroup.Vacuum.pwr_tot'])
    # print('TubePower.vac_power: %f' % top['TubeGroup.TubePower.vac_power'])
    # print('PropMech.pwr_req: %f' % top['TubeGroup.PropMech.pwr_req'])
    # print('TubePower.prop_power: %f' % top['TubeGroup.TubePower.prop_power'])

    print('\n')
    print('Total Tube Power [kW]: %f' % top['TubeGroup.TubePower.tot_power'])
    print('Tube Temp [K]: %f' % top['TubeGroup.temp_boundary'])
