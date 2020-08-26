import os
import sys 
file='empty' #sys.argv[1] #input("FileName:")
if not os.path.exists(file):
    os.makedirs(file)
os.system('sh runforDetect.sh '+file +' 0 0')#2:record-index;3: