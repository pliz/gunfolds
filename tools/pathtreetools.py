import sys

sys.path.append('./tools/')
from pathtree import PathTree
from ortools.constraint_solver import pywrapcp
from matplotlib.cbook import flatten
from functools import wraps
import numpy as np
import ipdb


def ptloopnum(pt):
    """
    Given a PathTree object returns the number of loop in it
    :param pt: PathTree object
    :return: number of loops (n)
    """

    def ptn(pt, n=0):
        for e in pt.loopset:
            if type(e) is int:
                n += 1
                continue
            n += ptn(e, n=1)
        return n

    return ptn(pt)


def ptnodenum(pt):
    """
    Given a PathTree object returns the number of latents that comprise it
    :param pt: PathTree object
    :return: number of nodes (n)
    """
    n = pt.preset - 1

    def ptn(pt, n=0):
        for e in pt.loopset:
            if type(e) is int:
                n += e - 1
                continue
            n += ptn(e, n=1)
        return n

    return n + ptn(pt)


def ptelement(pt, w):
    """
    An element generated by a PathTree with a given weight setting
    :param pt: PathTree
    :param w: a list of weights
    :return: an integer
    """
    n = pt.preset

    def sumloops(pt, w):
        n = 0
        ls = list(pt.loopset)
        for i in range(len(ls)):
            if type(ls[i]) is int:
                n += w[i] * ls[i]
                continue
            n += w[i][0] * ls[i].preset \
                 + min(1, w[i][0]) * sumloops(ls[i], w[i][1])
        return n

    return n + sumloops(pt, w)


def weights_pt(pt, weights):
    c = [0]

    def crawl(pt, w, c):
        wl = []
        for e in pt.loopset:
            if type(e) is int:
                wl.append(w[c[0]])
                c[0] += 1
                continue
            ww = w[c[0]]
            c[0] += 1
            wl.append([ww, crawl(e, w, c)])
        return wl

    return crawl(pt, weights, c)


def extraloops_pt(pt, loops):  # loops are tuples (loop, weight)
    c = [0]

    def crawl(pt, l, c):
        first = [l[c[0]]]
        wl = []
        for e in pt.loopset:
            c[0] += 1
            if type(e) is int:
                wl.append(l[c[0]])
                continue
            wl.append(crawl(e, l, c))
        return first + [wl]

    return crawl(pt, loops, c)


def ptelement_extraloop(pt, w, eloops):
    """
    An element generated by a PathTree with a given weight setting and extra loops on each level
    :param pt: PathTree
    :param w: a list of list of weights
    :param eloops: a list of tuples with lengths of extra loops and their weights
    :return: an integer
    """
    n = pt.preset + eloops[0][0] * eloops[0][1]

    def sumloops(pt, w, lps):
        ls = list(pt.loopset)
        n = 0
        for i in range(len(ls)):
            if type(ls[i]) is int:
                n += w[i] * ls[i] + min(1, w[i]) * lps[i][0] * lps[i][1]
                continue
            n += w[i][0] * ls[i].preset \
                 + min(1, w[i][0]) * (lps[i][0][0] * lps[i][0][1] + sumloops(ls[i], w[i][1], lps[i][1]))
        return n

    return n + sumloops(pt, w, eloops[1])


def isptelement_el(el, pt, w, eloops):
    return el == ptelement_extraloop(pt, w, eloops)


def isptsubset_el(elist, pt, w, eloops):
    for i in range(elist[-1]):
        if isptelement_el(i, pt, w, eloops):
            if not i in elist:
                return False
    return True


def isrightpt(el, elist, pt, w, eloops):
    for i in range(elist[-1]):
        if isptelement_el(i, pt, w, eloops):
            if not i in elist:
                return False
        if i == el and not isptelement_el(i, pt, w, eloops):
            return False
    return True


