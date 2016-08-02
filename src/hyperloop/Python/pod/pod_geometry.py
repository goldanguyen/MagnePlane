from __future__ import print_function

import numpy as np
from openmdao.core.component import Component
from openmdao.api import IndepVarComp, Component, Problem, Group
class PodGeometry(Component):
    """
    Notes
    ------
    Computes to corss sectional area, length, and planform area of the pod based on the sizes of internal components
    and the necessary duct area within the pod based on compressor peformance.  Assumes isentropic compression and a 
    compressor exit mach number of .3. Also calculate blockage factors based on pressurized cylinder equations.

    Params
    ------
    A_payload : float
        Cross sectional area of passenger compartment. Default value is 2.72
    gam : float
        Ratio of specific heats. Default value is 1.4
    R : float
        Ideal gas constant. Default valut is 287 J/(m*K).
    p_tunnel : float
        Pressure of air in tube.  Default value is 850 Pa.  Value will come from vacuum component
    M_pod : float
        pod Mach number. Default value is .8. value will be set by user
    A_p : float
        Cross sectional area of passenger compartment. Default value is 2.72 m**2
    L_comp : float
        length of the compressor. Default value is 1.0 m.
    L_bat : float
        length of battery. Default value is 1.0 m.
    L_inverter : float
        length of inverter. Default value is 1.0 m.
    L_trans : float
        length of transformer. Default value is 1.0 m
    L_p : float
        length of passenger compartment. Default value is 11.2 m
    L_conv : float
        length of the converging section of the nozzle. Default value is .3 m
    L_div : float
        length of the diverging section of the nozzle. Default value is 1.5 m
    L_motor : float
        length of the motor. Default value is 1.0 m
    p_duct : float
        Static pressure in the duct. Default value is 6800.0 Pa
    p_passenger : float
        Static pressure in passenger section. Default value is 101.3e3 Pa
    rho_pod : float
        Density of pod material. Default value is 2700.0 kg/m**3
    n_passengers : float
        Number of passengers per pod. Default value is 28
    SF : float
        Structural safety factor. Default value is 1.5
    Su : float
        Ultimate strength of pod material. Default value is 50.0e6 Pa
    A_duct : float
        Area of flow duct within pod. Default value is .3 m**2
    dl_passenger : float
        Length of passenger compartment per passenger row. Default value is .8 m.
    g : float
        gravitational acceleration. Default value is 9.81 m/s**2

    Returns
    -------
    A_pod : float
        Cross sectional area of pod.
    D_pod : float
        Diameter of pod
    S : float
        Platform area of the pod
    L_pod : float
        Length of Pod
    t_passenger : float
        thickness of structure in passenger section.
    t_pod : float
        thickness of outer pod section.
    BF : float
        Pod blockage factor.
    beta : float
        Duct blockage factor.
    """

    def __init__(self):
        super(PodGeometry, self).__init__()

        self.add_param('L_comp', val=1.0, desc='Length of Compressor', units='m')
        self.add_param('L_bat', val=1.0, desc='Length of Battery', units='m')
        self.add_param('L_motor', val=1.0, desc='Length of Motor', units='m')
        self.add_param('L_inverter', val=0.0, desc='Length of Inverter', units='m')
        self.add_param('L_trans', val=1.0, desc='Length of Transformer', units='m')
        self.add_param('L_p', val=11.2, desc='Payload Length', units='m')
        self.add_param('L_conv', val=.3, desc='Converging Lenth', units='m')
        self.add_param('L_div', val=1.5, desc='Diverging Length', units='m')
        self.add_param('L_inlet', 2.5, desc = 'Inlet length', units = 'm')
        self.add_param('p_tunnel', val=850.0, desc='tunnel pressure', units='Pa')
        self.add_param('A_payload', val=2.72, desc='Cross sectional area of passenger compartment')
        self.add_param('p_duct', 6800.0, desc = 'duct pressure', units = 'Pa')
        self.add_param('p_passenger', 101.0e3, desc = 'Passenger compartment pressure', units = 'Pa')
        self.add_param('rho_pod', 2700.0, desc = 'material density', units = 'kg/m**3')
        self.add_param('n_passengers', 28., desc = 'number of passengers', units = 'unitless')
        self.add_param('dm_passenger', 166.0, desc = 'mass per passenger', units = 'kg')
        self.add_param('SF', 1.5, desc = 'safety factor for pressure cylinder', units = 'unitless')
        self.add_param('Su', 50.0e6, desc = 'ultimate strength', units = 'Pa')
        self.add_param('A_duct', .3, desc = 'tunnel pressure', units = 'm**2')
        self.add_param('dl_passenger', .8, desc = 'passenger compartment length per person', units = 'm')
        self.add_param('g', 9.81, desc = 'gravity', units = 'm/s**2')

        self.add_output('A_pod', val = 0.0, desc = 'cross sectional area of pod', units = 'm**2')
        self.add_output('D_pod', val=0.0, desc='pod diameter', units='m')
        self.add_output('S', val=0.0, desc='platform area of pod', units='m**2')
        self.add_output('L_pod', val=0.0, desc='length of pod', units='m')
        self.add_output('t_passenger', 0.0, desc = 'passenger compartment thickness', units = 'm')
        self.add_output('t_pod', 0.0, desc = 'outer pod thickness', units = 'm')
        self.add_output('BF', 0.0, desc = 'Tunnel blockage Factor', units = 'unitless')
        self.add_output('beta', 0.0, desc = 'duct blockage factor', units = 'unitless')
    
    def solve_nonlinear(self, p, u, r):

        dp_passenger = p['p_passenger'] - p['p_duct']                   #Calculate pressure differential across passenger section wall
        r_passenger = np.sqrt(p['A_payload']/np.pi)                     #Calculate radius of the passenger section
        t_passenger = (dp_passenger*r_passenger)/(p['Su']/p['SF'])      #Calculate pod thickness based on pressurized cylinder equations

        L_passenger = (p['n_passengers']*p['dl_passenger'])/2.0         #Calculate length of passenger section
        r_pod = np.sqrt((p['A_duct']+p['A_payload'])/np.pi)             #Calculate pod radius initial value for sizing

        #Calculate mass of passenger section. Factor of 1.5 is to account for structure, luggage, etc.
        m_passenger = (p['n_passengers']*p['dm_passenger']*1.5) + p['rho_pod']*np.pi*(((r_passenger+t_passenger)**2)-(r_passenger**2))*L_passenger     
        
        dx = (m_passenger*p['g'])/((p['Su']/5.0)*L_passenger)           #Calculate thickness of structure supporting passenger section according to yield condition with safety factor = 5
        A_cross = dx*(r_pod-r_passenger)                                #Calculate cross sectional area of passenger compartment support structure
        
        beta = (A_cross + np.pi*(((r_passenger+t_passenger)**2) - (r_passenger**2)))/p['A_payload']     #Calculate duct blockage factor

        dp_pod = p['p_passenger'] - p['p_tunnel']                       #Calculate pressure differntial assuming atomospheric internal pressure
        t_pod = (dp_pod*r_pod)/(p['Su']/p['SF'])                        #Calculate pod thickness based on pressurized cylinder equations
        r_pod = np.sqrt((p['A_duct']+(1.0+beta)*p['A_payload'])/np.pi)  #Calculate corrected value of pod radius to account for beta

        BF = (p['A_payload']*(1.0+beta) + p['A_duct'])/(np.pi*((r_pod+t_pod)**2.0))                     #Calculate pod blockage factor
        A_pod = (p['A_duct'] + (1+beta)*p['A_payload'])/BF              #Calculate cross sectional area of the pod
        D_pod = np.sqrt((4*A_pod)/np.pi)                                #Calculate pod diameter

        L_pod = p['L_inlet'] + p['L_comp'] + p['L_bat'] + p['L_motor'] + p['L_inverter'] + p['L_trans'] + p['L_p'] + p['L_conv'] + p['L_div']  #Calculate pod length
        S = D_pod*L_pod                                                 #Calculate pod planform area

        u['A_pod'] = A_pod
        u['D_pod'] = D_pod
        u['L_pod'] = L_pod
        u['S'] = S
        u['t_passenger'] = t_passenger
        u['t_pod'] = t_pod
        u['BF'] = BF
        u['beta'] = beta

if __name__ == '__main__':
    top = Problem()
    root = top.root = Group()

    root.add('p', PodGeometry())

    top.setup()
    top.run()

    print('\n')
    print('Pod cross section = %f m^2' % top['p.A_pod'])
    print('Pod Diameter = %f m' % top['p.D_pod'])
    print('Pod Length = %f m' % top['p.L_pod'])
    print('Pod planform area = %f m^2' % top['p.S'])
    print('Passenger compartment thickness = %f m' % top['p.t_passenger'])
    print('Pod thickness is = %f m' % top['p.t_pod'])
    print('Pod blockage factor = %f' % top['p.BF'])
    print('Duct blockage factor is = %f' % top['p.beta'])

