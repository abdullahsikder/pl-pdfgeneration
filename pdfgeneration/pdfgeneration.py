#!/usr/bin/env python                                            
#
# pdfgeneration ds ChRIS plugin app
#
# (c) 2016-2019 Fetal-Neonatal Neuroimaging & Developmental Science Center
#                   Boston Children's Hospital
#
#              http://childrenshospital.org/FNNDSC/
#                        dev@babyMRI.org
#


import os
import sys
import json
import shutil
import pdfkit
import datetime
from pyvirtualdisplay import Display
sys.path.append(os.path.dirname(__file__))

# import the Chris app superclass
from chrisapp.base import ChrisApp


Gstr_title = """

Generate a title from 
http://patorjk.com/software/taag/#p=display&f=Doom&t=pdfgeneration

"""

Gstr_synopsis = """

(Edit this in-line help for app specifics. At a minimum, the 
flags below are supported -- in the case of DS apps, both
positional arguments <inputDir> and <outputDir>; for FS apps
only <outputDir> -- and similarly for <in> <out> directories
where necessary.)

    NAME

       pdfgeneration.py 

    SYNOPSIS

        python pdfgeneration.py                                         \\
            [-h] [--help]                                               \\
            [--json]                                                    \\
            [--man]                                                     \\
            [--meta]                                                    \\
            [--savejson <DIR>]                                          \\
            [-v <level>] [--verbosity <level>]                          \\
            [--version]                                                 \\
            <inputDir>                                                  \\
            <outputDir> 

    BRIEF EXAMPLE

        * Bare bones execution

            mkdir in out && chmod 777 out
            python pdfgeneration.py   \\
                                in    out

    DESCRIPTION

        `pdfgeneration.py` ...

    ARGS

        [-h] [--help]
        If specified, show help message and exit.
        
        [--json]
        If specified, show json representation of app and exit.
        
        [--man]
        If specified, print (this) man page and exit.

        [--meta]
        If specified, print plugin meta data and exit.
        
        [--savejson <DIR>] 
        If specified, save json representation file to DIR and exit. 
        
        [-v <level>] [--verbosity <level>]
        Verbosity level for app. Not used currently.
        
        [--version]
        If specified, print version number and exit. 

"""


class Pdfgeneration(ChrisApp):
    """
    An app that takes in prediction results and generates PDF.
    """
    AUTHORS                 = 'DarwinAI (jefferpeng@darwinai.ca)'
    SELFPATH                = os.path.dirname(os.path.abspath(__file__))
    SELFEXEC                = os.path.basename(__file__)
    EXECSHELL               = 'python3'
    TITLE                   = 'PDF generation plugin'
    CATEGORY                = ''
    TYPE                    = 'ds'
    DESCRIPTION             = 'An app that takes in prediction results and generates PDF'
    DOCUMENTATION           = 'http://wiki'
    VERSION                 = '0.1'
    ICON                    = '' # url of an icon image
    LICENSE                 = 'AGPL 3.0'
    MAX_NUMBER_OF_WORKERS   = 1  # Override with integer value
    MIN_NUMBER_OF_WORKERS   = 1  # Override with integer value
    MAX_CPU_LIMIT           = '' # Override with millicore value as string, e.g. '2000m'
    MIN_CPU_LIMIT           = '' # Override with millicore value as string, e.g. '2000m'
    MAX_MEMORY_LIMIT        = '' # Override with string, e.g. '1Gi', '2000Mi'
    MIN_MEMORY_LIMIT        = '' # Override with string, e.g. '1Gi', '2000Mi'
    MIN_GPU_LIMIT           = 0  # Override with the minimum number of GPUs, as an integer, for your plugin
    MAX_GPU_LIMIT           = 0  # Override with the maximum number of GPUs, as an integer, for your plugin

    # Use this dictionary structure to provide key-value output descriptive information
    # that may be useful for the next downstream plugin. For example:
    #
    # {
    #   "finalOutputFile":  "final/file.out",
    #   "viewer":           "genericTextViewer",
    # }
    #
    # The above dictionary is saved when plugin is called with a ``--saveoutputmeta``
    # flag. Note also that all file paths are relative to the system specified
    # output directory.
    OUTPUT_META_DICT = {}

    def define_parameters(self):
        """
        Define the CLI arguments accepted by this plugin app.
        Use self.add_argument to specify a new app argument.
        """
        self.add_argument('--imagefile', 
            dest         = 'imagefile', 
            type         = str, 
            optional     = False,
            help         = 'Name of image file submitted to the analysis')
        self.add_argument('--patientId', 
            dest         = 'patientId', 
            type         = str, 
            optional     = False,
            help         = 'Patient ID')

    def run(self, options):
        """
        Define the code to be run by this plugin app.
        """
        print(Gstr_title)
        print('Version: %s' % self.get_version())
        # fetch input data
        with open(f"{options.inputdir}/prediction-default.json") as f:
            classification_data = json.load(f)
        try: 
            with open(f"{options.inputdir}/severity.json") as f:
                severityScores = json.load(f)
        except:
            severityScores = None

        # output pdf here
        print(f"Creating pdf file in {options.outputdir}...")
        template_file = "pdf-covid-positive-template.html" 
        if classification_data['prediction'] != "COVID-19" or severityScores is None:
            template_file = "pdf-covid-negative-template.html"
        # put image file in pdftemple folder to use it in pdf
        shutil.copy(options.inputdir + '/' + options.imagefile, "pdftemplate/")
        with open(f"pdftemplate/{template_file}") as f:
            txt = f.read()
            # replace the values
            txt = txt.replace("${PATIENT_TOKEN}", options.patientId)
            txt = txt.replace("${PREDICTION_CLASSIFICATION}", classification_data['prediction'])
            
            prediction_analysis = ""
            for column_name in classification_data:
                prediction = classification_data.get(column_name, 'N/A')
                if (column_name != 'prediction') and (column_name != 'Prediction') and (column_name != '**DISCLAIMER**'):
                    percentage = f'{prediction} ({float(prediction)*100:.2f}%)'
                    prediction_analysis += f"<h3>{column_name}: <span>{percentage}</span></h3>"

            txt = txt.replace("${PRED_ANALYSIS}", prediction_analysis)
            txt = txt.replace("${X-RAY-IMAGE}", options.imagefile)

            time = datetime.datetime.now()
            txt = txt.replace("${month-date}", time.strftime("%c"))
            txt = txt.replace("${year}", time.strftime("%Y"))
            # add the severity value if prediction is covid
            if template_file == "pdf-covid-positive-template.html":
                txt = txt.replace("${GEO_SEVERITY}", severityScores["Geographic severity"])
                txt = txt.replace("${GEO_EXTENT_SCORE}", severityScores["Geographic extent score"])
                txt = txt.replace("${OPC_SEVERITY}", severityScores["Opacity severity"])
                txt = txt.replace("${OPC_EXTENT_SCORE}", severityScores['Opacity extent score'])
            with open("pdftemplate/specificPatient.html", 'w') as writeF:
                writeF.write(txt)
              
        try:
            disp = Display().start()
            pdfkit.from_file(['pdftemplate/specificPatient.html'], f"{options.outputdir}/patient_analysis.pdf")
        finally:
            disp.stop()

        # cleanup
        os.remove("pdftemplate/specificPatient.html")
        os.remove(f"pdftemplate/{options.imagefile}")
        


    def show_man_page(self):
        """
        Print the app's man page.
        """
        print(Gstr_synopsis)


# ENTRYPOINT
if __name__ == "__main__":
    chris_app = Pdfgeneration()
    chris_app.launch()
