import pickle
import sys
import os

from sklearn.base import BaseEstimator
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.manifold import TSNE
from sklearn.pipeline import Pipeline

import rdflib
import pandas as pd
import numpy as np

import random

from rdf2vec.converters import rdflib_to_kg
from rdf2vec import RDF2VecTransformer

from rdf2vec.walkers import (Walker, RandomWalker, WeisfeilerLehmanWalker,
                     AnonymousWalker, WalkletWalker, NGramWalker,
                     CommunityWalker, HalkWalker, WildcardWalker)

import warnings
warnings.filterwarnings('ignore')

files = {"AIFB": "aifb.n3",
         "AM": "rdf_am-data.ttl",
         "BGS": "BGS.nt",
         "MUTAG": "mutag.xml"}

labels = {"AIFB" : (["http://swrc.ontoware.org/ontology#affiliation",
                     "http://swrc.ontoware.org/ontology#employs",
                     "http://swrc.ontoware.org/ontology#carriedOutBy"], "person", "label_affiliation"),
          "AM" : (["http://purl.org/collections/nl/am/objectCategory",
                   "http://purl.org/collections/nl/am/material"], "proxy", "label_cateogory"),
          "BGS": (["http://data.bgs.ac.uk/ref/Lexicon/hasLithogenesis",
                   "http://data.bgs.ac.uk/ref/Lexicon/hasLithogenesisDescription",
                   "http://data.bgs.ac.uk/ref/Lexicon/hasTheme"], "rock", "label_lithogenesis"),
          "MUTAG": (["http://dl-learner.org/carcinogenesis#isMutagenic"], "bond", "label_mutagenic")}

if len(sys.argv) < 6: raise IOError("Five arguments expected: "
                                    "<dataset name> <num iterations> <walker> <classifier> <walk depth>")
dataset = sys.argv[1]
num_iter = sys.argv[2]
walker_type = sys.argv[3]
classif_type = sys.argv[4]
walk_depth = int(sys.argv[5])

# Load our train & test instances and labels
test_data = pd.read_csv(os.path.join('..', 'data', dataset, dataset + '_test.tsv'), sep='\t')
train_data = pd.read_csv(os.path.join('..', 'data', dataset, dataset + '_train.tsv'), sep='\t')

train_entities = [rdflib.URIRef(x) for x in train_data[labels[dataset][1]]]
train_labels = train_data[labels[dataset][2]]

test_entities = [rdflib.URIRef(x) for x in test_data[labels[dataset][1]]]
test_labels = test_data[labels[dataset][2]]

all_labels = list(train_labels) + list(test_labels)

# Define the label predicates, all triples with these predicates
# will be excluded from the graph
label_predicates = []
for pred in labels[dataset][0]:
    label_predicates.append(rdflib.term.URIRef(pred))

# Convert the rdflib to our KnowledgeGraph object
kg = rdflib_to_kg(os.path.join('..', 'data', dataset, files[dataset]),
                  filetype=files[dataset].split('.')[-1], label_predicates=label_predicates)


##############ESTIMATOR###############

class RDF2VecEstimator(BaseEstimator):
    def __init__(self, walker):
        """Initialise the estimator components."""
        self.walker = walker
        self.rdf2vec = RDF2VecTransformer(walkers=[self.walker])

    def set_params(self, **params):
        """Update parameter during cross-validation."""
        self.walker = DynamicUpdater.update(self.walker, params)
        self.rdf2vec = DynamicUpdater.update(RDF2VecTransformer(walkers=[self.walker]), params)

    def fit(self, X, y=None):
        """Fit estimator to training data."""
        # IMPORTANT: fit is performed on ALL training data, not X,
        # which is only the training data for a given split;
        # if fit is performed on X alone, the vocab will not contain
        # the entities in the valid set for the respective split
        self.rdf2vec.fit(kg, train_entities)

    def transform(self, X):
        """Return the learned embeddings."""
        return self.rdf2vec.transform(kg, X)

    def fit_transform(self, X, y=None):
        """Combine fit and transform."""
        self.fit(X, y)
        return self.transform(X)


##############EXPERIMENTS##############

logfile = open(os.path.join("results", "log_" + dataset + ".txt"), "a")
resfile = open(os.path.join("results", "experiments_" + dataset + ".txt"), "a")
if os.path.getsize(os.path.join("results", "experiments_" + dataset + ".txt")) == 0:
    resfile.write("num_iter,walker_type,classif_type,walk_depth,avg_num_walks,avg_acc,stddev_acc\n")

def print_results(myDict, colList=None):
   """ Pretty print a list of dictionaries (myDict) as a dynamically sized table.
   If column names (colList) aren't specified, they will show in random order.
   Author: Thierry Husson
   Edited by: Michael Weyns
   """
   if not colList: colList = list(myDict.keys() if myDict else [])
   myList = [colList] # 1st row = header
   for i in range(len(myDict[colList[0]])):
       myList.append([str(myDict[col][i] if myDict[col][i] is not None else '') for col in colList])
   colSize = [max(map(len,col)) for col in zip(*myList)]
   formatStr = ' | '.join(["{{:<{}}}".format(i) for i in colSize])
   myList.insert(1, ['-' * i for i in colSize]) # Separating line
   for item in myList: logfile.write(formatStr.format(*item) + "\n")
   logfile.write("\n")

