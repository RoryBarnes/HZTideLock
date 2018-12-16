#!/usr/local/bin/python3.7

# Script to run all vspace runs
import sys
import string
import subprocess as subp
import matplotlib.pyplot as plt
import vplot as vpl
import numpy as np


MSUN = 1.988416e33      # Stellar mass in grams from Prsa et al. 2016
AUCM = 1.49598e13       # Astronomical Unit in cm recommended by the IAU
RSUN = 6.957e10         # Stellar radius in cm from Prsa et al. 2016
LSUN = 3.828e33         # Nominal solar luminosity in cgs recommended by the IAU
PI = 3.1415926535
SIGMA = 5.6704e-5       # Stefan-Boltzmann constant in cgs units

# HZ boundaries from Kopparapu et al. (2013)
def HabitableZone(lum,teff,lim):
    seff = [0 for j in range(6)]
    seffsun = [0 for j in range(6)]
    aa = [0 for j in range(6)]
    b = [0 for j in range(6)]
    c = [0 for j in range(6)]
    d = [0 for j in range(6)]

    seffsun[0] = 1.7763
    seffsun[1] = 1.0385
    seffsun[2] = 1.0146
    seffsun[3] = 0.3507
    seffsun[4] = 0.2946
    seffsun[5] = 0.2484

    aa[0] = 1.4335e-4
    aa[1] = 1.2456e-4
    aa[2] = 8.1884e-5
    aa[3] = 5.9578e-5
    aa[4] = 4.9952e-5
    aa[5] = 4.2588e-5

    b[0] = 3.3954e-9
    b[1] = 1.4612e-8
    b[2] = 1.9394e-9
    b[3] = 1.6707e-9
    b[4] = 1.3893e-9
    b[5] = 1.1963e-9

    c[0] = -7.6364e-12
    c[1] = -7.6345e-12
    c[2] = -4.3618e-12
    c[3] = -3.0058e-12
    c[4] = -2.5331e-12
    c[5] = -2.1709e-12

    d[0] = -1.1950e-15
    d[1] = -1.7511E-15
    d[2] = -6.8260e-16
    d[3] = -5.1925e-16
    d[4] = -4.3896e-16
    d[5] = -3.8282e-16

    tstar = teff - 5700

    for j in range(6):
        seff[j] = seffsun[j] + aa[j]*tstar + b[j]*tstar**2 + c[j]*tstar**3 + d[j]*tstar**4
        # Assign HZ limit to lim array
        lim[j] = np.sqrt(lum/seff[j])

# stellar mass-luminosity relation from Baraffe et al. (2015). Fit by R. Barnes.
def MassLumBaraffe15(m):
    x=np.log10(m)
    l=-0.04941 + 6.6496*x + 8.7299*x**2 + 5.2076*x**3
    return 10**l

# Stellar mass-radius relation from Baraffe et al. (2015). Fit by R. Barnes.
def MassRadBaraffe15(m):
    # Check against dBaraffe15_MassRad in util.c in the EQTIDE package
    return 0.003269 + 1.304*m - 1.312*m**2 + 1.055*m**3

# Planetary radius from Sotin et al. (2007)
def MassRadSotin07(m):
    # Scaling law is broken at 1 M_Earth
    if (m >= 1):
        return np.power(m,0.274)
    else:
        return np.power(m,0.306)


# Check correct number of arguments
if (len(sys.argv) != 2):
    print('ERROR: Incorrect number of arguments.')
    print('Usage: '+sys.argv[0]+' <pdf | png>')
    exit(1)
if (sys.argv[1] != 'pdf' and sys.argv[1] != 'png'):
    print('ERROR: Unknown file format: '+sys.argv[1])
    print('Options are: pdf, png')
    exit(1)

# Number of dimensions
nsemi=101
nstar=94
semi=[0 for j in range(nsemi)]
star=[0 for j in range(nstar)]
tsync=[[0 for j in range(nsemi)] for k in range(nstar)]

result = subp.run("ls -d data/tsync*", shell=True, stdout=subp.PIPE).stdout.decode('utf-8')
dirs=result.split()

# Dirs contains array of directories to run

iStar=0
iSemi=0

