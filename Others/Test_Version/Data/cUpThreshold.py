import sys
import re
import math

'''nonempty 阈值 >='''

#目前先设定正负阈值一样
COUNT=[] # 0.5, 1, 1.5, ...；

def Top2(data):
   
    array=[]
    for str in data :
        str=re.sub('[1-6]---mx:|mi:|\n','',str)
        str=re.sub(',',' ',str)
        num=str.split()
        #print(num)
        array.append(max(float(num[0]),abs(float(num[1]))-1))#二者取最大，正负一定有三个mic低于该阈值，abs(负)=正+1
    array.sort()
    #print(max(array_z[3],array_f[3])) 
    site=array[3]
    if site == 2147483646 or site<0.5:
        site = 0.5
    if site>8:
        print(data)
    site=math.floor(site*2)-1
    if site >=99: site=99
    COUNT[site]+=1
    
    
def analysis():
    nonempty_num=0
    file = open('Data.txt', 'r')
    all_lines = file.readlines()
    i = 0
    while i< len(all_lines):
        line=re.sub('\n','',all_lines[i])
        #print(line)
        if line == 'nonempty,1,1.00m':
            nonempty_num+=1

            lc=1
            data=[]
            while lc < 6:
                data.append(all_lines[i-lc])
                lc+=1
            Top2(data)
        i+=1
    print(nonempty_num)
    print(COUNT)
    i=0
    while i<len(COUNT):
        if COUNT[i]>0:
            print((i+1)/2.0)
            break
        i+=1
       

if __name__ == "__main__":
    #print(math.ceil(1.6/0.5))
    for i in range(100):
        COUNT.append(0)
    sys.exit(analysis())