def ptelements(pt, seqlen=100, verbose=False, maxloop=100):
    """
    Generate first `seqlen` elements from a pathtree
    :param pt: a path tree object from pathtree.py
    :param seqlen: number of elements to generate in ascending order
    :param verbose: whether to print debugging information
    :return: a list of elements
    """
    solver = pywrapcp.Solver("pt-elements")

    # declare variables
    weights = []
    N = ptloopnum(pt)
    for i in range(N):
        weights.append(solver.IntVar(0, maxloop, "w[%04i]" % i))

    # declare constraints
    # solver.Add()

    # run the solver
    solution = solver.Assignment()
    solution.Add(weights)
    db = solver.Phase(weights,
                      solver.CHOOSE_FIRST_UNBOUND,
                      solver.ASSIGN_MIN_VALUE)
    solver.NewSearch(db)

    num_solutions = 0
    els = set()
    while solver.NextSolution():
        w = [x.Value() for x in weights]
        num_solutions += 1
        els.add(ptelement(pt, w))
        if len(els) == seqlen:
            break
    solver.EndSearch()

    # output solutions
    if verbose:
        print "num_solutions:", num_solutions
        print "failures:", solver.Failures()
        print "branches:", solver.Branches()
        print "WallTime:", solver.WallTime()

    return list(els)


def isptelement(pt, element, verbose=False, maxloop=100):
    """
    Check if an integer element is in the weight set represented by the path tree
    :param pt: a path tree object from pathtree.py
    :param element: an integer to check for presence in the weight
    :param verbose: whether to print debugging information
    :return: True or False
    """
    solver = pywrapcp.Solver("isptelement")

    # declare variables
    weights = []
    N = ptloopnum(pt)
    if not N:
        return element == pt.preset
    for i in range(N):
        weights.append(solver.IntVar(0, maxloop, "w[%04i]" % i))

    wpt = weights_pt(pt, weights)

    # declare constraints
    solver.Add(element == ptelement(pt, wpt))

    # run the solver
    solution = solver.Assignment()
    solution.Add(weights)
    db = solver.Phase(weights,
                      solver.CHOOSE_FIRST_UNBOUND,
                      solver.ASSIGN_MIN_VALUE)
    solver.NewSearch(db)

    solution_exists = False
    while solver.NextSolution():
        solution_exists = True
        break
    solver.EndSearch()

    # output solutions
    if verbose:
        print "failures:", solver.Failures()
        print "branches:", solver.Branches()
        print "WallTime:", solver.WallTime()

    return solution_exists


def loops_and_weights(solver, loops, weights):
    """
    Add constraints to solver that make sure loops are not generated if subtree is not active due to a zero weight upstream
    :param solver:
    :param loops:
    :param weights:
    :return:
    """

    def recurse(s, l, w):
        for ww, ll in zip(w, l):
            if type(ww) is list:
                for e in flatten(ll):
                    s.Add((ww[0] == 0) <= (e == 0))
                recurse(s, ll[1:], ww[1:])
            else:
                for e in flatten(ll):
                    s.Add((ww == 0) <= (e == 0))

    recurse(solver, loops[1], weights)


def eloops_simplify(eloops):
    l = []
    for e in eloops:
        if type(e) is list:
            l.append(eloops_simplify(e))
        else:
            l.append(int(e[0].Value()))
    return l


def ptaugmented(pt, eloops):
    def augment(pt, ls):
        pre = pt.preset
        loop = pt.loopset
        s = set()
        if ls[0]:
            s.add(ls[0])
        for l, el in zip(loop, ls[1]):
            if type(l) is int:
                if not el:
                    s.add(l)
                else:
                    s.add(PathTree({el}, pre=l))
                continue
            s.add(augment(l, el))

        return PathTree(s, pre=pre)

    t = augment(pt, eloops)

    return t


def ptsubset(pt, elist):
    for i in range(elist[-1]):
        if isptelement(pt, i) and not i in elist:
            return False
    return True


def smallest_pt(ptlist):
    if ptlist:
        idx = np.argsort(map(ptnodenum, ptlist))
        sol = ptlist[idx[0]]
    else:
        sol = None
    return sol


def pairprint(pt1, pt2, k=40):
    print np.c_[pt2seq(pt1, k), pt2seq(pt2, k)]


def etesteq(pt1, pt2, k=100):
    a1 = np.asarray(pt2seq(pt1, k))
    a2 = np.asarray(pt2seq(pt2, k))
    return np.sum(a1-a2) == 0


def keeptreegrow(pt, e, seq, cutoff=10):
    t = None
    while t is None:
        t = growtree(pt, e, seq, cutoff=cutoff)
        cutoff += 10
    return t


