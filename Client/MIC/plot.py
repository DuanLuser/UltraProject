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
    ax.plot(np.arange(0,len(array)),COUNT,array)
    ax.xaxis.set_ticks_position('top') #将x轴的位置设置在顶部
    count+=0.05
    
    
    