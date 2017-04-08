import argparse
import sys

sys.path.append('../')

import argcomplete

import anime9

'''

This is a basic handler that uses
args parse to take in a flagged directory
and positional argument link and starts downloading
to that directory.

'''

parser = argparse.ArgumentParser()

argcomplete.autocomplete(parser)

parser.add_argument('-d', '--directory', type=str, help="Location where the show should be downloaded")
parser.add_argument('link', type=str, help="Link to show")

args = parser.parse_args()

anime9.download(args.link, location=args.directory)
