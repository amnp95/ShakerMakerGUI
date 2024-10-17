import numpy as np
from scipy.integrate import trapezoid

def source_time_function(Tp,Te,Tr,dt,slp,get_slip=False):
    a = 1.
    b = 100.
    t = np.arange(0, Tr, dt)
    Nt = len(t)
    svf = 0*t

    i1 = t < Tp
    svf[i1] = t[i1]/Tp*np.sqrt(a + b/Tp**2)*np.sin(np.pi*t[i1]/(2*Tp))
    i2 = np.logical_and(t >= Tp, t < Te)
    svf[i2] = np.sqrt(a + b/t[i2]**2)
    i3 = t >= Te
    svf[i3] = np.sqrt(a + b/t[i3]**2)*np.sin(5/3*np.pi*(Tr-t[i3])/Tr)

    A = np.trapz(svf, dx=dt)

    svf /= A
    t = np.arange(Nt)*dt
    slip_rate_function = svf * slp 

    if get_slip:
        time = np.arange(Nt)*dt
        return trapezoid(slip_rate_function,time)
    else:
        from shakermaker.stf_extensions import Discrete
        return Discrete(slip_rate_function, t)