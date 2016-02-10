import numpy as np

from openmdao.core.group import Group, Component, IndepVarComp
from openmdao.solvers.newton import Newton
from openmdao.solvers.scipy_gmres import ScipyGMRES
from openmdao.units.units import convert_units as cu
from openmdao.api import Problem

from pycycle.components import Compressor, Shaft, FlowStart, Inlet, Nozzle, Duct, FlightConditions
from pycycle.species_data import janaf
from pycycle.connect_flow import connect_flow
from pycycle.constants import AIR_FUEL_MIX, AIR_MIX
from pycycle.constants import R_UNIVERSAL_ENG, R_UNIVERSAL_SI

from openmdao.solvers.ln_gauss_seidel import LinearGaussSeidel
from openmdao.solvers.ln_direct import DirectSolver

class CompressionCycle(Group):
    """A group that models an inlet->compressor->duct->nozzle->shaft"""

    def __init__(self):
        super(CompressionCycle, self).__init__()

        # initiate components
        #self.add('fc', FlightConditions())
        self.add('fl_start', FlowStart(thermo_data=janaf, elements=AIR_MIX))
        self.add('inlet', Inlet(thermo_data=janaf, elements=AIR_MIX))
        self.add('comp', Compressor(thermo_data=janaf, elements=AIR_MIX))
        self.add('duct', Duct(thermo_data=janaf, elements=AIR_MIX))
        self.add('nozzle', Nozzle(thermo_data=janaf, elements=AIR_MIX))
        self.add('shaft', Shaft(1))

        # connect components
        connect_flow(self,'fl_start.Fl_O', 'inlet.Fl_I')
        connect_flow(self,'inlet.Fl_O', 'comp.Fl_I')
        connect_flow(self,'comp.Fl_O', 'duct.Fl_I')
        connect_flow(self,'duct.Fl_O', 'nozzle.Fl_I')

        self.connect('comp.trq', 'shaft.trq_0')
        self.connect('shaft.Nmech', 'comp.Nmech')

        # self.nl_solver = Newton()
        # self.nl_solver.options['rtol'] = 1.4e-8
        # self.nl_solver.options['maxiter'] = 75
        # self.nl_solver.options['iprint'] = 1

