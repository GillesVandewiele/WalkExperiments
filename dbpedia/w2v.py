"""
Created on 3/16/20
@author: petar.ristoski@ibm.com
"""

import argparse
import os
from gensim.models import Word2Vec
from timeit import default_timer as timer
import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', filename='word2vec.out', level=logging.INFO)

def readSentences(input_file):
    sentences = []
    with open(input_file) as f:
        for line in f:
            sentences.append(line.rstrip().split(" "))
    return sentences


def trainW2V(input_sentences, output_loc):
    model = Word2Vec(size=300, workers=75, window=5, sg=1, negative=15, iter=5)
    model.build_vocab(input_sentences)
    model.train(input_sentences, total_examples=model.corpus_count, epochs=model.iter)
    model.save(output_loc)

def main(args):
    print("READING INPUT FILE...")
    start = timer()
    sentences =readSentences(args.i)
    end = timer()

    print("READ ",str(len(sentences))," WALKS IN",str(start-end))

    print("TRAINING W2V...")
    start = timer()
    trainW2V(sentences,args.o)
    end = timer()

    print("Model trainied in", str(start - end))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Embeddings')

    # Input and Output
    parser.add_argument('--i', required=True, help='Input file with all walks')
    parser.add_argument('--o', required=True, help='Output file to save embeddings')

    args = parser.parse_args()
    main(args)