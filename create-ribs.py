import argparse
import os
from collections import defaultdict
import cPickle as pickle

parser = argparse.ArgumentParser()
parser.add_argument('--prefixes', required=True)
parser.add_argument('--topo', required=True)
parser.add_argument('--dir', required=True)
parser.add_argument('--routes', default=None)
parser.add_argument('--log', action="store_true", default=False)
parser.add_argument('--rib', required=True)

FLAGS = parser.parse_args()

"""
last successful invocation:
python create-ribs.py --prefixes unique-prefixes.txt
        --topo inet-edges.txt
        --dir inet
        --log
        --routes routes
        --rib inet-ribs.csv
"""

def log(s):
    if FLAGS.log:
        print s

def read_topo(fname):
    edges = []
    nodes = []
    with open(fname) as f:
        edges = f.readlines()
        edges = map(lambda e: e.strip().split(' '), edges)
    for u,v in edges:
        nodes.append(u)
        nodes.append(v)
    nodes = list(set(nodes))
    return nodes, edges

def allpairs_shortest_path(nodes, edges):
    dist = defaultdict(lambda: defaultdict(int))
    nexthop = defaultdict(lambda: defaultdict(int))
    for u in nodes:
        for v in nodes:
            if u == v:
                dist[u][v] = 0
            else:
                dist[u][v] = 1000000

    for u,v in edges:
        dist[u][v] = 1

    idx = 0
    N = len(nodes)
    for i in nodes:
        log("%7.2f%% done, computing shortest path for %s" % (idx*100.0/N, i))
        for j in nodes:
            for k in nodes:
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    nexthop[i][j] = k
        idx += 1

    ret = [dict(dist), dict(nexthop)]
    if FLAGS.routes:
        with open(FLAGS.routes, 'w') as f:
            pickle.dump(ret, f)
            log("Dumped nexthop routing table to %s" % FLAGS.routes)
    return ret

def chunk(lst, size):
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def read_prefixes(fname):
    # Returns a list of prefixes
    ret = []
    with open(fname, 'r') as f:
        ret = map(lambda p: p.strip(), f.readlines())
    return ret

def main():
    nodes, edges = read_topo(FLAGS.topo)
    log("Found %d nodes" % len(nodes))
    routes = dict()
    if FLAGS.routes and os.path.exists(FLAGS.routes):
        with open(FLAGS.routes) as f:
            dist, routes = pickle.load(f)
        log("Reading existing routing table from file `%s'" % FLAGS.routes)
    else:
        dist, routes = allpairs_shortest_path(nodes, edges)

    # Now assign prefixes to nodes
    prefixes = read_prefixes(FLAGS.prefixes)
    per_node_size = (len(prefixes)+len(nodes)-1)/ len(nodes)
    prefixes = chunk(prefixes, per_node_size)
    print len(prefixes), len(nodes)

    # Now write each node's RIB file
    assert(len(prefixes) == len(nodes))
    if not os.path.exists(FLAGS.dir):
        os.makedirs(FLAGS.dir)

    node_prefixes = defaultdict(list)
    for node, owned_prefixes in zip(nodes, prefixes):
        outfile = '%s/prefix-%s.txt' % (FLAGS.dir, node)
        node_prefixes[node] = owned_prefixes
        with open(outfile, 'w') as f:
            f.write('\n'.join(owned_prefixes))
        log("wrote %s" % (outfile))

    # Now write the routes file
    routefile = '%s/routes.csv' % FLAGS.dir
    with open(routefile, 'w') as f:
        print >>f, "src,dst,nexthop,metric"
        for u in routes.keys():
            for v in routes[u].keys():
                print >>f, "%s,%s,%s,%d" % (u, v, routes[u][v], dist[u][v])
    log("write %s" % routefile)

    # Now create the ribs file
    with open(FLAGS.rib, 'w') as f:
        print >>f, "dstprefix,local,remote"
        count = 0
        N = len(routes)
        for u in routes.keys():
            for v in routes[u].keys():
                for prefix in node_prefixes[v]:
                    print >>f, "%s,%s,%s" % (prefix,u,v)
            count += 1
            log("[%3d/%3d: %6.3f%%] Done %20s (%11d bytes, %.3fGB)" % (count, N, count*100.0/N, u, f.tell(), f.tell()/1e9))
    log("wrote %s" % FLAGS.rib)
if __name__ == "__main__":
    main()

