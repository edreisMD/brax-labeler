"""Define report loader class."""
import re
import bioc
import pandas as pd
from negbio.pipeline import text2bioc, ssplit, section_split

from constants import *


class Loader(object):
    """Report impression loader."""
    def __init__(self, reports_path, extract_impression=False):
        self.reports_path = reports_path
        self.extract_impression = extract_impression
        self.punctuation_spacer = str.maketrans({key: f"{key} "
                                                 for key in ".,"})
        self.splitter = ssplit.NegBioSSplitter(newline=False)

    def load(self, batch = None):
        """Load and clean the reports."""
        collection = bioc.BioCCollection()
        reports = pd.read_csv(self.reports_path,
                              header=None,
                              names=[REPORTS])[REPORTS].tolist() 

        if batch != None:
            lista_reports_batch = [(batch*5000), (batch*5000 + 5000)]
            print(f"Loading {lista_reports_batch} reports.")
            reports = reports[(batch*5000):(batch*5000 + 5000)]


        for i, report in enumerate(reports):
            clean_report = self.clean(report)
            document = text2bioc.text2document(str(i), clean_report)

            if self.extract_impression:
                impression_split = re.split('CONCLUSAO:',
                                    document__)
                impression__ = impression_split[1]
                # print(impression__)

                document = section_split.split_document(document)
                self.extract_impression_from_passages(document)

            split_document = self.splitter.split_doc(document)

            assert len(split_document.passages) == 1,\
                ('Each document must have a single passage, ' +
                 'the Impression section.')

            collection.add_document(split_document)

        self.reports = reports
        self.collection = collection

    def extract_impression_from_passages(self, document):
        """Extract the Impression section from a Bioc Document."""
        impression_passages = []
        for i, passage in enumerate(document.passages):
            if 'title' in passage.infons:
                if passage.infons['title'] == 'opiniao':
                    next_passage = document.passages[i+1]
                    assert 'title' not in next_passage.infons,\
                        "Document contains empty impression section."
                    impression_passages.append(next_passage)

        assert len(impression_passages) <= 1,\
            (f"The document contains {len(document.passages)} impression (opiniao) " +
             "passages.")

        assert len(impression_passages) >= 1,\
            "The document contains no explicit impression passage."

        document.passages = impression_passages

    def clean(self, report):
        """Clean the report text."""
        # lower_report = report
        lower_report = str(report).lower()
        # Change `and/or` to `or`.
        corrected_report = re.sub('e/ou',
                                  'ou',
                                  lower_report)
        # Change any `XXX/YYY` to `XXX or YYY`.
        corrected_report = re.sub('(?<=[a-zA-Z])/(?=[a-zA-Z])',
                                  ' ou ',
                                  corrected_report)
        # Clean double periods
        clean_report = corrected_report.replace("..", ".")
        # Insert space after commas and periods.
        clean_report = clean_report.translate(self.punctuation_spacer)
        # Convert any multi white spaces to single white spaces.
        clean_report = ' '.join(clean_report.split())
        # Remove empty sentences
        clean_report = re.sub(r'\.\s+\.', '.', clean_report)

        return clean_report