# IMPORTANT:
# each parameter prefix has format <estimator name>__<name inside estimator>__<original param name>
# e.g. for walk rand, the window param for rdf2vec has name: rand__rdf2vec__window
# e.g. for walk comm, the max_iter param for rdf2vec has name: comm__rdf2vec__max_iter
params = {
    'rf':   {'rf__n_estimators': [10, 100, 250]},
    'svc':  {'svc__kernel': ['rbf'],
             'svc__C': [10**i for i in range(-3, 4)]},
    'comm':  {'comm__walker__hop_prob': [0.05, 0.1, 0.25], 'comm__walker__resolution': [0.1, 1, 10]},
    'ngram': {'ngram__walker__n': [1, 2, 3], 'ngram__walker__wildcards': [None, [1]]},
    #'rdf2vec': {walker_type + '__rdf2vec__window': [3, 5]}
}

class DynamicUpdater:
    """Class that updates an object with a parameter dictionary"""

    @staticmethod
    def update(updateable, iterable=(), **kwargs):
        """Update an object based on a parameter dictionary."""
        new_dictionary = {}
        for key in iterable:
            # remove key prefixes
            new_key = key.split("__")[-1]
            # only update key if already in dict
            if new_key in updateable.__dict__:
                new_dictionary[new_key] = iterable[key]
        updateable.__dict__.update(new_dictionary, **kwargs)
        return updateable

class Experiment:
    """Class used to run experiments."""

    @staticmethod
    def __create_walker(walker):
        """Create a walker object based on its name."""
        walkers = {
            # Parameter-free
            'rand': RandomWalker(walk_depth, float('inf')),
            'walklet': WalkletWalker(walk_depth, float('inf')),
            'anon': AnonymousWalker(walk_depth, float('inf')),

            # Hard-coded well-working parameters
            'halk': HalkWalker(walk_depth, float('inf'), freq_thresholds=[0.0, 0.1, 0.05, 0.01, 0.005, 0.001, 0.0005, 0.0001]),
            'wildcard': WildcardWalker(walk_depth, float('inf'), wildcards=[1, 2]),
            'wl': WeisfeilerLehmanWalker(walk_depth, float('inf'), wl_iterations=4),

            # Walkers to tune
            'ngram': NGramWalker(walk_depth, float('inf')),
            'comm': CommunityWalker(walk_depth, float('inf')),
        }
        if walker not in walkers:
          raise Exception('You provided "{}" which is not in {}'.format(walker, list(walkers.keys())))
        if walker in walkers: return walkers[walker]
        return None

    @staticmethod
    def __create_classifier(classif, init=42):
        """Create a classifier object with initialisation based on its name."""
        classifs = {
            'rf': RandomForestClassifier(random_state=init),
            'svc': SVC(random_state=init)
        }
        if classif not in classifs:
          raise Exception('You provided "{}" which is not in {}'.format(classif, list(classifs.keys())))
        if classif in classifs: return classifs[classif]
        return None

    @staticmethod
    def __create_estimator(walker, classif, init=42):
        """Create a full estimator for evaluation."""
        print("creating estimator for", walker, classif)
        p1 = Experiment.__create_walker(walker)
        p2 = Experiment.__create_classifier(classif, init)
        if p1 is not None and p2 is not None:
            return Pipeline([(walker, RDF2VecEstimator(p1)), (classif, p2)])

    @staticmethod
    def run_experiment():
        """Run an experiment for the given cmd line settings."""

        logfile.write("RUNNING EXPERIMENT FOR " + dataset + ", " + walker_type
                      + ", " + classif_type + ", " + str(walk_depth) + "\n\n")

        scores = []
        num_walks = []
        for i in range(int(num_iter)):
            init = random.randint(0, 420000)
            logfile.write("ITERATION " + str(i) + "...\n\n")
            est = Experiment.__create_estimator(walker_type, classif_type, init)
            param_grid = {}
            if walker_type in params:
                param_grid.update(**params[walker_type])
            if classif_type in params:
                param_grid.update(**params[classif_type])
            if 'rdf2vec' in params:
                param_grid.update(**params['rdf2vec'])
            clf = GridSearchCV(est, param_grid, cv=3)
            clf.fit(train_entities, train_labels)

            best_params = clf.best_params_
            logfile.write("best results found for " + str(best_params) + "\n\n")
            results = clf.cv_results_
            print_results(results)

            walker_params = {}
            classif_params = {}
            rdf2vec_params = {}
            for key in best_params:
                if walker_type in params and key in params[walker_type]:
                    walker_params[key] = best_params[key]
                if classif_type in params and key in params[classif_type]:
                    classif_params[key] = best_params[key]
                if 'rdf2vec' in params and key in params['rdf2vec']:
                    rdf2vec_params[key] = best_params[key]

            walker = DynamicUpdater.update(Experiment.__create_walker(walker_type), walker_params)
            transformer = DynamicUpdater.update(RDF2VecTransformer(walkers=[walker]), rdf2vec_params)
            embeddings = transformer.fit_transform(kg, train_entities + test_entities)
            train_embeddings = embeddings[:len(train_entities)]
            test_embeddings = embeddings[len(train_entities):]

            classif = DynamicUpdater.update(Experiment.__create_classifier(classif_type, init), classif_params)
            classif.fit(train_embeddings, train_labels)
            scores.append(accuracy_score(test_labels, classif.predict(test_embeddings)))
            num_walks.append(len(transformer.walks_))
            logfile.write(
                "confusion matrix:\n" + str(confusion_matrix(test_labels, classif.predict(test_embeddings))) + "\n\n")
            logfile.write("test accuracy: " + str(scores[-1]) + "\n\n")

        logfile.write("AVG test scores: " + str(np.average(scores)) + ", " + str(np.std(scores)) + "\n\n")
        logfile.write("-----------------------------------------------------------------------------\n\n")
        resfile.write(num_iter + "," + walker_type + "," + classif_type + "," + str(walk_depth)
                      + "," + str(np.average(num_walks)) + "," + str(np.average(scores)) + "," + str(np.std(scores)) + "\n")

        logfile.close()
        resfile.close()

Experiment.run_experiment()