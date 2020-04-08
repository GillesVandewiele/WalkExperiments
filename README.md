# Evaluating Walking Strategies for Node Embeddings in Knowledge Graphs

This repository contains the code needed to reproduce the experiments from "Evaluating Walking Strategies for Node Embeddings in Knowledge Graphs". 

## Installing dependencies

Our experiments require the following dependencies:
```
numpy==1.13.1
pandas==0.24.1
sklearn==0.22
pyRDF2Vec==0.0.5
rdflib==4.2.2
tqdm==4.19.5
```

## Producing identical embeddings with Weisfeiler-Lehman & Random Walks

Run the following in `identical/`:

```bash
PYTHONHASHSEED=42 python mutag_no_hash.py
```

The `PYTHONHASHSEED` is required to ensure deterministic results.

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
PYTHONHASHSEED=42 python benchmark_experiment.py <dataset name> <num iterations> <walker> <classifier> <walk depth>
```

An example could be:

```bash
PYTHONHASHSEED=42 python benchmark_experiment.py MUTAG 1 rand svc 2
```

Which will perform 1 measurements using random walks of depth 2 and an SVC classifier. A `results/log_{DATASET}.txt` and `results/experiments_{DATASET}.txt` will be created where the logs and final results can be found in respectively.

## Generating results for citation networks

### The data

We already provide the data for the three citation networks (`CORA`, `CITESEER` and `PUBMED`). Moreover, we provide the scripts that were used to convert the structured data to RDF (`convert_to_rdf.py`).

### Generating the results

Very similar to the benchmark KGs, except that you use the `citationnet_experiment.py` script:

```bash
PYTHONHASHSEED=42 python citationnet_experiment.py CORA 1 rand svc 2
``` 

## Generating embeddings for DBpedia

### The data
We use the English version of the 2016-10 DBpedia [dataset](https://wiki.dbpedia.org/downloads-2016-10). We only consider object properties, which are included in the following files: `instance types transitive`, `article categories` and `mappingbased objects`. We only consider subjects and objects from the `http://dbpedia.org/resource` namespace, resulting in: 4,356,314 entities and 52,689,448 triples in total.

### Generating the results
To generate the walks for DBpedia, 2 files are needed: (i) a file with all the DBpedia entities (one entity per line); (ii) a file with all the RDF triples in `nt` format.
To generate the walks for all walking strategies with the same parameters used in the paper, run the following command:

```bash
python generate_dbpedia_walks.py --entities "path to the file with DBpedia entities" --graph "path to the input triples file"
```
For each walking strategy the script will generate a file with the resulting walks, i.e., `walks_{STRATEGY}.txt`

To generate the word2vec embeddings with the parameters used in the paper, run the following command for each walking strategy:

```bash
python w2v.py --i "path to the walks file" --o "output file"
```

To evaluate the embeddings we use the [Configurable Evaluation Framework for Node Embedding Tecniques](https://github.com/mariaangelapellegrino/Evaluation-Framework). After downloading and compiling the evaluation framework, the evaluation can be executed with the following command for each embedding model:

```bash
python evaluate_dbpedia.py --vectors_file "path to the vectors file"
```

The script will generate a folder `results/` and will generate the results for each of the datasets used in each of the 4 downstream tasks: classification, regression, document similarity and entity relatedness. 