import numpy as np, math, sys
sys.path.insert(0, "D:/Downloads/Documents/Satellite/ch3_code")
import decay_sim as ds

MU, RE, WE = ds.MU_E, ds.R_E, ds.W_E
INC = math.radians(ds.INC_DEG)
COSI = math.cos(INC)

print("=== A. exact vs code vrel2 (pointwise, on a Keplerian orbit) ===")
# Keplerian orbit with elements a,e, argp=0, inc=INC; parametrise by true anomaly
def kepler_state(a, e, nu, inc=INC, argp=0.0):
    p = a * (1 - e * e)
    r = p / (1 + e * math.cos(nu))
    # perifocal
    xp = r * math.cos(nu); yp = r * math.sin(nu)
    # perifocal velocity
    h = math.sqrt(MU * p)
    vxp = -MU / h * math.sin(nu); vyp = MU / h * (e + math.cos(nu))
    # rotate perifocal -> inertial: Rz(argp) Rx(inc)
    cO,sO = math.cos(argp), math.sin(argp)
    ci,si = math.cos(inc), math.sin(inc)
    R = np.array([[cO,-sO,0],[sO*ci,cO*ci,-si],[sO*si,cO*si,ci]])
    return R @ np.array([xp,yp,0.0]), R @ np.array([vxp,vyp,0.0])

def exact_vrel2(r, v):
    vrel = v - np.cross(np.array([0.,0.,WE]), r)
    return float(vrel @ vrel)

def code_vrel2(r, v, a, e):
    p = a*(1-e*e); h = math.sqrt(MU*p)
    rn = np.linalg.norm(r); v2 = MU*(2/rn - 1/a)
    return v2 - 2*WE*h*COSI + WE**2*rn*rn*(1-0.5*(1-COSI**2))

a = 24396.137e3; e = 0.728312
print(f"{'nu':>7} {'exact':>16} {'code':>16} {'rel err':>10}")
errs=[]
for nu in np.linspace(0, 2*math.pi, 9)[:-1]:
    r,v = kepler_state(a,e,nu)
    ex = exact_vrel2(r,v); co = code_vrel2(r,v,a,e)
    errs.append(co/ex-1)
    print(f"{math.degrees(nu):7.1f} {ex:16.6e} {co:16.6e} {co/ex-1:+10.3e}")
print(f"  pointwise rel err: min {min(errs):+.3e} max {max(errs):+.3e}")
print(f"  (omega*r term is ~({WE*RE/1000:.1f} km/s)^2 vs v^2; the {WE**2*r**2} term is "
      f"{WE**2*a**2:.3e} vs v^2~{ (MU*(2/a-1/a)):.3e})")

print()
print("=== B. exact orbit-average of da/dt and de2/dt vs Model B averaged_rates ===")
# Exact: 2-body Kepler orbit + drag with co-rotating atmosphere, time-weighted average.
def exact_avg(a, e, am, f107, ap, cd, n=20001):
    # sample eccentric anomaly uniformly, weight by dt/dE = (1 - e cosE)/n
    E = np.linspace(0, 2*math.pi, n, endpoint=False)
    w = 1 - e*np.cos(E)
    rn = a*w
    v2 = MU*(2/rn - 1/a)
    # mean motion relation: dt/dE = w/n
    n_orb = math.sqrt(MU/a**3)
    # perifocal position/velocity from E
    xp = a*(np.cos(E)-e); yp = a*math.sqrt(1-e*e)*np.sin(E)
    r = np.stack([xp,yp,np.zeros_like(xp)],axis=1)
    # velocity in perifocal
    Edot = n_orb/w
    vxp = -a*np.sin(E)*Edot; vyp = a*math.sqrt(1-e*e)*np.cos(E)*Edot
    v = np.stack([vxp,vyp,np.zeros_like(xp)],axis=1)
    # rotate into inertial with inc
    ci,si = math.cos(INC), math.sin(INC)
    R = np.array([[1,0,0],[0,ci,-si],[0,si,ci]])
    r = r @ R.T; v = v @ R.T
    om = np.array([0.,0.,WE])
    vrel = v - np.cross(om, r)
    vr = np.linalg.norm(vrel, axis=1)
    rho = ds.rho_atm(rn-RE, f107, ap)
    D = 0.5*cd*am*rho*vr
    # da/dt = -(2a^2/mu) D (v.vrel) ;  d(e^2)/dt
    p = a*(1-e*e); h = math.sqrt(MU*p)
    vdotvrel = v2 - WE*h*COSI
    # dp/dt = -2 D p (1 - W r^2 cos i/h)
    adot_inst = -(2*a*a/MU)*D*vdotvrel
    pdot_inst = -2*D*p*(1 - WE*rn*rn*COSI/h)
    e2dot_inst = -pdot_inst/a + p*adot_inst/(a*a)
    # time weight dt/dE = w/n_orb, normalized so <.> = int X w dE / (2pi)
    adot = np.mean(adot_inst*w)*1.0
    e2dot = np.mean(e2dot_inst*w)*1.0
    return adot, e2dot

for (am, f107) in [(ds.composite_am(0.0),130.), (ds.composite_am(140.0,1.0),130.),
                   (ds.composite_am(0.0),70.), (ds.composite_am(400.0,1.0),130.)]:
    ad, e2d = exact_avg(a, e, am, f107, 10., ds.CD)
    ab, e2b = ds.averaged_rates(a, e*e, am, f107, 10., ds.CD)
    print(f" am={am:.5f} f107={f107:.0f}")
    print(f"   exact  da/dt={ad:.6e}  de2/dt={e2d:+.6e}")
    print(f"   ModelB da/dt={ab:.6e}  de2/dt={e2b:+.6e}")
    print(f"   ratio da {ab/ad:.5f}   de2 {e2b/e2d:.5f}")
