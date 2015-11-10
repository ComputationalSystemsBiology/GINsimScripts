from org.ginsim.common.callable import BasicProgressListener
from org.ginsim.service.export.nusmv import NuSMVConfig
import os
import re
import sys
import getopt
import imp
# Source path for the module HTML
HTML=imp.load_source('HTML','path/HTML.py')


if len(gs.args)==0:
    print "Usage: java -jar PATH/GINsim.jar -s attractors.py model.zginml -p perturbations.txt -r report.html"
    sys.exit(1)

if gs.args[0].find(".zginml")<0:
    print "The first argument should be a GINsim file (.zginml)"
    sys.exit(1)
    
g = gs.open(gs.args[0])
fmodel=gs.args[0]
reg=re.findall("([\w\-\_]*)",fmodel)
if(len(reg)<4):
   modelname=fmodel
else:
    modelname=reg[-4]
print "########################"
print "Model "+fmodel
print "########################"

if not os.path.isfile(fmodel):
    print(fmodel+" file not found")
    sys.exit (1)
    

fperturb=''
freport=''
 
# Parse the optional arguments -p perturbations.txt -r report.html
try:
    myopts, args = getopt.getopt(gs.args[1:],"r:p:")
except getopt.GetoptError, e:
    print (str(e))
    print("Usage: %s -p perturbations.txt -r report.html" % gs.args[0])
    sys.exit(2)
for o, a in myopts:
    if o == '-p':
        fperturb=a
    elif o == '-r':
        freport=a
 
 
perturblist=list()
if fperturb!="":
    if not os.path.isfile(fperturb):
	   print(fperturb+" file not found")
    else:
	f = open(fperturb,"r")
	for line in f:
	    if line[-1]=='\n':
   	        perturblist.append(line[:-1])
   	    else:
   	        perturblist.append(line)
	f.close()
    print "Perturbations from "+fperturb+": "+' - '.join(perturblist)
else:
    print "No perturbation file provided"    

	
#sreduction = gs.service("reduction")
ssim = gs.service("simulation")
sscc = gs.service("SCC")
#ssmv = gs.service("NuSMV")

# dummy progress listener
plist = BasicProgressListener()

# simulate the model and return the attractors (as a list of lists of states)
# if update is 0 or not specified, the simulation is asynchronous, otherwise synchronous
def simulate_model(g, model, update=0):

    sim_idx = 0
    simparameter = gs.associated(g, "reg2dyn_parameters", True)
    parameter = simparameter[sim_idx]
    currentupdate = str(parameter.getPriorityDefinition())
    selectedupdate="asynchronous" if update==0 else "synchronous"
    # change parameters to change the update policy
    while currentupdate!=selectedupdate and sim_idx<(len(simparameter)-1): 
       sim_idx+=1
       parameter = simparameter[sim_idx]
       currentupdate=str(parameter.getPriorityDefinition())
    if currentupdate!=selectedupdate:
        print selectedupdate+" update policy not found in the parameters of the model"
	
    simulator = ssim.get(model, plist, parameter)	
    # Actually run the simulation with the progress listener
    stg = simulator.do_simulation()
    
    # get the graph of the SCC and find attractors
    sccgraph = sscc.getSCCGraph(stg)
    attractors=list()
    for component in sccgraph.getNodes():
        attract=list()
        out = sccgraph.getOutgoingEdges(component)
        if out is None or len(out) == 0:
	    attract = component.getContent()
	    # for a synchronous simulation order complex attractors
	    if selectedupdate=="synchronous" and len(attract)>1:
                attractordered = [attract[0]]
	        for i in range(len(attract)-1):
		    nextstate=stg.getOutgoingEdges(attractordered[-1]).get(0).getTarget()
	            attractordered.append(nextstate)
                attract =  attractordered
	if(len(attract)>0):
	    attractors.append(attract)
	
    return attractors
    
    

