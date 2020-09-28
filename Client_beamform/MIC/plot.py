from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import mpl_toolkits.mplot3d
import matplotlib.pyplot as plt
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import numpy as np
import time

cSlice = 2117
rid = 260

figure=plt.figure()
#ax = Axes3D(figure)
ax=figure.gca(projection="3d")
#plt.ion()

count=0
file = open('LMic/data0-0.txt', 'r')
all_lines = file.readlines()

i = 0
first = 0
Z = []
for line in all_lines:
    array=[]
    line=line.strip()
    line=line.rstrip(',')
    line=line.split(',')
    for x in line:
        x=float(x)
        array.append(x)
    if first == 0:
        first = len(array)
    if len(array) != first:
        continue
    Z.append(array)
    count += 1

print(count)
X = (np.arange(0, first)/(cSlice*2)*(cSlice-rid)+rid)/44100*340/2
Y = np.arange(0,count)
X, Y = np.meshgrid(X,Y)
Z = np.matrix(Z)
print(len(Z.shape))
surf = ax.plot_surface(X,Y,Z,  cmap=plt.get_cmap('rainbow'), linewidth=1, antialiased=False)
ax.xaxis.set_ticks_position('top') #将x轴的位置设置在顶部

ax.set_zlim(0, 0.5)
ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
 
# Add a color bar which maps values to colors.
figure.colorbar(surf, shrink=0.5, aspect=10)

plt.show()

'''
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import mpl_toolkits.mplot3d
import matplotlib.pyplot as plt
import numpy as np

figure=plt.figure()
#ax = Axes3D(figure)
ax=figure.gca(projection="3d")
plt.ion()
plt.show()
count=0
file = open('Mic1.txt', 'r')
all_lines = file.readlines()

for line in all_lines:
    array=[]
    line=line.strip()
    line=line.rstrip(',')
    line=line.split(',')
    for x in line:
        x=float(x)
        array.append(x)
    COUNT=[count]*len(array)
    
    ax.plot_surface(np.arange(0,len(array)),COUNT,array)
    ax.xaxis.set_ticks_position('top') #将x轴的位置设置在顶部
    count+=0.05
'''