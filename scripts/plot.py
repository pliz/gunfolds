import seaborn as sb
import zickle as zkl
import sys
import numpy as np
from matplotlib import pyplot as plt

sys.path.append('./tools/')
densities = [.15, 0.2, 0.25, 0.3, 0.35]

def gettimes(d):
    t = [x['ms'] for x in d]
    time  = map(lambda x: x/1000./60., t)
    return time

def getalltimes(data, densities=densities):
    alltimes = []
    for dens in densities:        
        alltimes.append(gettimes(data[dens]))
    return alltimes

def timesfromfile(fname):
    d = zkl.load(fname)
    return getalltimes(d)

#alltimes_old = timesfromfile("hooke_nodes_8_old_nomem.zkl")
#alltimes_new = timesfromfile("hooke_nodes_8_newp_.zkl")

#alltimes_old = timesfromfile("hooke_nodes_10_newp_.zkl")
#alltimes_old = timesfromfile("hooke_nodes_6_g32g1_.zkl")
#alltimes_new = timesfromfile("leibnitz_nodes_35_newp_.zkl")

l = ['leibnitz_nodes_15_density_0.1_newp_.zkl',
     'leibnitz_nodes_20_density_0.1_newp_.zkl',
     'leibnitz_nodes_25_density_0.1_newp_.zkl',
     'leibnitz_nodes_30_density_0.1_newp_.zkl',
     'leibnitz_nodes_35_density_0.1_newp_.zkl']

alltimes_new = []
for fname in l:
    d = zkl.load(fname)
    alltimes_new.append(gettimes(d))

shift = 0.15
wds = 0.3
fliersz = 2
lwd = 1

plt.figure(figsize=[10,2])

# g = sb.boxplot(alltimes_old,names=map(lambda x: str(int(x*100))+"%",
#                                      densities),
#               widths=wds, color="Reds", fliersize=fliersz, linewidth=lwd,
#               **{'positions':np.arange(len(densities))-shift,
#                  'label':'naive approach'})

g = sb.boxplot(alltimes_new,names=map(lambda x: str(int(x*100))+"",
                                      densities),
               widths=wds, color="Blues",fliersize=fliersz,
               linewidth=lwd,
               **{'positions':np.arange(len(densities))+shift,
                  'label':'MSL'})

# plt.plot(np.arange(len(densities))-shift,
#         map(np.median,alltimes_old), 'ro-', lw=0.5, mec='k')
# plt.plot(np.arange(len(densities))+shift,
#         map(np.median,alltimes_new), 'bo-', lw=0.5, mec='k')
g.figure.get_axes()[0].set_yscale('log')
plt.xlabel('density (% of 36 total possible edges)')
plt.ylabel('computation time (minutes)')
plt.title('100 6 node graphs per density\n$G_2 \\rightarrow G_1$',
          multialignment='center')
plt.subplots_adjust(right=0.99, left=0.2)
plt.legend(loc=0)
plt.show()