# Display the states in stateslist (list of list of states) as tables 
# of all the states with the nodes as columns
def display_full_states(stateslist,nodes):
    for states in stateslist:
	table=""
	for node in nodes:
	    table+=str(node[0])+"\t"
	table=table[:-1]+"\n"
	for state in states:
	    table+=str(state).replace("","\t")[1:-1]+"\n"
	table+=str(len(states))+" states\n"
        print table
	
# Display the states in stateslist (list of list of states) as a line with
# the presence, absence or mix (*) of each component in each list
def display_short_states(stateslist,nodes):
    for states in stateslist:
	table=""
	for node in nodes:
	    table+=str(node[0])+"\t"
	table=table[:-1]+"\n"
	vector=[-1]*len(nodes)
	for state in states:
	    for i,s in enumerate(str(state)):
		if vector[i]==-1:
		    vector[i]=s
		elif vector[i]!="*" and vector[i]!=s:
		    vector[i]="*"
	table+="\t".join(str(e) for e in vector)+"\n"
	table+=str(len(states))+" states\n"
        print table	
	
# Change a state like "1200" to [(Mol1,1),(Mol2,2),(Mol3,0),(Mol4,0)]
def stateLogicalToList(state,nodes):
    return [(str(nodes[i][0]),int(str(state)[i])) for i in range(len(str(state)))]

def htmltext(text):
    text="<p>"+text.replace("\n","<br />")+"</p>"
    return text
    
def htmltextbold(text):
    text="<p style='font-weight:bold'>"+text.replace("\n","<br />")+"</p>"
    return text
    
def htmltitle(text):
    text="<h2>"+text.replace("\n","</h2><h2>")+"</h2>"
    return text

# Create an html table to display a set of states with only one row
def htmlShortTables(stateslist,nodes):
    # Reorder stateslist to put the complex attractors before
    newstateslist=list()
    for i, states in enumerate(stateslist):
        if(len(states)==1):
	    newstateslist.append(states)
	else:
	    newstateslist.insert(0,states)
    stateslist=newstateslist
    tables = ""
    colors = {'1':'Green', '0':'Red', '*':'Orange','2':'Green','3':'Green'}
    for states in stateslist:
        htmltable = HTML.Table(header_row=[str(node[0]) for node in nodes])
	vector=[-1]*len(nodes)
	for state in states:
	    for i,s in enumerate(str(state)):
		if vector[i]==-1:
		    vector[i]=s
		elif vector[i]!="*" and vector[i]!=s:
		    vector[i]="*"
        htmltable.rows.append([HTML.TableCell(value,bgcolor=colors[value]) for value in vector])
	tables += str(htmltable)
	tables += "<p>"+str(len(states))+(" states" if len(states)>1 else " state")+"</p>"
    return tables
    
# Similar to htmlShortTables but each cell shows the mean value of the component on all states
def htmlMeanTables(stateslist,nodes):
    tables = ""
    colors = {'1':'Green', '0':'Red', '*':'Orange','2':'Green','3':'Green'}
    # Reorder stateslist to put the complex attractors before
    newstateslist=list()
    for i, states in enumerate(stateslist):
        if(len(states)==1):
	    newstateslist.append(states)
	else:
	    newstateslist.insert(0,states)
    stateslist=newstateslist
    for states in stateslist:
        htmltable = HTML.Table(header_row=[str(node[0]) for node in nodes])
	vector1=[-1]*len(nodes)
	vector2=[-1]*len(nodes)
	for nb,state in enumerate(states):
	    for i,s in enumerate(str(state)):
		if vector1[i]==-1:
		    vector1[i]=s
		    vector2[i]=int(s)
		else:
		    if vector1[i]!="*" and vector1[i]!=s:
 		        vector1[i]="*"
  		    vector2[i]=(vector2[i]*nb+float(s))/(nb+1)
	for i in range(len(vector2)):
	    vector2[i]=int(vector2[i]) if vector2[i] % 1 == 0 else round(vector2[i],2)
        htmltable.rows.append([HTML.TableCell(str(vector2[j]),bgcolor=colors[vector1[j]]) for j in range(len(nodes))])
	tables += str(htmltable)
	tables += "<p>"+str(len(states))+(" states" if len(states)>1 else " state")+"</p>"
    return tables

