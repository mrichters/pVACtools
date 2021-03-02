import unittest
import unittest.mock
import os
import re
import sys
import tempfile
import py_compile
from subprocess import PIPE
from subprocess import run as subprocess_run
from filecmp import cmp
import yaml
import lib
from lib.pipeline import *
import datetime
from tools.pvacbind import *
from mock import patch
from .test_utils import *

def make_response(data, files, path):
    if not files:
        if 'length' in data:
            filename = 'response_%s_%s_%s.tsv' % (data['allele'], data['length'], data['method'])
        else:
            filename = 'response_%s_%s.tsv' % (data['allele'], data['method'])
        reader = open(os.path.join(
            path,
            filename
        ), mode='r')
        response_obj = lambda :None
        response_obj.status_code = 200
        response_obj.text = reader.read()
        reader.close()
        return response_obj
    else:
        configfile = data['configfile']
        reader = open(os.path.join(
            path,
            'net_chop.html' if 'NetChop-3.1' in configfile else 'Netmhcstab.html'
        ), mode='rb')
        response_obj = lambda :None
        response_obj.status_code = 200
        response_obj.content = reader.read()
        reader.close()
        return response_obj

def generate_class_i_call(method, allele, length, input_file):
    reader = open(input_file, mode='r')
    text = reader.read()
    reader.close()
    return unittest.mock.call('http://tools-cluster-interface.iedb.org/tools_api/mhci/', data={
        'sequence_text': ""+text,
        'method':        method,
        'allele':        allele,
        'length':        length,
        'user_tool':     'pVac-seq',
    })

def generate_class_ii_call(method, allele, path, input_path):
    reader = open(os.path.join(
        input_path,
        "MHC_Class_II",
        "tmp",
        "Test.15.fa.split_1-48"
    ), mode='r')
    text = reader.read()
    reader.close()
    return unittest.mock.call('http://tools-cluster-interface.iedb.org/tools_api/mhcii/', data={
        'sequence_text': ""+text,
        'method':        method,
        'allele':        allele,
        'user_tool':     'pVac-seq',
    })

def pvac_directory():
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def test_data_directory():
    return os.path.join(
        pvac_directory(),
        'tests',
        'test_data',
        'pvacbind'
    )

class PvacbindTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pVac_directory = pvac_directory()
        cls.test_data_directory = test_data_directory()
        cls.methods = {
            'ann': {
                'HLA-E*01:01': [9, 10]
            },
            'pickpocket': {
                'HLA-G*01:09': [9, 10],
                'HLA-E*01:01': [9, 10],
            },
        }

    def test_pvacbind_compiles(self):
        compiled_pvac_path = py_compile.compile(os.path.join(
            self.pVac_directory,
            'tools',
            'pvacbind',
            "main.py"
        ))
        self.assertTrue(compiled_pvac_path)

    def test_pvacbind_commands(self):
        pvac_script_path = os.path.join(
            self.pVac_directory,
            'tools',
            'pvacbind',
            "main.py"
            )
        usage_search = re.compile(r"usage: ")
        for command in [
            "run",
            'binding_filter',
            'valid_alleles',
            'allele_specific_cutoffs',
            'download_example_data',
            'top_score_filter',
            ]:
            result = subprocess_run([
                sys.executable,
                pvac_script_path,
                command,
                '-h'
            ], shell=False, stdout=PIPE)
            self.assertFalse(result.returncode)
            self.assertRegex(result.stdout.decode(), usage_search)

    def test_run_compiles(self):
        compiled_run_path = py_compile.compile(os.path.join(
            self.pVac_directory,
            "tools",
            "pvacbind",
            "run.py"
        ))
        self.assertTrue(compiled_run_path)

    def test_process_stops(self):
        output_dir = tempfile.TemporaryDirectory(dir = self.test_data_directory)
        params = {
            'input_file': os.path.join(self.test_data_directory, "input_with_stops.fasta"),
            'input_file_type': 'fasta',
            'sample_name': 'Test',
            'alleles': ['HLA-G*01:09'],
            'prediction_algorithms': ['NetMHC'],
            'output_dir': output_dir.name,
            'epitope_lengths': [9],
        }
        pipeline = PvacbindPipeline(**params)
        pipeline.create_per_length_fasta_and_process_stops(9)
        output_file   = os.path.join(output_dir.name, 'tmp', 'Test.9.fa')
        expected_file = os.path.join(self.test_data_directory, 'output_with_stops.fasta')
        self.assertTrue(cmp(output_file, expected_file))
        output_dir.cleanup()

    def test_pvacbind_pipeline(self):
        with patch('requests.post', unittest.mock.Mock(side_effect = lambda url, data, files=None: make_response(
            data,
            files,
            test_data_directory()
        ))) as mock_request:
            output_dir = tempfile.TemporaryDirectory(dir = self.test_data_directory)

            run.main([
                os.path.join(self.test_data_directory, "input.fasta"),
                'Test',
                'HLA-G*01:09,HLA-E*01:01',
                'NetMHC',
                'PickPocket',
                output_dir.name,
                '-e', '9,10',
                '--top-score-metric=lowest',
                '--keep-tmp-files',
                '--net-chop-method', 'cterm',
                '--netmhc-stab',
            ])

            run.main([
                os.path.join(self.test_data_directory, "input.fasta"),
                'Test',
                'H2-IAb',
                'NNalign',
                output_dir.name,
                '--top-score-metric=lowest',
                '--keep-tmp-files',
            ])

            for file_name in (
                'Test.all_epitopes.tsv',
                'Test.filtered.tsv',
            ):
                output_file   = os.path.join(output_dir.name, 'MHC_Class_I', file_name)
                expected_file = os.path.join(self.test_data_directory, 'MHC_Class_I', file_name)
                self.assertTrue(compare(output_file, expected_file))

            for file_name in (
                'Test.9.fa.split_1-48',
                'Test.9.fa.split_1-48.key',
                'Test.10.fa.split_1-48',
                'Test.10.fa.split_1-48.key',
            ):
                output_file   = os.path.join(output_dir.name, 'MHC_Class_I', 'tmp', file_name)
                expected_file = os.path.join(self.test_data_directory, 'MHC_Class_I', 'tmp', file_name)
                self.assertTrue(cmp(output_file, expected_file))

            for file_name in (
                'Test.HLA-G*01:09.9.parsed.tsv_1-48',
                'Test.HLA-G*01:09.10.parsed.tsv_1-48',
                'Test.HLA-E*01:01.9.parsed.tsv_1-48',
                'Test.HLA-E*01:01.10.parsed.tsv_1-48',
            ):
                output_file   = os.path.join(output_dir.name, 'MHC_Class_I', 'tmp', file_name)
                expected_file = os.path.join(self.test_data_directory, 'MHC_Class_I', 'tmp', file_name)
                self.assertTrue(compare(output_file, expected_file))

            for file_name in (
                'inputs.yml',
            ):
                output_file   = os.path.join(output_dir.name, 'MHC_Class_I', 'log', file_name)
                self.assertTrue(os.path.exists(output_file))

            #Class I output files
            methods = self.methods
            for method in methods.keys():
                for allele in methods[method].keys():
                    for length in methods[method][allele]:
                        mock_request.assert_has_calls([
                            generate_class_i_call(method, allele, length, os.path.join(output_dir.name, "MHC_Class_I", "tmp", "Test.{}.fa.split_1-48".format(length)))
                        ])
                        output_file   = os.path.join(output_dir.name, "MHC_Class_I", "tmp", 'Test.%s.%s.%s.tsv_1-48' % (method, allele, length))
                        expected_file = os.path.join(self.test_data_directory, "MHC_Class_I", "tmp", 'Test.%s.%s.%s.tsv_1-48' % (method, allele, length))
                        self.assertTrue(cmp(output_file, expected_file, False))

            #Class II output files
            for file_name in (
                'Test.all_epitopes.tsv',
                'Test.filtered.tsv',
            ):
                output_file   = os.path.join(output_dir.name, 'MHC_Class_II', file_name)
                expected_file = os.path.join(self.test_data_directory, 'MHC_Class_II', file_name)
                self.assertTrue(compare(output_file, expected_file))

            for file_name in (
                'Test.15.fa.split_1-48',
                'Test.15.fa.split_1-48.key',
                'Test.nn_align.H2-IAb.15.tsv_1-48',
            ):
                output_file   = os.path.join(output_dir.name, 'MHC_Class_II', 'tmp', file_name)
                expected_file = os.path.join(self.test_data_directory, 'MHC_Class_II', 'tmp', file_name)
                self.assertTrue(cmp(output_file, expected_file, False))

            for file_name in (
                'Test.H2-IAb.15.parsed.tsv_1-48',
            ):
                output_file   = os.path.join(output_dir.name, 'MHC_Class_II', 'tmp', file_name)
                expected_file = os.path.join(self.test_data_directory, 'MHC_Class_II', 'tmp', file_name)
                self.assertTrue(compare(output_file, expected_file))

            for file_name in (
                'inputs.yml',
            ):
                output_file   = os.path.join(output_dir.name, 'MHC_Class_II', 'log', file_name)
                self.assertTrue(os.path.exists(output_file))

            mock_request.assert_has_calls([
                generate_class_ii_call('nn_align', 'H2-IAb', self.test_data_directory, output_dir.name)
            ])

            with self.assertRaises(SystemExit) as cm:
                run.main([
                    os.path.join(self.test_data_directory, "input.fasta"),
                    'Test',
                    'H2-IAb',
                    'NNalign',
                    output_dir.name,
                    '--keep-tmp-files',
                ])
            self.assertEqual(
                str(cm.exception),
                "Restart inputs are different from past inputs: \n" +
                "Past input: top_score_metric - lowest\n" +
                "Current input: top_score_metric - median\nAborting."
            )

            output_dir.cleanup()

    def test_duplicate_fasta_header(self):
        with self.assertRaises(Exception) as cm:
            output_dir = tempfile.TemporaryDirectory(dir = self.test_data_directory)
            run.main([
                os.path.join(self.test_data_directory, "input.duplicate_header.fasta"),
                'Test',
                'HLA-A*02:01',
                'NetMHC',
                output_dir.name,
                '-e', '8'
            ])
        self.assertEqual(
            str(cm.exception),
            "Duplicate fasta header 1. Please ensure that the input FASTA uses unique headers."
        )
        output_dir.cleanup()

    def test_pvacbind_combine_and_condense_steps(self):
        output_dir = tempfile.TemporaryDirectory(dir = self.test_data_directory)
        for subdir in ['MHC_Class_I', 'MHC_Class_II']:
            path = os.path.join(output_dir.name, subdir)
            os.mkdir(path)
            test_data_dir = os.path.join(self.test_data_directory, 'combine_and_condense', subdir)
            for item in os.listdir(test_data_dir):
                os.symlink(os.path.join(test_data_dir, item), os.path.join(path, item))

        run.main([
            os.path.join(self.test_data_directory, "input.fasta"),
            'Test',
            'HLA-G*01:09,HLA-E*01:01,H2-IAb',
            'NetMHC',
            'PickPocket',
            'NNalign',
            output_dir.name,
            '-e', '9,10',
            '--top-score-metric=lowest',
            '--keep-tmp-files',
            '--allele-specific-binding-thresholds',
        ])

        for file_name in (
            'Test.all_epitopes.tsv',
            'Test.filtered.tsv',
        ):
            output_file   = os.path.join(output_dir.name, 'combined', file_name)
            expected_file = os.path.join(self.test_data_directory, 'combine_and_condense', 'combined', file_name)
            self.assertTrue(compare(output_file, expected_file))
