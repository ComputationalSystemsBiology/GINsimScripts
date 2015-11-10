from org.ginsim.common.callable import BasicProgressListener
from org.ginsim.service.export.nusmv import NuSMVConfig


g = gs.open(gs.args[0])
sreduction = gs.service("reduction")
ssim = gs.service("simulation")
sscc = gs.service("SCC")
ssmv = gs.service("NuSMV")

# dummy progress listener
plist = BasicProgressListener()


def run_simulation(g, model):
    sim_idx = 0
    # perform a reduction if available
    reductions = gs.associated(g, "modelSimplifier", True)
    if reductions is not None and len(reductions) > 0:
        print "reduce the model"
        model = reductions[0].apply(model);
        g = sreduction.getReconstructionTask(model, g).call()
        sim_idx += 1 # work around the extra parameter added by the reduction step
    else:
        print "No reduction"


    # Prepare the simulation
    simparameter = gs.associated(g, "reg2dyn_parameters", True)
    parameter = simparameter[sim_idx]
    simulator = ssim.get(model, plist, parameter)

    # Actually run the simulation with the progress listener
    stg = simulator.do_simulation()
    
    # show component names
    for node in model.getNodeOrder():
        print node,
    print

    # get the graph of the SCC and find attractors
    sccgraph = sscc.getSCCGraph(stg)
    for component in sccgraph.getNodes():
        out = sccgraph.getOutgoingEdges(component)
        if out is None or len(out) == 0:
            for node in component.getContent():
                print node,
            print

smvconfig = NuSMVConfig(g)
smvfilename = gs.args[0]+".smv"

model = g.getModel()

run_simulation(g, model)
ssmv.run(smvconfig, smvfilename)
print

perturbations = gs.associated(g, "mutant", False)
if perturbations:
    idx = 0
    for p in perturbations:
        perturbed = p.apply(model)
        smvconfig.updateModel(perturbed)
        smvfilename = "%s_perturbation_%s.smv" % (gs.args[0], idx)
        ssmv.run(smvconfig, smvfilename)
        print p
        run_simulation(g,perturbed)
        print
	idx+=1


