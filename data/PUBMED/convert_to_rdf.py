import pandas as pd
import numpy as np
import rdflib
import tqdm

features = pd.read_csv('feature.txt', sep='\t', header=None, index_col=0)
cites = pd.read_csv('net.txt', sep='\t', header=None)
labels = pd.read_csv('label.txt', sep='\t', header=None, index_col=0)

g = rdflib.Graph()

for i, row in tqdm.tqdm(features.iterrows(), total=len(features)):
	vals = [float(x.split(':')[1]) for x in row.values[0].split()]
	#assert all([x == 1.0 for x in vals])

	if i in labels.index:
		label = str(labels.loc[i][1])
		g.add((rdflib.URIRef('http://paper_'+str(i)), rdflib.URIRef('http://hasLabel'), rdflib.URIRef('http://label_'+label)))

	words = [x.split(':')[0] for x in row.values[0].split()]
	for word in words:
		g.add((rdflib.URIRef('http://paper_'+str(i)), rdflib.URIRef('http://hasWord'), rdflib.URIRef('http://word_'+word)))

for i, row in tqdm.tqdm(cites.iterrows(), total=len(cites)):
	dest, src, _ = map(str, row.values)
	g.add((rdflib.URIRef('http://paper_'+src), rdflib.URIRef('http://cites'), rdflib.URIRef('http://paper_'+dest)))

g.serialize(destination='pubmed.ttl', format='turtle')