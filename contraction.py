from libkuleshov.dna import reverse_complement
from libkuleshov.debug import keyboard
from string_graph import OverlapVertex, no_diedge

def contract_edges(g, E=None):
	if not E:
		candidate_edges = set(g.edges)
	else:
		candidate_edges = E

	remove_loops(g)
	# remove_parallel_edges

	while candidate_edges:
		if len(candidate_edges) % 10000 == 0:
			print len(candidate_edges)
		e = candidate_edges.pop()
		# if e.v1.id_ == '6074-1_1044-1': keyboard()
		E = e.v1.edges | e.v2.edges
		if can_be_contracted(e): 
			contract_edge(g,e)
			# for f in E:
				# assert len(f.connection) == 2

def remove_loops(g):
	for e in g.edges:
		if e.v1 == e.v2:
			g.remove_edge(e)
			e.v1.head_edges.discard(e)
			e.v1.tail_edges.discard(e)

def remove_parallel_edges(g):
	visited_pairs = set()
	E = list(g.edges)
	for e in E:
		s = frozenset([e.v1, e.v2])
		if s not in visited_pairs:
			visited_pairs.add(s)
		else:
			g.remove_edge(e)
			e.v1.disconnect_edge(e)
			e.v2.disconnect_edge(e)

def can_be_contracted(e):
	v1, v2 = e.v1, e.v2

	# we cannot contract loops:
	if v1 == v2: return False

	# an edge can be contracted if it connects v1, v2 at poles x, y
	# and it is the only edge at pole x in v1
	# and the only edge at pole y in v2

	if e.connection[v1] == 'H' and len(v1.head_edges) == 1:
		if e.connection[v2] == 'H' and len(v2.head_edges) == 1:
			return True
		elif e.connection[v2] == 'T' and len(v2.tail_edges) == 1:
			return True
	elif e.connection[v1] == 'T' and len(v1.tail_edges) == 1:
		if e.connection[v2] == 'H' and len(v2.head_edges) == 1:
			return True
		elif e.connection[v2] == 'T' and len(v2.tail_edges) == 1:
			return True

	return False

def contract_edge(g,e):
	if e.is_overlap_edge:
		contract_overlap_edge(g,e)
	elif e.is_scaffold_edge:
		contract_scaffold_edge(g,e)
	else:
		raise ValueError('Invalid edge type found')

def contract_scaffold_edge(g, e):
	v1, v2 = e.v1, e.v2

	assert e in v1.edges
	assert e in v2.edges

	# print
	# print e.id_, e.connection[v1], e.connection[v2]
	# print v1.id_, [f.id_ for f in v1.head_edges], [f.id_ for f in v1.tail_edges]
	# print v2.id_, [f.id_ for f in v2.head_edges], [f.id_ for f in v2.tail_edges]

	_orient_th(g, e, v1, v2)
	v1, v2 = e.v1, e.v2

	assert e.connection[v1] == 'T' and e.connection[v2] == 'H'

	orientation = e.orientation

	# remove vertices and edge
	g.remove_vertex_from_index(v1)
	g.remove_vertex_from_index(v2)
	g.remove_edge(e)

	# build new vertex
	# FIXME: refactor; make this method private
	new_id = g.vertex_id_generator.get_id()

	# FIXME: handle properly the case of negative distance
	distance = max(0, e.distance)
	padding = 'N' * 10

	if orientation == 0:
		new_seq = v1.seq + padding + v2.seq
	elif orientation == 1:
		new_seq = v1.seq + padding + reverse_complement(v2.seq)
	else:
		exit("ERROR: Incorrect orientation!")

	new_v = OverlapVertex(new_id, new_seq)
	new_v.head_edges = v1.head_edges
	new_v.tail_edges = v2.tail_edges

	# correct edges incident to first_v
	for f in v1.head_edges:
		f.replace(v1, new_v)

	for f in v2.tail_edges:
		f.replace(v2, new_v)

	# insert new node:
	g.add_vertex(new_v)

