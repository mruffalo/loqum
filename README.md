LoQuM
=====

LoQuM assigns reliable mapping quality scores to mappings of Illumina reads returned by an alignment tool. It uses the following features to estimate the probability that a read is mapped to the correct location:

* Linear regression on base quality
* Number of matches
* Number of mismatches
* Number of inserted, deleted bases
* Number of mappings
* Mapping quality returned by the alignment tool (if present)

LoQuM has been tested on the following alignment tools:

* Bowtie
* BWA
* mrFAST
* Novoalign
* SOAPv2

Requirements
------------
* Python 3 (3.2 or newer)
* NumPy
* SciPy
* R

Usage
-----

To replace mapping qualities in a SAM file:

    ./loqum.py sam_input saved_model_file sam_output

A suitable "saved model file" for BWA (trained on reads from the ART simulator) is distributed with LoQuM. Models for other aligners will be released shortly, as well as code improvements that will allow for easier creation of new prediction models.
