import os
import json
import pandas as pd
from config.settings import DATA_DIR


class Programs:
    def __init__(self):
        # Load Programs
        with open(os.path.join(DATA_DIR, 'us/programs.json'), 'r') as f:
            self.programs_dict = json.load(f)
        self.levels = self.programs_dict['levels']
        self.programs = self.programs_dict['programs']
        self.masters = self.programs_dict['masters']

        # Build up dict
        self.program2type = {}
        for t in self.programs_dict['type']:
            for p in self.programs_dict['type'][t]:
                self.program2type[p] = t
        assert len(set(self.programs) - set(self.program2type.keys())) == 0

        self.majors = pd.read_csv(os.path.join(DATA_DIR, 'tw/majors.csv'), sep=',', index_col='major_id', na_values=None)
        self.majors['major_name_upper'] = self.majors['major_name'].str.upper()

        for _, row in self.majors.iterrows():
            if row['major_name'] not in self.program2type:
                self.program2type[row['major_name']] = row['major_type']
            if row.name not in self.program2type:
                self.program2type[row.name] = row['major_type']

    def search_program(self, row, aid=None):
        # Append prefix and suffix for better matching
        row = ' ' + row + ' '
        program_level = None
        program_name = None

        # 1) Search for all CS programs in the 'programs.json'
        # Apply Phd but got MS offer
        if ' MS ' in row and ' PhD ' in row:
            program_level = 'MS'
        else:
            for level in self.levels:
                if ' ' + level + ' ' in row:
                    program_level = level
                    break

        for program in self.programs:
            if ' ' + program + ' ' in row:
                program_name = program
                break
        # 2) If we still can't find the program name, search for
        # non-CS program names
        row_upper = row.upper()
        if not program_name:
            for _, mrow in self.majors.iterrows():
                if ' ' + mrow['major_name_upper'] + ' ' in row_upper or \
                        ' ' + mrow['major_cabbr'] + ' ' in row_upper:
                    program_name = mrow['major_name']
                    break

        # 3) Still no luck, find from the major ids
        if not program_name:
            for _, mrow in self.majors.iterrows():
                if ' ' + mrow.name + ' ' in row_upper:
                    # Texas A&M corner case
                    if mrow.name == 'AM' and 'TEXAS AM' in row_upper:
                        continue
                    program_name = mrow['major_name']
                    break

        if program_level is not None:
            row = row.replace(' ' + program_level + ' ', ' ')
        if program_name is not None:
            row = row.replace(' ' + program_name + ' ', ' ')

        # Do some program "Abbr" mapping here
        if program_level is not None:
            # Phd program
            if program_level.startswith('P'):
                program_level = 'PhD'
            else:
                program_level = 'MS'

        if program_name is not None and program_level is None and program_name in self.masters:
            program_level = 'MS'

        return (program_level, program_name), row.strip()

    def normalize_program_name(self, program_level, program_name):
        """Normalize program name with given program level

        Sadly this part of code is just ugly... Someone have to do the
        dirty work

        Parameters
        ----------
        program_level : str or None
            Program level: ('MS', 'PhD', None)
        program_name : str
            Any possible program name, e.g. MSCS

        Returns
        -------
        str
            Normalized program name
        """
        program_type = self.program2type.get(program_name, '')
        if program_type == 'MEng':
            program_name = 'MEng'
        elif program_type == 'SE':
            program_name = program_name.replace(' ', '')
            program_name = 'MSSE' if program_name in ('SiliconValley', 'SV-SE', 'SE', 'SoftwareEngineering') else program_name
        elif program_type == 'IS':
            program_name = program_name.replace(' ', '')
            program_name = 'MSIS' if program_name in ('MasterofScienceinInformation',
                                                      'InformationSystem') else program_name
            program_name = 'MSIM' if program_name in ('InformationManagement') else program_name
        elif program_type == 'HCI':
            program_name = 'MHCI' if program_type in ('HCI', 'MS in HCI', 'Human-Computer Interaction') else program_name
            program_name = 'MCDE' if program_name == 'Human-Centered Design and Engineering' else program_name
        elif program_type == 'EE':
            if program_level == 'MS':
                program_name = 'MSEE' if program_name not in ('MSECE', 'MS ECE') else 'MS ECE'
            else:
                program_name = 'EE'
        elif program_type == 'CS':
            program_name = program_name.replace('CMU ', '')

            if program_name in ('MSCS', 'MS CS', 'MCS', 'Master of Science in Computer Science', 'MS in CS'):
                program_name = 'MSCS'
            elif program_name in ('Computer Science', 'CS', 'CSE'):
                program_name = 'MSCS' if program_level == 'MS' else 'CS'
            elif program_name in ('Professional CS', 'MCS', 'Master of Computer Science'):
                program_name = 'MCS'
            elif program_name in ('EE CS', 'EECS'):
                program_name = 'MS EECS' if program_level == 'MS' else 'EECS'
            elif program_name in ('CV', 'Computer Vision'):
                program_name = 'MSCV' if program_level == 'MS' else 'CV'
            else:
                program_name = 'MSIT-MOB' if program_name == 'MSIT-Mob' else program_name
                program_name = 'MSML' if program_name == 'MS in Machine Learning' else program_name
                program_name = 'MSDS' if program_name == 'MS DS' else program_name
        return program_name
