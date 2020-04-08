import random
import os
import numpy as np
import argparse

os.environ['PYTHONHASHSEED'] = '42'
random.seed(42)
np.random.seed(42)

import rdflib

from graph import rdflib_to_kg
from walkers import (RandomWalker, WeisfeilerLehmanWalker,
                     AnonymousWalker, WalkletWalker, NGramWalker, HalkWalker)

import warnings
from timeit import default_timer as timer

warnings.filterwarnings('ignore')

WALK_DEPTH = 4
MAX_WALKS = 500


def main(args):
    print("READING ENTITIES")
    with open(args.entities) as f:
        tmp_entities = [line.rstrip() for line in f]

    all_entities = [rdflib.URIRef(x) for x in tmp_entities]
    print("TOTAL ENTITIES: ", len(all_entities))

    # Load the data with rdflib
    print('Loading data... ')
    start = timer()
    g = rdflib.Graph()
    g.parse(args.graph, format='nt')
    # g.parse('mutag.owl')
    end = timer()
    print("Time to load graph:", str(end - start))

    # Convert the rdflib to our KnowledgeGraph object
    print("CONVERTING TO INTERNAL GRAPH....")
    start = timer()
    kg = rdflib_to_kg(g)
    end = timer()
    print("Time to convert graph:", str(end - start))

    # Define our walking strategies
    random_walker = RandomWalker(WALK_DEPTH, MAX_WALKS)
    ano_walker = AnonymousWalker(WALK_DEPTH, MAX_WALKS)
    walklet_walker = WalkletWalker(WALK_DEPTH, MAX_WALKS)
    ngram_walker = NGramWalker(WALK_DEPTH, MAX_WALKS, n=3, wildcards=[1])
    wl_walker = WeisfeilerLehmanWalker(WALK_DEPTH, MAX_WALKS, wl_iterations=4)
    halk_walker = HalkWalker(WALK_DEPTH, MAX_WALKS, freq_thresholds=[0.001])

    walkers = [
        ('random', random_walker),
        ('anon', ano_walker),
        ('walklet', walklet_walker),
        ('ngram', ngram_walker),
        ('wl', wl_walker),
        ('halk', halk_walker),
    ]

    # Generate the corpus for each strategy
    for name, walker in walkers:
        print("RUNINNG WALKER: ", name)
        start = timer()
        file_name = 'walks_{}.txt'.format(name)
        walker.print_walks(kg, all_entities, file_name)
        end = timer()
        print("WALKER", name, "TOOK", str(end - start))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Embeddings')

    # Input and Output
    parser.add_argument('--entities', required=True, help='File with DBpedia entities')
    parser.add_argument('--graph', required=True, help='File with triples')

    args = parser.parse_args()
    main(args)
