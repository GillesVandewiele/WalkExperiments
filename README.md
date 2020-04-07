# Evaluating Walking Strategies for Node Embeddings in Knowledge Graphs

This repository contains the code needed to reproduce the experiments from "Evaluating Walking Strategies for Node Embeddings in Knowledge Graphs". 

## Installing pyRDF2Vec

Our experiments require pyRDF2Vec. To install this, you can either use pip install or clone the repository:

```bash
# Pip alternative
python -m pip install pyRDF2Vec
# Clone repository
git clone https://github.com/IBCNServices/pyRDF2Vec.git
cd pyRDF2Vec
python setup.py install
```

## Generating results for benchmark KGs

### Download the data

The data can be downloaded [here](http://data.dws.informatik.uni-mannheim.de/rmlod/LOD_ML_Datasets/). Moreover, there is a [paper](https://madoc.bib.uni-mannheim.de/41308/1/Ristoski_Datasets.pdf) and [website](https://www.uni-mannheim.de/dws/research/resources/sw4ml-benchmark/) describing the datasets. Make sure you create a `data/` directory, with a subdirectory for each dataset. Each subdirectory should contain:

* A file with rdf data (can be of different formats)
* A TSV file with the training entities and labels (`{DATASET}_train.tsv`)
* A TSV file with the testing entities and labels (`{DATASET}_test.tsv`)

As the `AIFB` and `MUTAG` datasets are rather small, we have already download these.

### Generating the results

After downloading the data, create a `results/` directory, where the logs will be stored. To generate results for a certain dataset, a certain walking strategy and a certain depth, run the following command:
```bash
python benchmark_experiment.py <dataset name> <num iterations> <walker> <classifier> <walk depth>
```

An example could be:

```bash
python benchmark_experiment.py MUTAG 1 rand svc 2
```

Which will perform 1 measurements using random walks of depth 2 and an SVC classifier. A `results/log_{DATASET}.txt` and `results/experiments_{DATASET}.txt` will be created where the logs and final results can be found in respectively.

## Generating results for citation networks

### The data

We already provide the data for the three citation networks (`CORA`, `CITESEER` and `PUBMED`). Moreover, we provide the scripts that were used to convert the structured data to RDF (`convert_to_rdf.py`).

### Generating the results

Very similar to the benchmark KGs, except that you use the `citationnet_experiment.py` script:

```bash
python citationnet_experiment.py CORA 1 rand svc 2
``` 

## Generating embeddings for DBpedia