# Create an html table to display a set of states each on one row
def htmlFullTables(stateslist,nodes):
    # Reorder stateslist to put the complex attractors before
    newstateslist=list()
    for i, states in enumerate(stateslist):
        if(len(states)==1):
	    newstateslist.append(states)
	else:
	    newstateslist.insert(0,states)
    stateslist=newstateslist
    tables=""
    colors = {'1':'Green', '0':'Red', '*':'Orange','2':'Green','3':'Green'}
    for states in stateslist:
        htmltable = HTML.Table(header_row=[str(node[0]) for node in nodes])
	vector=[-1]*len(nodes)
	for state in states:
            htmltable.rows.append([HTML.TableCell(s,bgcolor=colors[s]) for s in str(state)])
	tables += str(htmltable)
	tables += "<p>"+str(len(states))+(" states" if len(states)>1 else " state")+"</p>"
    return tables
    
# Create an html table to display the nodes with the names of the first row,
# the max value on the second and the input value (True/False) on the third
def htmlNodeTable(nodes):
    maxlist=["Max"]
    maxlist.extend([str(node[1]) for node in nodes])
    inputlist=["Input"]
    inputlist.extend([str(node[2]) for node in nodes])    
    nodeslist=["Node"]
    nodeslist.extend([str(node[0]) for node in nodes])      
    print maxlist, inputlist
    htmltable = HTML.Table([maxlist,inputlist],header_row=nodeslist)
    return "<p>Nodes:</p>"+str(htmltable)
    
# Create an HTML report    
def createReport(filename):
    if filename!="":   
        f=open(filename,"w")
        f.close() 
# Append some text to the HTML report    
def appendReport(text,filename):
    if filename!="":   
        f=open(filename,"a")
        f.write(text)
        f.close() 

 # equivalent to itertools.permutations (new in Python 2.6)
def permutations(iterable, r=None):
    # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
    # permutations(range(3)) --> 012 021 102 120 201 210
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return
    indices = range(n)
    cycles = range(n, n-r, -1)
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return    
    
# perturbation Mol1 E1, Mol2 E1 can also be written Mol2 E1, Mol1 E1
def combinations(perturbation):
    perturbelements = perturbation.split(", ")
    permutiterator = permutations(perturbelements)
    return [", ".join(permut) for permut in permutiterator]
   
# Define a simple perturbation from a string like "Rb KO" or "E2F [Rb@0]"  
# Input: perturbstring is a tuple: ("Rb KO", "KO")  
# Output: a tuple (perturbation or None, empty string or error message) 
def defineSimplePerturbation(perturbstring,nodes):
    perturbelements = (perturbstring[0].split()[0],perturbstring[1])
    if len(perturbelements)!=2:
        message = str(perturbstring)+" shoulg be a string with two elements"
        return (None,message)
    else:
        for i in (0,1):
            if perturbelements[i][0]==' ':
                perturbelements[i]=perturbelements[i][1:]
            if perturbelements[i][-1]==' ':
                perturbelements[i]=perturbelements[i][:-1]
        nodeperturb = None
        for node in nodes:
            if str(node)==perturbelements[0]:
                nodeperturb=node
        if nodeperturb==None:
            message = "Unrecognised node in "+str(perturbstring[0])
            return (None,message)
        perturbation = None
        if perturbelements[1]=="KO":
            perturbation = PerturbationFixed(nodeperturb,0)
        elif re.match("E(\d)",perturbelements[1]):
            reg=re.match("E(\d)",perturbelements[1])
            if int(reg.group(1))<0 or int(reg.group(1))>nodeperturb.getMax():
                message = "Invalid perturbation level in "+str(perturbstring[0])
                return (None,message)
            perturbation = PerturbationFixed(nodeperturb,int(reg.group(1)))
        elif re.match("\[(\d),(\d)\]",perturbelements[1]):
            reg=re.match("\[(\d),(\d)\]",perturbelements[1])
            if int(reg.group(1))<0 or int(reg.group(1))>nodeperturb.getMax() or int(reg.group(2))<0 or int(reg.group(2))>nodeperturb.getMax():
                message = "Invalid perturbation range in "+str(perturbstring[0])
                return (None,message)
            perturbation = PerturbationRange(nodeperturb,int(reg.group(1)),int(reg.group(2)))
        elif re.match("\[(\w*)@(\d)\]",perturbelements[1]):
            reg=re.match("\[(\w*)@(\d)\]",perturbelements[1])
            noderegulator = None
            for node in nodes:
                if str(node)==reg.group(1):
                    noderegulator=node
            if noderegulator==None:
                message = "Unrecognised node in "+str(perturbelements[1])
                return (None,message)
            if int(reg.group(2))<0 or int(reg.group(2))>noderegulator.getMax():
                message = "Invalid perturbation level in "+str(perturbstring[0])
                return (None,message)
            perturbation = PerturbationRegulator(nodeperturb,noderegulator,int(reg.group(2)))
    return (perturbation,"")
    
