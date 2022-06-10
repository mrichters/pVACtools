import os
from random import sample
import shutil
from turtle import distance
import pandas as pd
import pyfaidx
from filter_regtools_results import *
from junction_to_fasta import *
from fasta_to_kmers import *
from pvactools.lib.run_argument_parser import *
from pvactools.lib.input_file_converter import PvacspliceVcfConverter


class JunctionPipeline():
    def __init__(self, **kwargs):
        self.input_file                       = kwargs['input_file']
        self.annotated_vcf                    = kwargs['annotated_vcf']
        self.sample_name                      = kwargs['sample_name']
        self.output_dir                       = kwargs['base_output_dir']
        self.fasta_path                       = kwargs['ref_fasta']
        self.class_i_epitope_length           = kwargs.pop('class_i_epitope_length', None)
        self.class_ii_epitope_length          = kwargs.pop('class_ii_epitope_length', None)
        self.junction_score                   = kwargs.pop('junction_score', 10)
        self.variant_distance                 = kwargs.pop('variant_distance', 100)
        self.maximum_transcript_support_level = kwargs.pop('maximum_transcript_support_level', 1)
        self.normal_sample_name               = kwargs.pop('normal_sample_name', None)


    def execute(self):
        #self.filter_regtools_results()
        #self.vcf_to_tsv()
        #self.combine_inputs()
        self.junction_to_fasta()
        #self.fasta_to_kmers()

    def create_file_path(self, type):
        inputs = {
            'annotated': '_annotated.tsv',
            'filtered' : '_filtered.tsv',
            'combined' : '_combined.tsv',
            'fasta'    : '_transcripts.fa',
        }
        file_name = self.sample_name + inputs[type]
        return os.path.join(self.output_dir, file_name) 

    def filter_regtools_results(self):
        print('Filtering regtools results')
        filter_params = {
            'input_file'  : self.input_file,
            'output_file' : self.create_file_path('filtered'),
            'output_dir'  : self.output_dir,
            'score'       : self.junction_score,
            'distance'    : self.variant_distance,
            'tsl'         : self.maximum_transcript_support_level,
        }
        filter = FilterRegtoolsResults(**filter_params)
        filter.execute()
        print('Completed')

    def vcf_to_tsv(self):
        print('Converting .vcf to TSV')
        convert_params = {
            'input_file'  : self.annotated_vcf,
            'output_file' : self.create_file_path('annotated'),
            'sample_name' : self.sample_name,
        }
        if self.normal_sample_name is not None:
            convert_params['normal_sample_name'] = self.normal_sample_name
        converter = PvacspliceVcfConverter(**convert_params)
        converter.execute()
        print('Completed')
    
    def combine_inputs(self):
        print('Combining junction and variant information')
        # read in filtered junctions and annotated tsv
        junctions = pd.read_csv(self.create_file_path('filtered'), sep='\t')
        annotated = pd.read_csv(self.create_file_path('annotated'), sep='\t')
        # rename annotated cols
        annotated.rename(columns={
                'transcript_name' : 'transcripts',
                'chromosome_name' : 'variant_chrom', 
                'start'           : 'variant_start', 
                'stop'            : 'variant_stop',
            }, inplace=True
        )
        # remove version number in annotated  to compare with filtered junctions file
        annotated['transcripts'] = annotated['transcripts'].str.split('.', expand=True)[[0]]
        
        # separate snvs and indels because need coors fix for indels
        snv_df = annotated[(annotated['reference'].str.len() == 1) & (annotated['variant'].str.len() == 1)]
      
        # increment variant_start for indels in junctions to match coords from annotated
        junctions.loc[~junctions['transcripts'].isin(snv_df['transcripts'].unique().tolist()), ['variant_start']] += 1

        # remove junctions variant_stop as it is redundant for snvs and unwanted for indels (correct version supplied by annotated)
        # then, merge dfs by variant_info, transcript_id
        self.merged_df = junctions.drop(columns=['variant_stop']).merge(annotated, on=['variant_chrom', 'variant_start', 'transcripts'])

        # usage of annotated's variant_stop col over junctions' leaves it non-adjacent to variant_start
        # [OPTIONAL] below, move variant_stop to be right after variant_start for readability
        stop_index = self.merged_df.columns.tolist().index('variant_start') + 1
        self.merged_df.insert(stop_index, 'variant_stop', self.merged_df.pop('variant_stop'))

        # f'{self.gene_name}.{self.tscript_id}.{self.junction_name}.{self.anchor}'
        # uniquify tsv indexes
        self.merged_df['index'] = self.merged_df['Gene_name'] + '.' + self.merged_df['Transcript_stable_ID'] + '.' + self.merged_df['name'] + '.' + self.merged_df['anchor']

        self.merged_df.to_csv(self.create_file_path('combined'), sep='\t', index=False)
        print('Completed')

    def junction_to_fasta(self):
        print('Assembling tumor-specific splicing junctions')
        filtered_df = pd.read_csv(self.create_file_path('combined'), sep='\t')
        for i in filtered_df.index.unique().to_list():
            junction = filtered_df.loc[[i], :]
            for row in junction.itertuples():
                junction_params = {
                    'fasta_path'     : self.fasta_path,
                    'tscript_id'     : row.Transcript_stable_ID,
                    'chrom'          : row.junction_chrom,
                    'junction_name'  : row.name,
                    'junction_coors' : [row.junction_start, row.junction_stop],
                    'index'          : row.index, 
                    'anchor'         : row.anchor,
                    'strand'         : row.strand,
                    'gene_name'      : row.Gene_name,
                    'output_file'    : self.create_file_path('fasta'),
                    'output_dir'     : self.output_dir,
                    'vcf'            : self.annotated_vcf,
                    'sample_name'    : self.sample_name,
                }

                # write chrs here - include work dir cleanup at the end
                # chrom_fasta = pyfaidx.Fasta(self.fasta_path)[row.junction_chrom][:]
                
                # ref_path = os.path.join(self.output_dir, f'{row.junction_chrom}.fa')
                # alt_path = os.path.join(self.output_dir, f'{row.junction_chrom}_alt.fa')
                
                # for x in [ref_path, alt_path]:
                #     if not os.path.exists(x):
                #         f = open(x, 'w')
                #         f.write(f'>{chrom_fasta.name}\n{chrom_fasta.seq}\n')
                #         f.close()

                # junction_params['ref_fasta'] = pyfaidx.Fasta(ref_path)
                # junction_params['alt_fasta'] = pyfaidx.FastaVariant(alt_path, self.annotated_vcf, sample=self.sample_name)
                # end
                
                junctions = JunctionToFasta(**junction_params)
                wt = junctions.create_wt_df()
                if wt.empty:
                    continue
                mut = junctions.create_alt_df()
                if mut.empty:
                    continue
                wt_aa, mut_aa = junctions.get_sequence_wrapper()
                junctions.create_sequence_fasta(wt_aa, mut_aa)
                # wt_aa, wt_dna = junctions.get_aa_sequence(wt)
                # if not wt_aa or not wt_dna:
                #     print(f'{row.Transcript_stable_ID} Error: reference sequence not found')
                #     continue
                # mut_aa, mut_dna = junctions.get_aa_sequence(mut)
                
                #junctions.create_sequence_fasta(wt_dna, mut_dna)
        print('Completed')
    

    def fasta_to_kmers(self):
        print('Creating a fasta of kmer peptides from altered portion of transcripts')
        kmer_params = {
            'fasta'           : self.create_file_path('fasta'),
            'output_dir'      : self.output_dir,
            'epitope_lengths' : self.class_i_epitope_length + self.class_ii_epitope_length, 
            'combined_df'     : self.create_file_path('combined'),
        }
        fasta = FastaToKmers(**kmer_params)
        fasta.execute()
        print('Completed')