for dir in dirs:
    if dir != "0":  # WTF?
        cmd = "cd "+dir+"; vplanet vpl.in >& output"
        subp.call(cmd, shell=True)
        # At this point the log file has been generated

        logfile=dir+'/tsync.log'
        forwfile=dir+'/tsync.planet.forward'
        log=open(logfile,"r")
        forw=open(forwfile,"r")

        sys.stdout.flush()
        sys.stderr.flush()
        # Now search for Io's parameters
        foundstar=0
        foundpl=0
        for line in log:
            words=line.split()
            if len(words) > 2:
                if (words[1] == "BODY:") and (words[2] == "star"):
                    foundstar=1
                if (words[0] == "(Mass)") and (foundstar == 1):
                    star[iStar] = float(words[3])/1.988416e30
                    foundstar=0
                if (words[1] == "BODY:") and (words[2] == "planet"):
                    foundpl=1
                if (words[0] == "(SemiMajorAxis)") and (foundpl == 1):
                    semi[iSemi] = float(words[4])/1.49597870700e11
        for line in forw:
            words=line.split()
            tsync[iStar][iSemi] = np.log10(float(words[0]))
        print(dir,semi[iSemi],star[iStar],iStar,tsync[iStar][iSemi])
        iSemi += 1
        if (iSemi == nsemi):
        # New line in semi
            iStar += 1
            iSemi = 0

# Arrays ecc,obl,heat now contain the data to make the figure

print(star)
print(semi)


msmin=0.07      # Minimum stellar mass in solar units
msmax=1.01     # Maximum stellar mass in solar units
dm=0.00003      # Increment in stellar mass in solar units

amin=0.005      # Minimum semi-major axis in AU
amax=1.01      # Maximum semi-major axis in AU
da=0.0003       # Increment in semi-major axis in AU

abin=int((amax-amin)/da)    # delta semi-major axis
mbin=int((msmax-msmin)/dm)  # delta stellar mass

acol=[(amin + i*da) for i in range(abin)]  # vector of semi-major axis values
mcol=[(msmin + i*dm) for i in range(mbin)] # vector of stellar mass values

# Calculate HZ boundaries
l=[0 for i in range(mbin)]    # Stellar luminosity
rs=[0 for i in range(mbin)]   # Stellar radius
teff=[0 for i in range(mbin)] # Stellar effective temperature
rv=[0 for i in range(mbin)]   # Recent Venus
mg=[0 for i in range(mbin)]   # Moist Greenhouse
maxg=[0 for i in range(mbin)] # Maximum Greenhouse
em=[0 for i in range(mbin)]   # Early Mars
lim=[0 for j in range(6)]     # HZ limits

for im in range(mbin):
    l[im] = MassLumBaraffe15(mcol[im])
    rs[im] = MassRadBaraffe15(mcol[im])
    teff[im]=((l[im]*LSUN)/(4*PI*SIGMA*(rs[im]*RSUN)**2))**0.25
    HabitableZone(l[im],teff[im],lim)
    rv[im] = lim[0]
    mg[im] = lim[2]
    maxg[im] = lim[3]
    em[im] = lim[4]


plt.figure(figsize=(6.5,9))

plt.xlabel('Semi-Major Axis [AU]',fontsize=20)
plt.ylabel('Stellar Mass [M$_\odot$]',fontsize=20)
plt.tick_params(axis='both', labelsize=20)

fbk = {'lw':0.0, 'edgecolor':None}

plt.fill_betweenx(mcol,rv,em,facecolor='0.85', **fbk)
plt.fill_betweenx(mcol,mg,maxg,facecolor='0.75', **fbk)
plt.title('Synchronization Time [log$_{10}$(years)]')

#plt.xscale('log')
#plt.yscale('log')
plt.xlim(0.01,1)
plt.ylim(0.075,1)

ContSet = plt.contour(semi,star,tsync,5,colors='black',linestyles='solid',
                      levels=[6,7,8,9,10],linewidths=3)
plt.clabel(ContSet,fmt="%.0f",inline=True,fontsize=18)

# Io's heat flux is 1.5-3 W/m^2. After some fussing, this choice of contour matches that range.
#plt.contour(ecc,obl,heat,5,colors=vpl.colors.orange,linestyles='solid',

plt.tight_layout()

if (sys.argv[1] == 'pdf'):
    plt.savefig('HZSync.pdf')
if (sys.argv[1] == 'png'):
    plt.savefig('HZSync.png')
