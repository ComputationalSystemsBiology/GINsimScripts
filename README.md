# GINsim scripts repository

Model analysis and simulations can be performed automatically in GINsim (http://ginsim.org/) with python scripts.

## Basics and resources

  * To get the full list of services accessible in script mode:
```
  java -jar GINsim.jar -s
```

  * [API Documentation (javadoc)](http://doc.ginsim.org/devel/apidocs/index.html?overview-summary.html)

  * General usage:
```
  java -jar GINsim.jar -s script.py model.zginml
```

## Example scripts

This repository contains a list of ready-to-use scripts.

  * stable_core.py computes the stable states of a model without simulation.

  * simulation_attractors.py performs simulations on the model to obtain all attractors, for the unperturbed model and also for each perturbation defined in the model. The update policy of the first defined parameter is used.

  * simulation_attractors_exportsmv.py does the same but exports also the unperturbed model and each perturbed model into a SMV file.

  * attractors.py finds the attractors of the unperturbed model (asynchronous and synchronous) and saves the result in a html file. If a file with a list of perturbations is provided (one perturbation per line), the attractors (asynchronous) for each perturbation are also saved in the report.
     * Usage: ```java -jar GINsim.jar -s attractors.py model.zginml -p perturbations.txt -r report.html```
     * The script requires the module [HTML.py](http://www.decalage.info/en/python/html) whose path has to be copied at the beginning of the script.


## Code snippets:

### Basics

  * Open a GINsim file (zginml)

```
  g = gs.open("my_model.zginml")
```

### Initial states

  * Get each initial state name and the table containing the __initial state__ values

```
  sinit = gs.associated(g, "initialState", True)
  for i in sinit.getInitialStates():
    print(i.getName())
    print(i.getMaxValueTable())
```

  * Get each initial state name and the table containing the __input__ values

```
  initStates = gs.associated(g, "initialState", True)
  for i in initStates.getInputConfigs():
    print(i.getName())
    print(i.getMaxValueTable())
```

  * Get each initial state name and values one by one

```
  initStates = gs.associated(g, "initialState", True)
  for i in initStates.getInputConfigs():
    print(i.getName())
    for n in i.getMaxValueTable():
      print(n, i.getMaxValueTable()[n])
```

  * Access the names of the input/normal nodes

```
  sinit = gs.associated(g, "initialState", True)
  # Input nodes
  print(sinit.getInputNodes())
  # Other nodes
  print(sinit.getNormalNodes())
```

### Perturbations

  * Get the list of available perturbations

```
  perturbations = gs.associated(g, "mutant", False)
  print(perturbations)
  for p in perturbations:
    print(p)
    print(p.component)
    print(p.value)
```

### Simulation parameters

  * Get parameter names

```
  simparameter = gs.associated(g, "reg2dyn_parameters", True)
  print(simparameter)
```

  * Print name and description of all parameter sets

```
  model = g.getModel()
  for params in simparameter:
    print(params.getName())
    print(params.getDescr(model.nodeOrder))
```

  * Get all defined parameter sets and for each one get its update method (priorityDefinition: synchronous/asynchronous), its initial values, and input values 

```
  simparameter = gs.associated(g, "reg2dyn_parameters", True)
  for sp in simparameter:
    print(sp.getName())
    print(sp.getPriorityDefinition())
    for ins in sp.getInitialState().keySet():
      print(ins.getName())
      print(ins.getMaxValueTable())
    for ins in sp.getInputState().keySet():
      print(ins.getName())
      print(ins.getMaxValueTable())
    print
```

### Running simulations, finding stable states...

  * Get the model

```
  model = g.getModel()
```

  * Apply a perturbation to a given model

```
  model = perturbation.apply(model)
```

  * Perform a model simulation using some parameters (see above how to access them). Get back the State Transition Graph.

```
  # Create a dummy progress listener (needed by simulation function)
  from org.ginsim.common.callable import BasicProgressListener
  plist = BasicProgressListener()
  # Get the service
  ssim = gs.service("simulation")
  # Perform simulation
  stg = ssim.get(model, plist, parameter).do_simulation()
```

  * Get the SCC graph of a State Transition graph.

```
  # Get the service
  sscc = gs.service("SCC")
  # Get the SCC graph, stg being here a State Transition graph
  sccgraph = sscc.getSCCGraph(stg)
```

  * Find stable states of a STG

```
  for state in stg.getNodes():
    outedges = stg.getOutgoingEdges(state)
    if outedges is None or len(outedges) == 0:
      # Do something
```


### Exports

  * A graph (e.g. a big STG) can be exported to a set of formats like Biolayout (using biolayoutExport() function), GraphViz (using graphvizExport() function) and Cytoscape (using cytoscapeExport() function). These tools can be more suitable to visualise big graphs.

```
  # Example to export in GraphViz format (.dot) :
  # Get service to export graph structure
  sgs = gs.service("structure-export")
  # Export structure in GraphViz format
  # (stg: state transition graph, filename: file path as string)
  sgs.graphvizExport(stg, stg.getNodes(), stg.getEdges(), filename)
```

  * Modify a GraphViz file (.dot) to include for each Node the corresponding gene names and its state (they will be added to the file as Node attributes).

```
  # Open the file exported by GINsim
  exporteddot = open(filename, "r")
  # Create a new file which will contain the copied and additional information
  modifieddot = open(filename2, "w")
  for line in exporteddot:
    # If the line contains a Node definition
    # its label will describe the status of each gene of the GRN (e.g. 0010011)
    if re.match("\s+[01]+ \[.*\];", line):
      # Extract the label name and split char by char
      nodeid = list(line.split(None, 1)[0])
      # Add the attributes using the Node names included in the Model object
      # Also replace '-' by '_' or import can fail (ex: in Gephi)
      nodesinfo = ', '.join("%s=%s" % t for t in zip([str(n).replace('-','_') for n in model.getNodeOrder()], nodeid))
      # Change the original line of the dot file
      line = line.replace("];", ", "+nodesinfo+"];")
    # Print line in the new file
    modifieddot.write(line)
  # Close the files
  exporteddot.close()
  modifieddot.close()
```
