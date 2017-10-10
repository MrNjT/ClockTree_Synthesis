import math
import sys, os
import re

if(len(sys.argv)<5):
   print "Usage: python clockTree.py netlistFile BufferType input_pin output_pin clock_Signal"
   exit(0)
netlistFile = sys.argv[1]
circuit = netlistFile.split(".")
circuitName = circuit[0]
cellType = sys.argv[2]
cellIn = sys.argv[3]
cellOut = sys.argv[4]
clk = sys.argv[5]
lef = "osu035_stdcells.lef"
netlist_original=netlistFile
netlist_noFF = []
#count flip flops
flipFlops = 0
flipFlopsLineIndex=[]
with open(netlistFile) as f1:
      netlist = f1.readlines()

index =0
clockTreeNetlist=[]
for line in netlist:
      line = line.strip()
      if line.startswith(".gate DFF") or line.startswith(".model") or line.startswith(".inputs") or line.startswith(".outputs") or line.startswith(".end"):
             clockTreeNetlist.append(line)             
      if not line.startswith(".gate DFF"):
          netlist_noFF.append(line)

for line in clockTreeNetlist:
   if line.startswith(".gate DFF"):
          flipFlops = flipFlops + 1
          flipFlopsLineIndex.append(index)
   index = index + 1

endIndex = len(netlist)
numNodes = 2*flipFlops - 1
numLevels = int(math.log(numNodes,2)) 
bufInput=""
bufOutput=""
unconnected = True
i=0
firstOut = "a0_1"
firstBuf = cellType + "_0_0"
netlist.insert(len(netlist)-1, ".gate " + cellType + " " + str(cellIn)+"=" + str(clk) + " " + str(cellOut) +"=" + str(firstOut) )
clockTreeNetlist.insert(len(clockTreeNetlist)-1, ".gate " + cellType + " " + str(cellIn)+"=" + str(clk) + " " + str(cellOut) +"=" + str(firstOut) )
for level in range(numLevels):
    nodesInLevel = 2**(level+1)
    for node in range(nodesInLevel):
	bufInput = "a"+str(level) + "_" + str(int((node)/2+1))
        bufOutput =  "a"+str(level+1)+ "_" + str(node+1)
        bufInst = cellType + "_" + str(level+1) + "_" + str(node+1)
        mystr = ".gate " + cellType + " " + str(cellIn)+"=" + str(bufInput) + " "+ str(cellOut) +"=" + str(bufOutput)
        if (level == numLevels -1 and unconnected == True) or level < numLevels-1:
        	netlist.insert(len(netlist)-1,mystr)
                clockTreeNetlist.insert(len(clockTreeNetlist)-1,mystr)
        #netlist.insert(len(netlist)-1,mystr)
        if level == numLevels -1 and unconnected == True:
           regex = re.compile(r"CLK=%s.+ "%str(clk))
           clockTreeNetlist[flipFlopsLineIndex[i]] = re.sub(r"CLK=%s.+ "%str(clk),"CLK="+ bufOutput+ " ",clockTreeNetlist[flipFlopsLineIndex[i]])
           #clockTreeNetlist[flipFlopsLineIndex[i]] = clockTreeNetlist[flipFlopsLineIndex[i]].replace("CLK=" + str(clk),"CLK="+ bufOutput)
           i = i+1
           if i == flipFlops:
              unconnected = False

#step1, place original netlist without CTS
os.system("./blif2cel.tcl --blif " + netlist_original + " --lef " + str(lef) + " --cel " + "step1.cel")
f20 = open("step1.cel","r")
cel_contents = f20.readlines()
for i in range(len(cel_contents)):
    if cel_contents[i].startswith("pad"):
       if ((cel_contents[i].split(" "))[-1]).startswith("twpin_clk"):
         print i
         for j in range(6):
           if cel_contents[i+j].startswith("pin"):
              cel_contents.insert(i+j,"restrict side B sidespace 0.5\n" )
              print j
              break
f20.close()
f21 = open("step1.cel","w")
for i in cel_contents:
    f21.write(i)
f21.close()
os.system("cp osu035.par "+ "temp.par")
os.system("mv temp.par "+ "step1" + ".par")
os.system("graywolf " + "step1")
os.system("./place2def.tcl step1 FILL 4")
os.system("mv step1.def " + circuitName+ "_step1.def")

#get core area
gsav_file = open("step1.gsav","r")
gsav = gsav_file.readlines()
core=""
for line in gsav:
  line = line.strip()
  if line.startswith("core"):
    core = line.split(' ', 1)[1]
    break

