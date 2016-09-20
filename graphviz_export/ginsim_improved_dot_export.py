# Example of a CL
# java -Xmx1G -jar GINsim-2.9.4-with-deps.jar -s ./ginsim_improved_dot_export.py ginsim_model.zginml graphviz_export.dot 


from pprint import pprint

# Get the GINsim file (first argument), and read GINsim model data from it
g = gs.open(gs.args[0])

# Get the model
model = g.getModel()
	
# Get ST graph in GraphViz format (dot)
filename = gs.args[1]

import re,sys 

# Modify the exported file to include Node status information
tempdot = open(filename, "r")
fulldot = open(filename+"_improved.dot", "w")
for line in tempdot:
	if re.match("\s+[01]+ \[.*\];", line):
		nodeid = list(line.split(None, 1)[0]) # To get the first word, then split into an array of chars
		nodesinfo = ', '.join("%s=%s" % t for t in zip([str(n).replace('-','_') for n in model.getNodeOrder()], nodeid))
		line = line.replace("];", ", "+nodesinfo+"];")
	if re.match("\s+[01]+ -> [01]+;", line):
		edgenodes = re.findall(r"[01]+", line)
		moreOrLess = int(edgenodes[0]) - int(edgenodes[1])
		chMoreOrLess = '+'
		if moreOrLess > 0:
			chMoreOrLess = '-'
		#print chMoreOrLess
		line = line.replace(";", " [label=\""+chMoreOrLess+"\"];") #, [transition=\""+chMoreOrLess+"\"];
	fulldot.write(line)
tempdot.close()
fulldot.close()



