#!/usr/bin/env python
import argparse
import sys
import os
import logging
logging.basicConfig(level=logging.DEBUG)

from corputils.core.sentence_matchers import PeripheralLinearBigramMatcher, UnigramMatcher,\
    get_composition_matchers
from corputils.core.feature_extractor import BOWFeatureExtractor, TargetsFeaturesExtractor
from corputils.core.count_pipeline import CountSumPipeline

from clutils.config_loader import load_config


def main():
    parser = argparse.ArgumentParser(description=
    '''Generates a list of coocurrence patterns of the form 
    pivot <direction> context
    given a dependency parsed corpus.
    Pivots = Context Words''')
    parser.add_argument('corpora', help='files with the parsed corpora',
        nargs='+')
    parser.add_argument('-C', '--config', default='config.yml')
    parser.add_argument('-D', '--debug', action='store_true', default=False,
    help="runs in local multithreading mode")
    parser.add_argument('--resume', action='store_true', default=False,
    help="If the output of a module is already present, don't re-run it "
    "(only useful if the job died)")
    parser.add_argument('-o', '--output', default='output', 
    help='output directory')
    parser.add_argument('-z', '--gzip', action='store_true', default=False, 
    help="Interpret corpora as gzipped files")
    parser.add_argument('-w', dest='window_size', type=int, default=None)
    parser.add_argument('-s', dest='separator', default='s', help="sentence "
    "separator (default=s)")
    parser.add_argument('-x', '--token_sep', default='<-->', help="token "
    "separator for composed bigrams (e.g. red-j<-->car-n)")
    parser.add_argument('--only-content', help='Filter out all words with the ' 
                        'first letter of the POS not in "NJVR"', 
                        action='store_true', default=False)
    parser.add_argument('-t0', '--targets0', metavar='FILE', help='filter output '
    'unigram targets for which the lexical item is not in the provided list '
    '(line-separated list of elements formatted as specified by -tf)')
    parser.add_argument('-t1', '--targets1', metavar='FILE', help='filter output '
    'bigram targets for which the 1st lexical item is not in the provided list '
    '(line-separated list of elements formatted as specified by -tf)')
    parser.add_argument('-t2', '--targets2', metavar='FILE', help='filter output '
    'bigram targets for which the 2nd lexical item is not in the provided list '
    '(line-separated list of elements formatted as specified by -tf)')
    parser.add_argument('-c', '--contexts', metavar='FILE', help='filter output '
    'context features by those specified in the file (line-separated list of elements '
    'formatted as specified by -cf)')
    parser.add_argument('-i', '--ignore_case', default=False, action='store_true',
        help='ignore case on match patterns')
    parser.add_argument('--to-lower', default=False, action='store_true',
        help='transform words and lemmas to lowercase')
    parser.add_argument('-tf', '--target-format', default='{lemma}-{cat}', 
                        help="format used for the target. Variables are "
                        "{word}, {lemma}, {pos} and {cat} (default: {lemma}-{cat})")
    parser.add_argument('-cf', '--context-format', default='{lemma}-{cat}', 
                        help="format used for the context. Variables are "
                        "{word}, {lemma}, {pos} and {cat} (default: {lemma}-{cat})")
    parser.add_argument('--no-unigrams', action='store_true', default=False,
                        help="Don't output features for unigram targets")
    parser.add_argument('-l', '--linear-comp', help='''Match phrases based on a pseudo-regular expression.
    Each token is represented with a T<> marker which can 
    take as optional arguments "word" and "pos". 
    E.g. T<word=big,pos=JJ>(T<pos=JJ>)*T<word=file(rows.txt),pos=NN|NNS>''')
    parser.add_argument('-dr', '--deprel', help='Dependency arc marching: specify the '
    'relation tag name')
    parser.add_argument('-dw','--depword', help='Dependency arc matching: left word regexp')
    parser.add_argument('-dl','--deplemma', help='Dependency arc matching: left '
    'lemma regexp')
    parser.add_argument('-dp', '--deppos', help='Dependency arc matching: left pos regexp')
    parser.add_argument('-df', '--depfile', help='Dependency arc matching: file '
    'containing possible dependent tokens (with the format specified by -tf)')
    parser.add_argument('-hl', '--headlemma', help='Dependency arc matching: right '
    'lemma regexp')
    parser.add_argument('-hw', '--headword', help='Dependency arc matching: right word regexp')
    parser.add_argument('-hp', '--headpos', help='Dependency arc matching: right pos regexp')
    parser.add_argument('-hf', '--headfile', help='Dependency arc matching: file '
    'containing possible head tokens (with the format specified by -ff)')

    args = parser.parse_args()
    w = args.window_size
    
    targets = {}
    #Target unigrams filter
    targets[1] = {}
    if args.targets0:
        targets[1][1] = args.targets0

    

    targets[2] = {}
    if args.targets1:
        targets[2][1] = args.targets1
        
    if args.targets2:
        targets[2][2] = args.targets2
        
        
    if args.contexts:
        contexts_words = args.contexts
    else:
        contexts_words = None
    


    
    matchers = []
    #create a matcher for the core space
    if not args.no_unigrams:
        matchers.append(UnigramMatcher())
    #build functions that match a peripheral bigram
    matchers.extend(get_composition_matchers(args) )
    #FIXME: FeatureExtractors don't need to know target format (move filters to
    #TargetsFeaturesExtractor
    #define the kind of features we want to extract
    feature_extractor = BOWFeatureExtractor(args.window_size, contexts_words,
        args.context_format)
    #initialize extractor
    #FIXME: TargetsFeaturesExtractor is not a FeaturesExtractor (find a better name)
    targets_features_extractor = TargetsFeaturesExtractor(matchers,
                                                          feature_extractor,
                                                          args.target_format,
                                                          args.context_format,
                                                          targets)
    try:
        config = load_config(args.config)
    except:
        print "Error while trying to load configuration file {0}".format(args.config)
        raise

    #pipeline = StreamingCountPipeline('compute-0-1', 17160,#random.randint(2000,32767), 
    #    os.path.join(os.getcwd(), args.output), targets_features_extractor, 
    #    args.corpora, args.gzip, args.target_format, args.context_format)
    pipeline = CountSumPipeline( 
        os.path.join(os.getcwd(), args.output), targets_features_extractor, 
        args.corpora, args.gzip, args.target_format, args.context_format,
        args.separator, args.to_lower)
    pipeline.run(debug=args.debug, resume=args.resume, config=config)

        
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Aborted!"
        sys.exit(1)
