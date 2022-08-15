import unittest
import os
import sys
import tempfile
from subprocess import call
from filecmp import cmp
import py_compile

from pvactools.tools.pvacsplice.fasta_to_kmers import FastaToKmers
from .test_utils import *

class CombineInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python        = sys.executable
        cls.executable    = os.path.join(pvactools_directory(), "pvactools", "tools", "pvacsplice", "fasta_to_kmers.py")
        cls.test_data_dir = os.path.join(pvactools_directory(), "tests", "test_data", "pvacsplice", "fasta_to_kmers")

    def module_compiles(self):
        self.assertTrue(py_compile.compile(self.executable))

    def test_combine_inputs_runs_and_produces_expected_output(self):
        input_fasta = os.path.join(self.test_data_dir, 'Test_transcripts.fa')
        output_dir = tempfile.TemporaryDirectory()
        epitope_lengths = [8, 9] ##### class_i and class_ii lengths

        # init
        params = {
            'fasta'           : input_fasta,
            'output_dir'      : output_dir.name,
            'epitope_lengths' : epitope_lengths,#self.class_i_epitope_length + self.class_ii_epitope_length,
        }
        fasta = FastaToKmers(**params)

        # exec
        fasta.execute()

        # check output via direct file comparison
        for file_name in (
            'kmer_index.tsv',
            *['peptides_length_{}.fa'.format(l) for l in epitope_lengths],
        ):
            output_file   = os.path.join(output_dir.name, file_name)
            expected_file = os.path.join(self.test_data_dir, file_name)
            self.assertTrue(compare(output_file, expected_file), "files don't match {} - {}".format(output_file, expected_file))

        #import pdb; pdb.set_trace()
        output_dir.cleanup()
