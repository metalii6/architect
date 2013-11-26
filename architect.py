#!/usr/bin/env python
import argparse

# get graph from SGA's asqg; then load/store from internal asqg-like format
from graph_load import load_from_sga_asqg, save_graph, load_graph

# save file in dot format
from visualize import to_graphviz_dot, to_graphviz_dot_with_intervals, \
         			  to_graphviz_dot_with_double_intervals

# visualize parts of assembly graph
from visualize import print_connection

# examine misassemblies
from misassemblies import examine_misassemblies

# collect statistics about the graph
from graph_stats import print_stats

# contract edges that are similar
from contraction import contract_edges

# graph simplification operation that involve counting wells (PMMP)
from pmpp import resolve_repeats, delete_spurious_edges

# method to verify graph correctness
from verificator import examine_repeats, examine_connections

# remove some transitive edges
from remove_transitive import pop_triangles

# resolve short repeats in the graph by using lengths
from resolve_repeats import resolve_short_repeats

from libkuleshov.debug import keyboard

##############################################################################

def main():
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(title='Commands')

	## LOAD

	load_parser = subparsers.add_parser('load')
	load_parser.set_defaults(func=load)

	load_parser.add_argument('--asqg', required=True)
	load_parser.add_argument('--out', required=True)

	## CONTRACT

	contract_parser = subparsers.add_parser('contract')
	contract_parser.set_defaults(func=contract)

	contract_parser.add_argument('--inp', required=True)
	contract_parser.add_argument('--out', required=True)
	contract_parser.add_argument('--dot')
	contract_parser.add_argument('--stats')
	contract_parser.add_argument('--masm', action='store_true')

	## DELETE SPURIOUS

	spurious_parser = subparsers.add_parser('prune')
	spurious_parser.set_defaults(func=spurious)

	spurious_parser.add_argument('--inp', required=True)
	spurious_parser.add_argument('--out', required=True)
	spurious_parser.add_argument('--dot')
	spurious_parser.add_argument('--stats')
	spurious_parser.add_argument('--masm', action='store_true')

	## RESOLVE SHORT REPEATS

	short_repeats_parser = subparsers.add_parser('resolve-short-repeats')
	short_repeats_parser.set_defaults(func=short_repeats)

	short_repeats_parser.add_argument('--inp', required=True)
	short_repeats_parser.add_argument('--out', required=True)
	short_repeats_parser.add_argument('--dot')
	short_repeats_parser.add_argument('--stats')
	short_repeats_parser.add_argument('--masm', action='store_true')

	## RESOLVE REPEATS BY WELLS

	repeats_parser = subparsers.add_parser('resolve')
	repeats_parser.set_defaults(func=repeats)

	repeats_parser.add_argument('--inp', required=True)
	repeats_parser.add_argument('--out', required=True)
	repeats_parser.add_argument('--dot')
	repeats_parser.add_argument('--stats')
	repeats_parser.add_argument('--masm', action='store_true')

	## REMOVE TRANSITIVE EDGES

	remove_transitive_parser = subparsers.add_parser('remove-transitive')
	remove_transitive_parser.set_defaults(func=remove_transitive)

	remove_transitive_parser.add_argument('--inp', required=True)
	remove_transitive_parser.add_argument('--out', required=True)
	remove_transitive_parser.add_argument('--dot')
	remove_transitive_parser.add_argument('--stats')
	remove_transitive_parser.add_argument('--masm', action='store_true')

	## VIEW STATISTICS

	view_parser = subparsers.add_parser('view')
	view_parser.set_defaults(func=view)

	view_parser.add_argument('--inp', required=True)
	view_parser.add_argument('--edge', type=int)
	view_parser.add_argument('--vertex', type=int)
	view_parser.add_argument('--dot')

	args = parser.parse_args()
	args.func(args)

###############################################################################
## FUNCTIONS

def load(args):
	g = load_from_sga_asqg(args.asqg)

	save_graph(g, args.out + '.asqg', 
        		  args.out + '.containment')

def contract(args):
	g = load_graph(args.inp + '.asqg', args.inp + '.containment')

	contract_edges(g)
	save_optional_output(g, args)

	save_graph(g, args.out + '.asqg', 
        		  args.out + '.containment')

def spurious(args):
	g = load_graph(args.inp + '.asqg', 
        	       args.inp + '.containment')

	for i in xrange(4):
	  examine_connections(g, conservative='very')
	  delete_spurious_edges(g, conservative='very')
	  contract_edges(g)

	print 'SECOND RUN'

	examine_connections(g, conservative='yes')
	delete_spurious_edges(g, conservative='yes')

	save_optional_output(g, args)
	examine_misassemblies(g)

	save_graph(g, args.out + '.asqg', 
        		  args.out + '.containment')

def short_repeats(args):
	g = load_graph(args.inp + '.asqg', 
        	       args.inp + '.containment')

	resolve_short_repeats(g)
	save_optional_output(g, args)

	save_graph(g, args.out + '.asqg', 
        		  args.out + '.containment')

def repeats(args):
	g = load_graph(args.inp + '.asqg', 
        	       args.inp + '.containment')

	resolve_repeats(g)
	examine_repeats(g)
	save_optional_output(g, args)

	save_graph(g, args.out + '.asqg', 
        		  args.out + '.containment')

def remove_transitive(args):
	g = load_graph(args.inp + '.asqg', 
        	       args.inp + '.containment')

	pop_triangles(g)

	save_graph(g, args.out + '.asqg', 
        		  args.out + '.containment')

def view(args):
	g = load_graph(args.inp + '.asqg', 
        	       args.inp + '.containment')

	if args.edge:
		print_connection(g.get_edge(args.edge))
	elif args.dot:
		to_graphviz_dot_with_intervals(g, args.dot)

###############################################################################
## HELPERS

def save_optional_output(g, args):
	if args.dot:
		to_graphviz_dot_with_intervals(g, args.dot)
	if args.stats:
		print_stats(g, args.stats)
	if args.masm:
		examine_misassemblies(g)


if __name__ == '__main__':
	main()