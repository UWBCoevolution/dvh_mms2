#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 15:39:55 2017

@author: ymseah
"""

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import re

class ComparePolymorphisms:
    
    def parse_compare_html(self, filepath):
        '''
        Input: filepath to breseq COMPARE html output
        Output: BS4 object generated by BeautifulSoup and Python HTML parser.
        '''
        bs_object = BeautifulSoup(open(filepath), 'html.parser')
        return bs_object

    def get_html_generation_frequencies(self, data_html_object):
        '''
        Input: compare html object parsed by BeautifulSoup
        Output: dictionary of mutation frequencies across generations
        Key: (reference genome ID, position of mutation, mutation)
        Value: [ancestor frequency, generation 100 f, gen 300 f, gen 500 f, gen 780 f, gen 1000 f]
        '''
        table_cells = data_html_object.body.find_all('td')
        generation_frequencies_dict = {}
        for cell in table_cells:
            if re.match('NC_', str(cell.string)):
                position = cell.next_sibling.next_sibling.next_sibling
                clean_position = int(re.sub(',', '', position.string))
                mutation = position.next_sibling.next_sibling.next_sibling
                gen_freqs_key = (cell.string, clean_position, mutation.string)
                freq_ancestor = mutation.next_sibling.next_sibling.next_sibling
                freq_gen100 = freq_ancestor.next_sibling
                freq_gen300 = freq_gen100.next_sibling
                freq_gen500 = freq_gen300.next_sibling
                freq_gen780 = freq_gen500.next_sibling
                freq_gen1000 = freq_gen780.next_sibling
                gen_freqs_value = [freq_ancestor.string, freq_gen100.string, freq_gen300.string, freq_gen500.string, freq_gen780.string, freq_gen1000.string]
                generation_frequencies_dict[gen_freqs_key] = gen_freqs_value
        return generation_frequencies_dict

    def get_suspect_html_frequencies(self, generation_frequencies_dict):
        '''
        Input: dictionary of mutation frequencies from get_generation_frequencies()
        Output: dictionary subset of input, only containing values with frequency patterns '100% - 0% - 100%'.
        Key: (reference genome ID, position of mutation, mutation)
        Value: [ancestor frequency, generation 100 f, gen 300 f, gen 500 f, gen 780 f, gen 1000 f]
        '''
        suspect_frequencies_dict = {}
        for key, value in generation_frequencies_dict.items():
            counter = 1
            while counter <= len(value):
                if counter + 1 < len(value):
                    if value[counter] == None:
                        if value[counter - 1] == '100%' or value[counter + 1] == '100%':
                            suspect_frequencies_dict[key] = value
                    elif value[counter] == '100%':
                        if value[counter - 1] == None or value[counter + 1] == None:
                            suspect_frequencies_dict[key] = value
                elif counter + 1 == len(value):
                    if value[counter] == None and value[counter - 1] == '100%':
                        suspect_frequencies_dict[key] = value
                    elif value[counter] == '100%' and value[counter - 1] == None:
                        suspect_frequencies_dict[key] = value                        
                counter += 2
        return suspect_frequencies_dict

    def annotated_gd_to_df(self, filepath, generation):
        '''
        Input1: path to annotated GenomeDiff file
        Input2: generation sampled
        Output: annotated.gd as a data frame
        '''
        df_from_gd = pd.read_table(filepath, comment='#', names=range(50), dtype=str)
        df_from_gd.insert(0, 'generation', generation)
        return df_from_gd

    def summary_df(self, line_name, all_df_from_gd, output_path):
        '''
        Input1: name of evolution line
        Input2: path to output folder
        Input3: list of data frames for all generations of indicated evolution line
        Output: data frame of subset information from multiple annotated.gd files.
        '''
        summary = pd.concat(all_df_from_gd, ignore_index=True)
        summary.insert(0, 'line', line_name)
        summary.insert(2, 'frequency', 0.0)
        summary.insert(3, 'polymorphism_frequency', 0.0)
        summary.insert(4, 'new_cov', '')
        summary.insert(5, 'total_cov', '')
        summary.insert(6, 'gene_product', '')
        summary.insert(7, 'gene_position', '')
        summary.insert(8, 'reject', '')
        summary.insert(9, 'jc_side2_ref_genome', '')
        summary.insert(10, 'jc_side2_position', '')
        print('Creating summary data frame for ' + line_name)
        for row in summary.itertuples():
            if summary.loc[row[0], 0] == 'JC':
                summary.loc[row[0], 'jc_side2_ref_genome'] = summary.loc[row[0], 6]
                summary.loc[row[0], 'jc_side2_position'] = summary.loc[row[0], 7]
            #check each column
            col_index = 6
            while col_index < 50:
                #1. polymorphism frequencies
                if re.match('frequency=', str(summary.loc[row[0], col_index])):
                    summary.loc[row[0], 'frequency'] = re.sub('frequency=', '', str(summary.loc[row[0], col_index]))
                elif re.match('polymorphism_frequency=', str(summary.loc[row[0], col_index])):
                    summary.loc[row[0], 'polymorphism_frequency'] = re.sub('polymorphism_frequency=', '', str(summary.loc[row[0], col_index]))
                #2. gene products
                elif re.match('gene_product=', str(summary.loc[row[0], col_index])):
                    summary.loc[row[0], 'gene_product'] = re.sub('gene_product=', '', str(summary.loc[row[0], col_index]))
                #3. polymorphism rejection reasons
                elif re.match('reject=', str(summary.loc[row[0], col_index])):
                    summary.loc[row[0], 'reject'] = re.sub('reject=', '', str(summary.loc[row[0], col_index]))
                #4. gene annotations
                elif re.match('gene_position=', str(summary.loc[row[0], col_index])):
                    summary.loc[row[0], 'gene_position'] = re.sub('gene_position=', '', str(summary.loc[row[0], col_index]))
                #5. new coverage
                elif re.match('new_cov=', str(summary.loc[row[0], col_index])):
                    summary.loc[row[0], 'new_cov'] = re.sub('new_cov=', '', str(summary.loc[row[0], col_index]))
                #6. total coverage
                elif re.match('total_cov=', str(summary.loc[row[0], col_index])):
                    summary.loc[row[0], 'total_cov'] = re.sub('total_cov=', '', str(summary.loc[row[0], col_index]))
                col_index += 1
            #set frequencies type to float
            if re.match('1|2|3|4|5|6|7|8|9', str(summary.loc[row[0], 'frequency'])):
                summary.loc[row[0], 'frequency'] = float(summary.loc[row[0], 'frequency'])
            else:
                summary.loc[row[0], 'frequency'] = 0.0
            #set polymorphism_frequencies type to float
            if re.match('1|2|3|4|5|6|7|8|9', str(summary.loc[row[0], 'polymorphism_frequency'])):
                summary.loc[row[0], 'polymorphism_frequency'] = float(summary.loc[row[0], 'polymorphism_frequency'])
            else:
                summary.loc[row[0], 'polymorphism_frequency'] = 0.0
            #set positions (col 4) type to int
            summary.loc[row[0], 4] = int(summary.loc[row[0], 4])
            #set reject col to 'NA' when no reject reason given because row represents evidence, not polymorphism.
            if (summary.loc[row[0], 'reject'] == '') & (summary.loc[row[0], 2] == '.'):
                summary.loc[row[0], 'reject'] = 'NA'
            print(line_name + str(row[0]) + ' done.')
        summary.rename(columns = {0: 'entry_type', 1: 'item_id', 2: 'evidence_ids', 3: 'ref_genome', 4:'position'}, inplace=True)
        summary_subset = summary[['line', 'generation', 'frequency', 'polymorphism_frequency', 'new_cov', 'total_cov', 'gene_product', 'gene_position', 
                                  'reject', 'entry_type', 'item_id', 'evidence_ids', 'ref_genome', 'position', 'jc_side2_ref_genome', 'jc_side2_position']].copy()
        summary_subset.to_csv(output_path + line_name + 'summary_df_subset.tsv', index=False, sep='\t')
        return summary_subset

    def write_html_frequency_dicts_to_file(self, dictionary, filename_prefix):
        '''
        Input1: dictionary of frequencies i.e., output from get_suspect_frequencies() or get_html_generation_frequencies().
        Input2: string prefix for output file name, to identify evolution line etc.
        Output: tab-separated text file of Input1 content.
        '''
        print('Writing to ' + filename_prefix + '_frequencies.tsv ...')
        with open(filename_prefix + '_frequencies.tsv', 'w') as output_file:
            output_file.write('ref_genome\tposition\tmutation\thtml_freq_anc\thtml_freq_100\thtml_freq_300\thtml_freq_500\thtml_freq_780\thtml_freq_1000\n')
            for key, value in dictionary.items():
                output_file.write(str(key[0]) + '\t' + str(key[1]) + '\t' + str(key[2]) + '\t' + str(value[0]) + '\t' + str(value[1]) + '\t' + str(value[2]) + '\t' 
                                  + str(value[3]) + '\t' + str(value[4]) + '\t' + str(value[5]) + '\n')
        print('Done')
        return
            
    def get_polymorphism_evidence(self, summary_df_subset, frequencies_dict):
        '''
        Input 1: data frame, summary of annotated.gd
        Input 2: dictionary of frequencies from COMPARE html file
        Output: dictionary of evidence for polymorphisms
        '''
        summary_df_subset_evidence = summary_df_subset[(summary_df_subset['entry_type'] == 'RA') |
                (summary_df_subset['entry_type'] == 'MC') | 
                (summary_df_subset['entry_type'] == 'JC') | 
                (summary_df_subset['entry_type'] == 'UN')]
        evidence_dict = {}
        for key, value in frequencies_dict.items():
            print(key, value)
            row_indices = summary_df_subset_evidence[((key[0] == summary_df_subset_evidence['ref_genome']) | (key[0] == summary_df_subset_evidence['jc_side2_ref_genome'])) & 
                                                     ((key[1] == summary_df_subset_evidence['position']) | (key[1] == summary_df_subset_evidence['jc_side2_position']))].index.tolist()
            for row in row_indices:
                evolution_line = summary_df_subset_evidence.loc[row, 'line']
                generation = summary_df_subset_evidence.loc[row, 'generation']
                gd_frequency = summary_df_subset_evidence.loc[row, 'frequency']
                gd_polymorphism_frequency = summary_df_subset_evidence.loc[row, 'polymorphism_frequency']
                new_cov = summary_df_subset_evidence.loc[row, 'new_cov']
                total_cov = summary_df_subset_evidence.loc[row, 'total_cov']
                reject_reason = summary_df_subset_evidence.loc[row, 'reject']
                evidence_type = summary_df_subset_evidence.loc[row, 'entry_type']
                item_id = summary_df_subset_evidence.loc[row, 'item_id']
                new_key = list(key)
                new_key.append(item_id)
                new_key = tuple(new_key)
                evidence_dict[new_key] = [evolution_line, generation, gd_frequency, gd_polymorphism_frequency, new_cov, total_cov, reject_reason, evidence_type]
        return evidence_dict
    
    def write_evidence_dicts_to_file(self, dictionary, filename_prefix):
        '''
        Input1: dictionary of evidence, i.e. output from get_polymorphism_evidence().
        Input2: string prefix for output file name, to identify evolution line etc.
        Output: tab-separated text file of Input1 content.
        '''
        print('Writing to ' + filename_prefix + '_evidence.tsv ...')
        with open(filename_prefix + '_evidence.tsv', 'w') as output_file:
            output_file.write('ref_genome\tposition\tmutation\tline\tgeneration\tfrequency\tpolymorphism_frequency\tnew_cov\ttotal_cov\treject_reason\tevidence_type\titem_id\n')
            for key, value in dictionary.items():
                output_file.write(str(key[0]) + '\t' + str(key[1]) + '\t' + str(key[2]) + '\t' + str(value[0]) + '\t' + str(value[1]) + '\t' + 
                                  str(value[2]) + '\t' + str(value[3]) + '\t' + str(value[4]) + '\t' + str(value[5]) + '\t' + str(value[6]) + '\t' + str(value[7]) + '\t' + str(key[3]) + '\n')
        print('Done')
        return