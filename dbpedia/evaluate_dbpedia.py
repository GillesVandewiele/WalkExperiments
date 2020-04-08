import argparse

from evaluation_framework.manager import FrameworkManager


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evaluation framework for RDF embedding methods')
    parser.add_argument('--vectors_file', type=str, required=True,
                        help='Path of the file where your vectors are stored. File format: one line for each entity with entity and vector')
    args = parser.parse_args()
    evaluation_manager = FrameworkManager()

    evaluation_manager.evaluate(args.vectors_file,
                                tasks=['EntityRelatedness', 'Classification', 'Regression', 'DocumentSimilarity'],
                                parallel=True, debugging_mode=True, vector_size=300)