core_coordinates=core.split(" ")
xmin=core_coordinates[0]
xmax=core_coordinates[2]
ymin=core_coordinates[1]
ymax=core_coordinates[3]
original_area = (int(xmax)-int(xmin)) * (int(ymax)-int(ymin))
utilization = 0.8
area_new = original_area/utilization
area_inv = 480*2000
num_added_inv = int((area_new-original_area)/area_inv)
j=10000
f_original = open(netlist_original,"r")
contents = f_original.readlines() 
for i in range(num_added_inv):
    contents.insert(len(contents)-1,".gate INVX4 A=" + str(i) + " Y="+str(j))
    j=j+1
f_original.close()
f2 = open("step1_1.blif","w")
for line in contents:
    f2.write(line)
    f2.write("\n")
f2.close()
os.system("./blif2cel.tcl --blif " + "step1_1.blif" + " --lef " + str(lef) + " --cel " + "step1.cel")
f20 = open("step1.cel","r")
cel_contents = f20.readlines()
for i in range(len(cel_contents)):
    if cel_contents[i].startswith("pad"):
       if ((cel_contents[i].split(" "))[-1]).startswith("twpin_clk"):
         print i
         for j in range(6):
           if cel_contents[i+j].startswith("pin"):
              cel_contents.insert(i+j,"restrict side B sidespace 0.5\n" )
              print j
              break
f20.close()
f21 = open("step1.cel","w")
for i in cel_contents:
    f21.write(i)
f21.close()
os.system("rm fixed_area")
os.system("cp osu035.par "+ "temp.par")
os.system("mv temp.par "+ "step1" + ".par")
os.system("graywolf " + "step1")
os.system("./place2def.tcl step1 FILL 4")
#os.system("mv step1.def " + circuitName+ "_step_1_1.def")
#remove inverters
start=-1
end=-1
f50 = open("step1.ncel")
contents=f50.readlines()
for i in range(len(contents)):
   line = contents[i].strip()
   if line.startswith("cell"):
       if ((line.split(" "))[-1]).startswith("INVX4") and start == -1:
          start=i
   if line.startswith("pad"):
       end = i
       break
del contents[start:end]

#get core area
gsav_file = open("step1.gsav","r")
gsav = gsav_file.readlines()
core=""
for line in gsav:
  line = line.strip()
  if line.startswith("core"):
    core = line.split(' ', 1)[1]
    break

core_coordinates=core.split(" ")
xmin=core_coordinates[0]
xmax=core_coordinates[2]
ymin=core_coordinates[1]
ymax=core_coordinates[3]

#add fixed area to par file
par_file = open("step1.par","r")
inserted = False
par = par_file.readlines()
for i in range(len(par)):
     line = par[i].strip()
     if line.startswith("GENR*utilization"):
         del par[i]
for i in range(len(par)):
     line = par[i].strip()
     if line.startswith("TWMC*") and inserted == False:
        par.insert(i,"TWMC*core : "+core+"\n")
        inserted = True
os.system("rm step1.par")
newpar = open("step1.par","w")
for i in range(len(par)):
    newpar.write(par[i])
    #newpar.write("\n")
newpar.close()


#step2, clock tree
f2 = open("clockTree.blif","w")
for line in clockTreeNetlist:
    f2.write(line)
    f2.write("\n")
f2.close()
os.system("./blif2cel.tcl --blif " + "clockTree.blif" + " --lef " + str(lef) + " --cel " +   "clockTree.cel")

f30=open("fixed_area","r")
area1 = int(f30.readlines()[0])
f30.close()

DFFpositions={}
j=0
with open("step1.ncel") as f3:
      ncel = f3.readlines()
for i in range(len(ncel)):
    ncel[i] = ncel[i].strip()
    if ncel[i].startswith("cell"):
       splitLine = ncel[i].split(" ")
       if splitLine[-1].startswith("DFF"):
         DFFpositions[(splitLine[-1])] = ncel[i+1]          
       
f11=open("clockTree.cel","r")
content = f11.readlines()
for i in range(len(content)):
    content[i] = content[i].strip()
    if content[i].startswith("cell"):
       splitLine = content[i].split(" ")
       if splitLine[-1].startswith("DFF"):
          for key, value in DFFpositions.iteritems():
              if key == splitLine[-1]:
                 content.insert(i+1,value)
for i in range(len(content)):
    if content[i].startswith("pad"):
       if ((content[i].split(" "))[-1]).startswith("twpin_clk"):
         print i
         for j in range(6):
           if content[i+j].startswith("pin"):
              content.insert(i+j,"restrict side B sidespace 0.5\n" )
              print j
              break
f12 = open("step1.cel","w")

