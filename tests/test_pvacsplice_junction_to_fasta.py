import unittest
import os
import sys
import tempfile
from subprocess import call
from filecmp import cmp
import py_compile

from pvactools.tools.pvacsplice.junction_to_fasta import JunctionToFasta
from .test_utils import *

class CombineInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python        = sys.executable
        cls.executable    = os.path.join(pvactools_directory(), "pvactools", "tools", "pvacsplice", "junction_to_fasta.py")
        cls.test_data_dir = os.path.join(pvactools_directory(), "tests", "test_data", "pvacsplice", "junction_to_fasta")

    def module_compiles(self):
        self.assertTrue(py_compile.compile(self.executable))

    def test_junction_to_fasta_runs_and_produces_expected_output(self):
        sample_name = 'sample'

        input_file = os.path.join(self.test_data_dir, 'Test_junctions.tsv')
        ref_fasta = os.path.join(self.test_data_dir, 'Test_ref.fa')
        alt_fasta = os.path.join(self.test_data_dir, 'Test_alt.fa')
        annotated_vcf = os.path.join(self.test_data_dir, 'Test_variants.vcf.gz')

        output_dir = tempfile.TemporaryDirectory()
        output_file = os.path.join(output_dir.name, '{}_transcripts.fa'.format(sample_name))

        # init
        params = {
            'input_file'    : input_file,# combined junctions file
            'ref_fasta'     : ref_fasta,
            'alt_fasta'     : alt_fasta,
            'output_file'   : output_file,
            #'output_dir'    : output_dir,
            'annotated_vcf' : annotated_vcf,# needed when pass ref/alt_fasta as files
            'sample_name'   : sample_name,# needed when pass ref/alt_fasta as files
        }
        junctions = JunctionToFasta(**params)

        # exec
        junctions.execute()

        # check result
        expected_file = os.path.join(self.test_data_dir, 'Test_transcripts.fa')
        self.assertTrue(compare(output_file, expected_file), "files don't match {} - {}".format(output_file, expected_file))

        output_dir.cleanup()
