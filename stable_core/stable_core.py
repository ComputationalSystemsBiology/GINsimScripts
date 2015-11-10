import jarray

g = gs.open(gs.args[0])
istates = gs.associated(g, "initialState", True).getInitialStates()
ssrv = gs.service("stable")

def copy_path(values, coreNodes):
    n = len(coreNodes)
    path = jarray.zeros(n, 'b')
    i = 0
    for idx in coreNodes:
        path[i] = values[idx]
        i += 1
    
    return path

def unfold_rec(values, jokers, stack, coreNodes):
    if len(jokers) < 1:
        path = copy_path(values, coreNodes)
        if False:
            for p in stack:
                idx = 0
                ident = True
                for v in p:
                    if v != path[idx]:
                        ident = False
                        break
                    idx += 1
                if ident:
                    return
        stack.append( path )
        return
    
    idx, mx = jokers[0]
    njk = jokers[1:]
    for v in xrange(mx):
        values[idx] = v
        unfold_rec(values, njk, stack, coreNodes)
    values[idx] = -1

def unfold(values, maxvalues, stack, coreNodes):
    n = len(values)
    jokers = [ (idx, maxvalues[idx]+1) for idx in xrange(n) if values[idx] == -1 ]
    unfold_rec(values, jokers, stack, coreNodes)

    return stack

def find_stable_states(model, nodeOrder):

    maxvalues = []
    coreNodes = []
    inputNodes = []
    coreOrder = []
    idx = 0
    for n in nodeOrder:
        if n.isInput():
            inputNodes.append(idx)
        else:
            coreNodes.append(idx)
            coreOrder.append(n)
            maxvalues.append( n.getMaxValue() )
        idx += 1
    unfoldNodes = xrange(len(coreNodes))

    searcher = ssrv.getStableStateSearcher(model)
    searcher.call()
    paths = searcher.getPaths()
    values = paths.getPath()
    stack = []
    for l in paths:
        path = copy_path(values, coreNodes)
        #stack.append(l)
        unfold(path, maxvalues, stack, unfoldNodes)

    for path in stack:
        name = istates.nameState(path, coreOrder)
        if name is None:
            name = ""
        state = ""
        for v in path:
            if v < 0: state += "*"
            else: state += "%d" % v
        print name + "\t" + state


# Get stable states for all perturbations
model = g.getModel()

find_stable_states(model, g.getNodeOrder())