for i in range(len(content)):
    content[i] = content[i].replace("nonfixed","fixed")
    f12.write(content[i])
    f12.write("\n")
f12.close()
#place
os.system("mv step1.pl1 step1.pl1_1")
os.system("graywolf " + "step1")
os.system("./place2def.tcl step1 FILL 4")
os.system("mv step1.def " + circuitName+ "_step_2.def")
f30=open("fixed_area","r")
area2 = int(f30.readlines()[0])
f30.close()

##################################################################################################
diff_area = area1-area2 #original area - clock tree area
buff_width = 480
# add unconnected inverters to fill empty places
num_added_buffs = int(diff_area/buff_width) - 20
j=10000
for i in range(num_added_buffs):
    clockTreeNetlist.insert(len(clockTreeNetlist)-1,".gate INVX4 A=" + str(i) + " Y="+str(j))
    j=j+1
f2 = open("clockTree.blif","w")
for line in clockTreeNetlist:
    f2.write(line)
    f2.write("\n")
f2.close()

os.system("./blif2cel.tcl --blif " + "clockTree.blif" + " --lef " + str(lef) + " --cel " +   "clockTree.cel")

f11=open("clockTree.cel","r")
content = f11.readlines()
for i in range(len(content)):
    content[i] = content[i].strip()
    if content[i].startswith("cell"):
       splitLine = content[i].split(" ")
       if splitLine[-1].startswith("DFF"):
          for key, value in DFFpositions.iteritems():
              if key == splitLine[-1]:
                 content.insert(i+1,value)
for i in range(len(content)):
    if content[i].startswith("pad"):
       if ((content[i].split(" "))[-1]).startswith("twpin_clk"):
         print i
         for j in range(6):
           if content[i+j].startswith("pin"):
              content.insert(i+j,"restrict side B sidespace 0.5\n" )
              print j
              break
f12 = open("step1.cel","w")
for i in range(len(content)):
    content[i] = content[i].replace("nonfixed","fixed")
    f12.write(content[i])
    f12.write("\n")
f12.close()
#place
f40 = open("fixed_area","w")
f40.write(str(area1)) #use original area
f40.close()
os.system("mv step1.pl1 step1.pl1_1")
os.system("graywolf " + "step1")
os.system("./place2def.tcl step1 FILL 4")
#remove extra inverters
start=-1
end=-1
f50 = open("step1.ncel")
contents=f50.readlines()
for i in range(len(contents)):
   line = contents[i].strip()
   if line.startswith("cell"):
       if ((line.split(" "))[-1]).startswith("INVX4") and start == -1:
          start=i
   if line.startswith("pad"):
       end = i
       break
del contents[start:end]

#fix buffers, FlipFlops
f12 = open("step1.cel","w")
for i in range(len(contents)):
    contents[i] = contents[i].replace("nonfixed","fixed")
    f12.write(contents[i])
    f12.write("\n")
f12.close()
#place
f40 = open("fixed_area","w")
f40.write(str(area1))#use original area
f40.close()
os.system("mv step1.pl1 step1.pl1_1")
os.system("graywolf " + "step1")
os.system("./place2def.tcl step1 FILL 4")
os.system("mv step1.def " + circuitName + "_step2.def")
          
with open("step1.ncel") as f7:
     step3 = f7.readlines()
f8 = open("step3.cel","w")
for i in range(len(step3)):
    step3[i] = step3[i].replace("nonfixed","fixed")
    f8.write(step3[i])
    f8.write("\n")
f8.close()

f40 = open("fixed_area","w")
f40.write(str(area1))
f40.close()
#step3, add rest of cells to step3.cel and place
f9 = open("netlist_noFF.blif","w")
for i in netlist_noFF:
    f9.write(i)
    f9.write("\n")
f9.close()
os.system("./blif2cel.tcl --blif " + "netlist_noFF.blif" + " --lef " + str(lef) + " --cel " +   "netlist_noFF.cel")
with open ("netlist_noFF.cel") as f11:
     netlist_noFF = f11.readlines()
f10 = open("netlist_noFF.cel","w")
for i in netlist_noFF:
    if i.startswith("pad"):
      break
    f10.write(i)
    f10.write("\n")
f10.close()

filenames = ['netlist_noFF.cel','step3.cel']
with open('step1.cel', 'w') as outfile:
    for fname in filenames:
        with open(fname) as infile:
            outfile.write(infile.read())
os.system("mv step1.pl1 step.pl1_2")
os.system("graywolf " + "step1")
os.system("./place2def.tcl step1 FILL 4")
os.system("mv step1.def "+ circuitName+".def")