def contract_overlap_edge(g, e):
	v1, v2 = e.v1, e.v2

	assert e in v1.edges
	assert e in v2.edges

	_orient_th(g, e, v1, v2)
	v1, v2 = e.v1, e.v2

	assert e.connection[v1] == 'T' and e.connection[v2] == 'H'

	v1_ovl_start = e.ovl_start[v1]
	v2_ovl_end = e.ovl_end[v2]
	orientation = e.orientation

	# remove vertices and edge
	g.remove_vertex_from_index(v1)
	g.remove_vertex_from_index(v2)
	g.remove_edge(e)

	# build new vertex
	# FIXME: refactor; make this method private
	new_id = g.vertex_id_generator.get_id()

	if orientation == 0:
		assert v1.seq[v1_ovl_start:] == v2.seq[0:v2_ovl_end+1]
		new_seq = v1.seq[0:v1_ovl_start] + v2.seq
	elif orientation == 1:
		assert v1.seq[v1_ovl_start:] == reverse_complement(v2.seq[0:v2_ovl_end+1])
		new_seq = v1.seq[0:v1_ovl_start] + reverse_complement(v2.seq)
	else:
		exit("ERROR: Incorrect orientation!")

	assert len(new_seq) == len(v1.seq[0:v1_ovl_start]) + len(v2.seq)

	new_v = OverlapVertex(new_id, new_seq)
	new_v.head_edges = v1.head_edges
	new_v.tail_edges = v2.tail_edges

	new_v.metadata['contigs'] = v1.metadata['contigs'] + v2.metadata['contigs']
	v2_ctg_starts = v2.metadata['contig_starts'].copy()
	v2_ctg_ends = v2.metadata['contig_ends'].copy()
	if orientation == 1:
		v2_len = len(v2.seq)
		for ctg in v2.metadata['contig_starts']:
			v2_ctg_starts[ctg] = v2_len - v2.metadata['contig_ends'][ctg] - 1
			v2_ctg_ends[ctg] = v2_len - v2.metadata['contig_starts'][ctg] - 1

	new_v.metadata['contig_starts'] = dict(v1.metadata['contig_starts'].items() + v2_ctg_starts.items())
	new_v.metadata['contig_ends'] = dict(v1.metadata['contig_ends'].items() + v2_ctg_ends.items())

	length_increase = len(v1.seq[0:v1_ovl_start])

	# FIXME: fold this into shift function for vertex
	# NOTE: this is wrong for wells b/c they could occur in v1 & v2
	for ctg in v2.metadata['contig_starts']:
		new_v.metadata['contig_starts'][ctg] += length_increase
		new_v.metadata['contig_ends'][ctg] += length_increase

	all_ctgs = new_v.metadata['contig_starts'].copy()
	new_len = len(new_v.seq)
	for ctg in all_ctgs:
		if 4000 < new_v.metadata['contig_starts'][ctg] \
		<= new_v.metadata['contig_ends'][ctg] < new_len - 4000:
			del new_v.metadata['contig_starts'][ctg]
			del new_v.metadata['contig_ends'][ctg]

	# correct edges incident to first_v
	for f in v1.head_edges:
		f.replace(v1, new_v)

	for f in v2.tail_edges:
		f.replace(v2, new_v)
		f.shift(new_v, length_increase)
	
		if f.ovl_start[new_v] != 0:
			assert f.ovl_end[new_v] == len(new_v) - 1

	# assert no_diedge(new_v)

	# insert new node:
	g.add_vertex(new_v)

# ----------------------------------------------------------------------------
# helpers

def _orient_th(g, e, v1, v2):
	"""Changes edge and vertices so that e connects v1, v2 as T->H."""

	if e.connection[e.v1] == e.connection[e.v2]:
		if e.connection[e.v1] == 'H':
			_flip_vertex(e.v1, g)
		elif e.connection[e.v1] == 'T':
			_flip_vertex(e.v2, g)
	elif e.connection[e.v1] == 'H' and e.connection[e.v2] == 'T':
		e.flip()

# FIXME: Make this a method of StringGraph
def _flip_vertex(v, g):
	for e in v.edges:
		e.orientation = (e.orientation + 1) % 2
		e.flip_connection(v)

	v.seq = reverse_complement(v.seq)
	v.head_edges, v.tail_edges = v.tail_edges, v.head_edges

	v_len = len(v.seq)

	if v.metadata:
		v_ctg_starts = v.metadata['contig_starts'].copy()
		v_ctg_ends = v.metadata['contig_ends'].copy()
		for ctg in v.metadata['contig_starts']:
			v.metadata['contig_starts'][ctg] = v_len - v_ctg_ends[ctg] - 1
			v.metadata['contig_ends'][ctg] = v_len - v_ctg_starts[ctg] - 1