def seq2pt(seq, verbose=False, cutoff=100):
    if not seq: return None
    pt = PathTree({}, pre=seq[0])
    for e in seq[1:]:
        if verbose: print e
        pt = keeptreegrow(pt, e, seq, cutoff=cutoff)
    return pt


def growtree(pt, element, ref_elements, verbose=False, maxloop=100, cutoff=100):
    """
    Add a loop with the minimal length to a path tree to enable it to generate a given element and still be a subset of a given list
    :param pt: a path tree object from pathtree.py
    :param element: an integer to check for presence in the weight
    :param ref_elements: a (finite) list that should be a superset of numbers generated by the new path tree, for numbers smaller than tosubset[-1]
    :param verbose: whether to print debugging information
    :return: a PathTree augmented with a new loop
    """
    solver = pywrapcp.Solver("loop_an_element")

    # PathTree already can generate that number. Just to foolproof
    if isptelement(pt, element):
        return pt

    # declare variables
    weights = []  # weights denoting how many times a loop is active (marginalized)
    loops = []  # extra loops that can be potentially added
    lweights = []  # weights for the extra loops (marginalized out in the end)
    ltuples = []  # tuple list to hold loops and weights together

    N = ptloopnum(pt)  # number of loops in the PathTree
    for i in range(N):
        weights.append(solver.IntVar(0, maxloop, "w[%04i]" % i))

    for i in range(N + 1):
        w = solver.IntVar(0, maxloop, "lw[%04i]" % i)
        l = solver.IntVar(0, maxloop, "l[%04i]" % i)
        lweights.append(w)  # loop related weight
        loops.append(l)
        ltuples.append((l, w))

    eloops = extraloops_pt(pt, ltuples)
    ws = weights_pt(pt, weights)

    # declare constraints
    solver.Add(solver.MemberCt(ptelement_extraloop(pt, ws, eloops), ref_elements))
    solver.Add(element == ptelement_extraloop(pt, ws, eloops))  # make sure the element can be generated
    solver.Add(solver.Count(loops, 0, len(loops) - 1))  # only one loop is on
    solver.Add(solver.Count(lweights, 0, len(lweights) - 1))  # only one loop is weighted
    for i in range(len(lweights)):
        solver.Add((lweights[i] == 0) <= (loops[i] == 0))  # if a loop has weight zero then it can't be active
        #solver.Add(lweights[i] >= loops[i])
    loops_and_weights(solver, eloops, ws)  # if a subtree is off (weight zero) no need to add loops

    # run the solver
    solution = solver.Assignment()
    solution.Add(loops)
    db = solver.Phase(loops + lweights + weights,
                      solver.CHOOSE_FIRST_UNBOUND,
                      solver.ASSIGN_MIN_VALUE)
    solver.NewSearch(db)

    numsol = 0
    pts = []
    while solver.NextSolution():
        #print numsol,
        new_pt = ptaugmented(pt, eloops_simplify(eloops))
        if verbose:
            print "trying PathTree: ", new_pt
        if ptsubset(new_pt, ref_elements):
            pts.append(new_pt)
            if verbose:
                print "OK PathTree: ", pts[-1]
        numsol += 1
        if numsol >= cutoff:
            break
    solver.EndSearch()

    # output solutions
    if verbose:
        print "solutions:", numsol
        print "failures:", solver.Failures()
        print "branches:", solver.Branches()
        print "WallTime:", solver.WallTime()
        print "for ", element, "solutions found ", numsol

    return smallest_pt(pts)


def pt2seq(pt, num):
    if not pt.loopset:
        return [pt.preset]
    i = 0
    s = set()
    while len(s) < num:
        if isptelement(pt, i, maxloop=10 * num):
            s.add(i)
        i += 1
    l = list(s)
    l.sort()
    return l


def s2spt(s):  # convert edge set to pt
    ss = set()
    for e in s:
        if type(e) is int:
            ss.add(PathTree({0}, pre={e}))
            continue
        ss.add(e)
    return ss


def spt_elements(spt, num):
    """
    Generate numbers from a set of PathTrees
    :param spt: set of PathTrees
    :param num: number of elements (from the first) to generate
    :return: list of num numbers
    """
    i = 0
    s = set()
    while len(s) < num:
        if issptelement(spt, i):
            s.add(i)
        i += 1
    return list(s)


def issptelement(spt, element):
    a = False
    for pt in s2spt(spt):
        a = a or isptelement(pt, element)
    return a