if __name__ == "__main__":

    prob = Problem()
    prob.root = CompressionCycle()

    params = (
        ('MN', 0.6),
        ('inlet_MN', 0.6),
        ('P', 17., {'units':'psi'}),
        ('T', 500.0, {'units':'degR'}),
        ('W', 1.0, {'units':'kg/s'}),
        ('PsE', 4.0, {'units':'psi'})
    )

    prob.root.add('des_vars', IndepVarComp(params))
    prob.root.connect('des_vars.P', 'fl_start.P')
    prob.root.connect('des_vars.T', 'fl_start.T')
    prob.root.connect('des_vars.W', 'fl_start.W')
    # prob.root.connect('des_vars.alt', 'fc.alt')
    # prob.root.connect('des_vars.W', 'fc.fs.W')
    # prob.root.connect('des_vars.MN', 'fc.MN_target')
    prob.root.connect('des_vars.inlet_MN', 'inlet.MN_target')
    # prob.root.connect('fc.ambient.Ps', 'nozzle.Ps_exhaust')
    prob.root.connect("des_vars.PsE", "nozzle.Ps_exhaust")



    prob.setup(check=False)

    # Flight Conditions
    prob['des_vars.W'] = 298.17 #550 lbm/s

    # Inlet Conditions
    prob['inlet.ram_recovery'] = 0.99
    prob['des_vars.inlet_MN'] = 0.6

    # Compressor Conditions
    prob['comp.map.PRdes'] = 12.47
    prob['comp.map.effDes'] = 0.9

    # Nozzle Conditions
    prob['nozzle.Cfg'] = 0.99
    prob['nozzle.dPqP'] = 0.

    prob['des_vars.PsE'] = 14.7

    # Shaft
    prob['shaft.Nmech'] = 10000.

    #prob.root.nozzle.list_connections()

    import time
    t = time.time()
    prob.run()
    print time.time() - t

    astar = np.sqrt(prob['fl_start.Fl_O:stat:gamma']*R_UNIVERSAL_SI*(cu(prob['fl_start.Fl_O:stat:T'], 'degR', 'degK')))
    ustar = astar*prob['fl_start.Fl_O:stat:MN']
    dstar = prob['fl_start.Fl_O:stat:gamma']*cu(prob['fl_start.Fl_O:stat:P'],'psi','Pa')/astar**2
    mustar = 0.00001716*(cu(prob['fl_start.Fl_O:stat:T'], 'degR', 'degK')/273.15)**1.5*(273.15+110.4)/(cu(prob['fl_start.Fl_O:stat:T'], 'degR', 'degK')+110.4) # --- Sutherlands Law
    #Re = dstar*ustar/mustar*Lstar_Lref
    print mustar

    print ""
    print "--- Output ----------------------"

    print "--- Freestream Static Conditions ---"
    print "Mach No.:    %.6f " % (prob['fl_start.Fl_O:stat:MN'])
    print "Ambient Ps:  %.6f Pa" % (cu(prob['fl_start.Fl_O:stat:P'], 'psi', 'Pa'))
    print "Ambient Ts:  %.6f K" % (cu(prob['fl_start.Fl_O:stat:T'], 'degR', 'degK'))
    print "Ambient Rho: %.6f kg/m^3" % (cu(prob['fl_start.Fl_O:stat:rho'], 'lbm/ft**3', 'kg/m**3'))
    print "Pod Velocity:   %.6f m/s" % (cu(prob['fl_start.Fl_O:stat:V'], 'ft/s', 'm/s'))
    print "Ambient Viscosity %.8f kg/(m-s)" % (mustar) #*1.48816394
    print "Reynolds No.=  %.6f  -/grid unit" % ((cu(prob['fl_start.Fl_O:stat:rho'],'lbm/ft**3','kg/m**3')*cu(prob['fl_start.Fl_O:stat:V'],'ft/s','m/s'))/(mustar))
    print ""

    print "--- Fan Conditions ---"
    print "Fan Face Mach No.:   %.6f " % (prob['inlet.Fl_O:stat:MN'])
    print "Fan Radius: %.6f m" % (np.sqrt((cu(prob['inlet.Fl_O:stat:area'], 'inch**2', 'm**2'))/np.pi))
    print "Fan Area:   %.6f m^2" % (cu(prob['inlet.Fl_O:stat:area'], 'inch**2', 'm**2'))
    print "Fan Mdot:   %.6f kg/s" % (cu(prob['inlet.Fl_O:stat:W'], 'lbm/s', 'kg/s'))
    print "Fan Ps:     %.6f Pa" % (cu(prob['inlet.Fl_O:stat:P'], 'psi', 'Pa'))
    print "Fan SPR:    %.6f Pa" % (prob['inlet.Fl_O:stat:P']/prob['fl_start.Fl_O:stat:P'])
    print ""

    print "--- Nozzle Plenum Conditions ---"
    print "Nozzle Plenum Area:  %.6f m^2" % (cu(prob['duct.Fl_O:stat:area'], 'inch**2', 'm**2'))
    print "Nozzle Plenum Ps:    %.6f Pa" % (cu(prob['duct.Fl_O:stat:P'], 'psi', 'Pa'))
    print "Nozzle Plenum Pt:    %.6f Pa" % (cu(prob['duct.Fl_O:tot:P'], 'psi', 'Pa'))
    print "Nozzle Plenum TPR    %.6f Pa" % (prob['duct.Fl_O:tot:P']/prob['fl_start.Fl_O:stat:P'])
    print ""

    print "--- Nozzle Exit Conditions ---"
    print "Mach No.:         %.6f " % (prob['nozzle.Fl_O:stat:MN'])
    print "Nozzle Exit Area: %.6f m^2" % (cu(prob['nozzle.Fl_O:stat:area'], 'inch**2', 'm**2'))
    print "Exhaust Ps:       %.6f Pa" % (cu(prob['fl_start.Fl_O:stat:P'], 'psi', 'Pa'))
    print "Pod Gross Thrust:       %.6f lb" % prob['nozzle.Fg']

    print "--- Debug ---"
    print 'nozzle.Fl_I:tot:P ', prob['nozzle.Fl_I:tot:P']
    print 'nozzle.Fl_I:tot:T ', prob['nozzle.Fl_I:tot:T']
    print 'nozzle.Fl_I:tot:n ', prob['nozzle.Fl_I:tot:n']

    print 'nozzle.Fl_I:stat:W ', prob['nozzle.Fl_I:stat:W']
    print 'nozzle.Fl_I:stat:V ', prob['nozzle.Fl_I:stat:V']
    print 'nozzle.Fl_I:stat:area ', prob['nozzle.Fl_I:stat:area']
    print 'nozzle.Fl_I:stat:P ', prob['nozzle.Fl_I:stat:P']
    print 'nozzle.Fl_I:stat:T ', prob['nozzle.Fl_I:stat:T']
    #print prob['nozzle.Fl_I:']
    print "out"
    print 'nozzle.perf_calcs.sub:P ', prob['nozzle.perf_calcs.sub:P']
    print 'nozzle.perf_calcs.sup:P ', prob['nozzle.perf_calcs.sup:P']
    print 'fl_start.ambient.Ps ', prob['fl_start.Fl_O:stat:P']
    print 'nozzle.Fl_O:tot:P ', prob['nozzle.Fl_O:tot:P']
    print 'nozzle.Fl_O:tot:T ', prob['nozzle.Fl_O:tot:T']

    print "Exhaust Pt:       %.6f Pa" % (cu(prob['nozzle.Fl_O:tot:P'], 'psi', 'Pa'))

    print ""
    print "--- Force/Power Balances ---"
    print "comp pwr out: ", prob['comp.power']
    print "comp trq out: ", prob['comp.trq']
    print "net trq: ", prob['shaft.trq_net']
    print
    # print 'resid', prob['pwr_balance.pwr_net']
    print "comp.Fl_O:tot:P", prob['comp.Fl_O:tot:P']
    print "comp.Fl_O:tot:T", prob['comp.Fl_O:tot:T']
    print "comp.Fl_O:tot:h", prob['comp.Fl_O:tot:h']
