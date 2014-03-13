1. Download topology from
http://www.cs.washington.edu/research/networking/rocketfuel

And create an edge file which has all edges in the topology.  Each
line consists of "A<space>B" where A and B are neighbours in the
topology.

We have some sample edges in the INET topology graph here:
inet-edges.txt

2. Download BGP prefixes from
http://routeviews.org/bgpdata/2013.08/RIBS/

3. Download bgpparser from irl.cs.ucla.edu/software/bgpparser.html
Compile and get the bin/bgpparser executable.

4. Extract all prefixes from the RIB file:

bin/bgpparser -f rib.20130801.0000 |  \
		grep PREFIX |  \
		sed -e 's/PREFIX//g' -e 's/<//g' -e 's|/>||g' -e 's/>//g' |  \
		awk '{ print $1 }' > allprefixes.txt

This can take a while....

5. Uniq them:
cat allprefixes.txt | uniq > unique-prefixes.txt

You don't need to sort before doing uniq because the prefixes are
lexicographically sorted.

6. Create the routing table for each router:

python create-ribs.py --prefixes unique-prefixes.txt \
       --topo inet-edges.txt \
       --dir topo \
       --rib inet-ribs.csv \
       --log \
       --routes routes

It will create one file routes in the current directory to cache the
all-pairs shortest path computation. These routes were computed using
Floyd-Warshall shortest path.

Inside tmp-dir, the script will create a txt file for each router that
contains the prefixes that is owned by the router.  One prefix per
line in ip/len format.

It will also generate dir/routes.csv with the following format:

   <source router>,<dest router>,<next hop router>,<metric>

   where metric is the length of the shortest path to the destination
   router (neighbours have length 1).

To generate ribs with the following format:

    <Dest IP Prefix>,<Local Router>,<Remote Router>

We basically do the following:

For each src in inet/routes.csv, construct rib-$src.csv as follows:
   For each dst in (src,dst) load all prefixes from inet/$dst.txt
       Insert prefix,dst into the rib-$src.txt

This will be output to inet-ribs.csv.

