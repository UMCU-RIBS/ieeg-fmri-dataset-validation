
import re
import warnings
import os

from collections import OrderedDict


class FSL_template(OrderedDict):
    def __init__(self, analysis):
        self.analysis = analysis
        self.template = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    'fsl', 'template_' + self.analysis +'.fsf')
        if self.template:
            self.read(self.template)

    def read(self, template):
        self.template = template
        with open(self.template, 'rb') as infile:
            data = infile.read()
        self.parse(data)

    def parse(self, data):
        coding = 'utf-8'
        buff = [s.strip() for s in data.decode(coding).split('\n')]
        self.data = buff

    def set_EV_values(self):
        assert self.analysis == 'second_level', 'EV values are only used in second_level analysis'
        grab_n_inputs = lambda s: re.match('# Higher-level EV value for EV 1 and input \d+$', s)
        temp = [grab_n_inputs(s) for s in self.data if grab_n_inputs(s) != None]
        last_index = -1
        for i in range(self.n_inputs):
            if i < len(temp):
                self.data[self.data.index(temp[i].string) + 1] = 'set fmri(evg' + str(i + 1) + '.1) 1.0'
                last_index = self.data.index(temp[i].string) + 1
            else:
                self.data.insert(last_index + 2, '# Higher-level EV value for EV 1 and input ' + str(i + 1))
                self.data.insert(last_index + 3, 'set fmri(evg' + str(i + 1) + '.1) 1.0')
                self.data.insert(last_index + 4, '')
                last_index = last_index + 3

    def set_group_membership(self):
        assert self.analysis == 'second_level', 'Group membership is only used in second_level analysis'
        grab_n_inputs = lambda s: re.match('# Group membership for input \d+$', s)
        temp = [grab_n_inputs(s) for s in self.data if grab_n_inputs(s) != None]
        last_index = -1
        for i in range(self.n_inputs):
            if i < len(temp):
                self.data[self.data.index(temp[i].string) + 1] = 'set fmri(groupmem.' + str(i + 1) + ') 1'
                last_index = self.data.index(temp[i].string) + 1
            else:
                self.data.insert(last_index + 2, '# Group membership for input ' + str(i + 1))
                self.data.insert(last_index + 3, 'set fmri(groupmem.' + str(i + 1) + ') 1')
                self.data.insert(last_index + 4, '')
                last_index = last_index + 3

    def set_output_directory(self, output_directory):
        # output directory
        self.data[self.data.index('# Output directory')+1] = 'set fmri(outputdir) ' + '"' + output_directory + '"'

    def set_4D_data(self, inputs_4D):
        grab_n_inputs = lambda s: re.match('# 4D AVW data or FEAT directory \(\d+\)$', s)
        temp = [grab_n_inputs(s) for s in self.data if grab_n_inputs(s) != None]
        self.n_inputs = len(inputs_4D)
        last_index = -1
        for i in range(len(inputs_4D)):
            if i < len(temp):
                if self.analysis == 'first_level':
                    self.data[self.data.index(temp[i].string) + 1] = 'set feat_files(' + str(i+1) + \
                                                                     ') ' + '"' + inputs_4D[i] + '"'
                elif self.analysis == 'second_level':
                    self.data[self.data.index(temp[i].string) + 1] = 'set feat_files(' + str(i + 1) + \
                                                                     ') ' + '"' + inputs_4D[i] + '.feat"'
                else:
                    warnings.warn('Should be first_level or second_level analysis')
                last_index = self.data.index(temp[i].string) + 1
            else:
                self.data.insert(last_index + 2, '# 4D AVW data or FEAT directory (' + str(i+1) + ')')
                if self.analysis == 'first_level':
                    self.data.insert(last_index + 3, 'set feat_files(' + str(i+1) + ') ' + '"' + inputs_4D[i] + '"')
                elif self.analysis == 'second_level':
                    self.data.insert(last_index + 3, 'set feat_files(' + str(i + 1) + ') ' + '"' +
                                                                                                inputs_4D[i] + '.feat"')
                else:
                    warnings.warn('Should be first_level or second_level analysis')
                self.data.insert(last_index + 4, '')
                last_index = last_index + 3
        self.data[self.data.index('# Number of first-level analyses') + 1] = 'set fmri(multiple) ' + str(len(inputs_4D))


    def set_structural_images(self, structural_images):
        assert self.analysis == 'first_level', 'Structural images are only used in first_level analysis'
        grab_n_inputs = lambda s: re.match('# Subject\'s structural image for analysis \d+$', s)
        temp = [grab_n_inputs(s) for s in self.data if grab_n_inputs(s) != None]
        last_index = -1
        for i in range(len(structural_images)):
            if i < len(temp):
                self.data[self.data.index(temp[i].string) + 1] = 'set highres_files(' + str(i+1) + ') ' + \
                                                                                    '"' + structural_images[i] + '"'
                last_index = self.data.index(temp[i].string) + 1
            else:
                self.data.insert(last_index + 2, '# Subject\'s structural image for analysis ' + str(i+1))
                self.data.insert(last_index + 3, 'set highres_files(' + str(i+1) + ') ' +
                                                                                    '"' + structural_images[i] + '"')
                self.data.insert(last_index + 4, '')
                last_index = last_index + 3

    def write(self, filename):
        self.filename = filename
        with open(self.filename, 'w') as outfile:
            outfile.write('\n'.join(self.data))