#!/usr/bin/python
# Sample a set of lines out of a file

import random
import sys

def SampleItems(source_items, sample_size):
    """Cleans and randomly samples the source items."""
    if len(source_items) < sample_size:
        sample_size = len(source_items)
    sampled = random.sample(source_items, sample_size)
    random.shuffle(sampled)
    return sampled


def Usage(error):
    """Alert the user that they made an error in usage of the command."""
    print 'ERROR: %s' % error
    print
    print 'usage: %s samples sourcefile' % sys.argv[0]
    print
    sys.exit(1)


def ProcessArguments():
    if len(sys.argv) < 2:
        Usage('No sample size specified')
    sample_size = int(sys.argv[1])
    if len(sys.argv) < 3:
        source_file = 'sys.stdin'
        source_items = sys.stdin.readlines()
    else:
        source_file = sys.argv[2]
        source_items = open(source_file).readlines()
    target_items = open(sys.argv[3], 'w') if len(sys.argv) > 3 else sys.stdout
    return source_file, source_items, sample_size, target_items


def RunCommand():
    source_file, source_items, sample_size, target_items = ProcessArguments()
    target_items.writelines(SampleItems(source_items, sample_size))


if __name__ == '__main__':
    RunCommand()