# Define a simple or a multiple perturbation from perturbstringlist:  
# a list of tuples like: [("Rb KO", "KO"), ("CycE [Rb@0]","[Rb@0]")]   
# Output: a tuple (perturbation or None, empty string or error message)   
def definePerturbation(perturbstringlist,nodes):
    if len(perturbstringlist)>1:
        perturbationslist = list()
        for perturbstring in perturbstringlist:
            perturb=defineSimplePerturbation(perturbstring,nodes)
            if perturb[0]==None:
                return(perturb)
            else:
                perturbationslist.append(perturb[0])
        print perturbationslist
        return(PerturbationMultiple(perturbationslist),"")
    else:
        return(defineSimplePerturbation(perturbstringlist[0],nodes))

## Create a report with the nodes of the model
model=g.getModel()
nodes = [(node, node.getMax(), node.isInput()) for node in model.getNodeOrder()]
print "Nodes: (True=Input):"+str(nodes)
print

createReport(freport)
appendReport(htmltitle("Model "+modelname+".zginml"),freport)
appendReport(htmlNodeTable(nodes),freport)


print "------- Simulations WT -------\n"
print "-- Asynchronous attractors WT:"
attractors = simulate_model(g, model)
display_short_states(attractors,nodes)
appendReport(htmltitle("Simulations WT")+\
            htmltextbold("Asynchronous attractors WT:")+\
            htmlMeanTables(attractors,nodes),freport)
    
print "-- Synchronous attractors WT:"
attractors = simulate_model(g, model,1)
display_full_states(attractors,nodes)
appendReport(htmltextbold("Synchronous attractors WT:")+\
             htmlFullTables(attractors,nodes),freport)

perturbations = gs.associated(g, "mutant", False)

print "------- Simulations of perturbations -------\n"
for p1 in perturblist:
    print p1
    foundperturb=False
    p2=None
    for p3 in perturbations:
	if p1==str(p3) or p1 in combinations(str(p3)):
	    foundperturb=True
	    p2=p3
	    break;
    if foundperturb==False:
	#message = "Perturbation "+str(p1)+" not defined in the model"
	p1list = re.findall("(\w+ (KO|E\d*|\[\d,\d\]|\[\w*@\d]))",p1)
        p2tup = definePerturbation(p1list,model.getNodeOrder())
	# p2tup is (Perturbation,"") or (None,"Error message")
        p2 = p2tup[0]
        if p2==None:
           message = "\nImpossible to define the perturbation "+str(p1)+": "+p2tup[1]
           print message+"\n"
   	   appendReport("<p>"+message.replace('\n','<br />')+"</p>",freport)
        #else:
           #message += "\nDefined perturbation "+str(p2)
        
    if p2!=None:
        perturbed = p2.apply(model)
        attractors = simulate_model(g, perturbed)
	print "-- Asynchronous attractors for "+str(p1)+":"
	display_short_states(attractors,nodes)
	appendReport(htmltextbold("Asynchronous attractors for "+str(p1)+":")+\
	             htmlMeanTables(attractors,nodes),freport)
	             	

if freport!="":
    print "Report saved in "+freport
else:
    print "No HTML report asked"
