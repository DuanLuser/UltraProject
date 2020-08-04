import os
file=input("FileName:")
if not os.path.exists(file):
    os.makedirs(file)
os.system('sh runforDetect.sh '+file)