#!/usr/bin/env python

import argparse
import re
import yaml
from pathlib import Path


def check_exists(fp):
    '''Check if file in fp exists
    
    :param fp: Path object to file to test
    '''
    if not fp.exists():
        raise ValueError("%s does not exist" % fp)


def extract_contributors(contributor_fp):
    '''Extract list of contributors
    
    :param fp: Path object to file with contributors
    '''
    contributors = {}
    with open(contributor_fp, 'r') as contributor_f:
        contributors = yaml.load(contributor_f)
    return contributors


def get_author_name(author_id, contributors):
    '''Get author name from list of contributors

    :param author_id: GitHub id of the author
    :param contributors: dictionary with contributor details
    '''
    if author_id in contributors and 'name' in contributors[author_id]:
        return contributors[author_id]['name']
    else:
        return author_id


def get_time(time):
    '''Get time from metadata
    
    :param time: time from metadata
    '''
    if 'h' in time:
        return time.replace('h', ' hours')
    elif 'H' in time:
        return time.replace('H', ' hours')
    elif 'm' in time:
        return time.replace('m', ' minutes')
    elif 'M' in time:
        return time.replace('M', ' minutes')


def create_abstract(metadata):
    '''Create an abstract from the metadata of the tutorial

    :param 
    '''
    a = "<why/aim (1st paragraph of the introduction)>. " \
        "This tutorial is developed for the data analysis platform Galaxy. " \
        "The Galaxy's concept makes high-throughput sequencing data analysis a " \
        "structured, reproducible and transparent process. "
    a += "In this tutorial we focus on %s questions: %s " % (
        len(metadata['questions']), 
        ' '.join(metadata['questions']))
    a += "After finishing this tutorial you will be able to %s." % (
        ', '.join([s[0].lower() + s[1:] for s in metadata['objectives']]))
    a += "Requirements for this tutorial is a minimal Galaxy experience and " \
        "a Galaxy account on the Galaxy Europe server. "
    a += "The estimated duration of this tutorial is around %s." % (
        get_time(metadata['time_estimation']))
        
    return a


def extract_metadata(yaml_metadata, contributor_fp):
    '''Extract metadata needed by pandoc from tutorial and contributors

    :param yaml_metadata: YAML content on the top of a tutorial
    :param contributor_fp: Path object to file with contributors
    '''
    metadata = {
        'title': '',
        'author': [],
        'abstract': '',
        'bibliography': 'references.bib'
    }
    contributors = extract_contributors(contributor_fp)
    
    metadata['title'] = yaml_metadata['title']
    for c in yaml_metadata['contributors']:
        metadata['author'].append(get_author_name(c, contributors))
    metadata['abstract'] = create_abstract(yaml_metadata)

    return metadata


def format_tuto_content(content, yaml_metadata, tuto_fp):
    '''Format the tutorial content (boxes)

    :param content: list with tutorial lines
    :param yaml_metadata: YAML content on the top of a tutorial
    :param tuto_fp: string with path to file with original tutorial
    '''
    l_content = []
    do_not_add_next_lines = False

    for l in content:
        # remove lines with includes
        if '{% include' in l:
            continue
        # remove questions, comments, details, tips, agenda boxes
        elif re.search(r'{% icon (question|details|comment|tip|warning) %}', l):
            do_not_add_next_lines = True
            continue
        elif '### Agenda' in l:
            do_not_add_next_lines = True
            continue
        elif do_not_add_next_lines:
            if re.search(r'{:[ ]?\.(question|details|comment|tip|warning|agenda)}', l):
                do_not_add_next_lines = False
            continue
        # format hands-on boxes
        elif '{% icon hands_on %}' in l:
            l = l.replace('> ### {% icon hands_on %} ', '***')
            l = l[:-1] +  '***\n'
        elif '{: .hands_on}' in l:
            continue
        elif l.startswith('> '):
            l = l[2:]
        elif l.startswith('>'):
            continue
        # remove {:.no_toc}
        elif re.search(r'{:[ ]?\.no_toc}', l):
            continue
        # rename 1st part
        elif '# Introduction' in l:
            l = '# Description of the data\n'

        l_content.append(l)

    # prepare introduction
    intro = "\n# Introduction\n\n" \
        "<why/aim (1st paragraph of the introduction)>.\n\n" \
        "This tutorial provides a detailed workflow for <outputs> from <inputs> using Galaxy." \
        "Galaxy [@afgan2018galaxy] is a data analysis platform that provides access to hundreds" \
        " of tools used in a wide variety of analysis scenarios. os. It features a web-based user " \
        "interface while automatically and transparently managing underlying computation details. " \
        "The Galaxy's concept makes high-throughput sequencing data analysis a structured, "\
        "reproducible and transparent process.\n\n" \
        "The tutorial starts from <inputs>. It runs first a <overview of each step (1 sentence) of the "\
        "workflow with tool names in bold and citation.>\n\n" \
        "The entire analysis described this article can be conducted efficiently on any Galaxy server "\
        "which has the needed tools. However, to be sure, the authors recommend to use the Galaxy "\
        "Europe server (https://usegalaxy.eu/).\n\n" \
        "The tutorial presented in this article has been developed by the Galaxy Training Network "\
        "[@batut2018community] and is available online at https://training.galaxyproject.org/"
    intro += tuto_fp.replace('md', 'html')
    intro += '.\n\n'

    # prepare references
    ref = "\n# References\n\n"

    # transform list of lines into string, add introduction, add references
    form_content = intro + ''.join(l_content) + ref

    # replace {{ page.zenodo_link }} by correct link
    form_content = form_content.replace(
        '{{ page.zenodo_link }}',
        yaml_metadata['zenodo_link'])

    # replace icons
    form_content = re.sub(r'{% icon [a-z\-\_]+ %}[ ]?', '', form_content)

    # replace {% cite ... %} by correct [@...]
    form_content = re.sub(r'{% cite ([a-z0-9\-\_]+) %}', '[@\g<1>]', form_content)

    return form_content


def format_tutorial(tuto_fp, formatted_tuto_fp, contributor_fp):
    '''Read tutorial content, format it for pandoc and export it
    
    1. Extract metadata needed by pandoc from tutorial and contributors
    2. Format tutorial content (boxes)
    3. Write in the output file

    :param tuto_fp: Path object to file with original tutorial
    :param formatted_tuto_fp: Path object to file with formatted tutorial for pandoc
    :param contributor_fp: Path object to file with contributors
    '''    
    with tuto_fp.open("r") as tuto_f:
        full_content = tuto_f.readlines()#yaml.load(tuto_f)

        yaml_content = ''
        for i, l in enumerate(full_content[1:]):
            if l.startswith("---"):
                break
        yaml_metadata = yaml.load(''.join(full_content[1:i]))

        metadata = extract_metadata(yaml_metadata, contributor_fp)
        formatted_tuto_content = format_tuto_content(
            full_content[i+2:],
            yaml_metadata,
            str(tuto_fp))
        
    with formatted_tuto_fp.open("w") as tuto_f:
        tuto_f.write('---\n')
        tuto_f.write(yaml.dump(metadata))
        tuto_f.write('---\n')
        tuto_f.write(formatted_tuto_content)


def add_references(article_ref_fp, tuto_ref_fp):
    '''
    Add references

    :param article_ref_fp: Path object to file with references for article
    :param tuto_ref_fp: Path object to file with references for tutorial
    '''
    ref = ''

    if tuto_ref_fp.exists():
        with tuto_ref_fp.open("r") as ref_f:
            ref = ref_f.read()
    
    ref += "@article{afgan2018galaxy,\n" \
        "  title={The Galaxy platform for accessible, reproducible and " \
        "collaborative biomedical analyses: 2018 update},\n" \
        "  author={Afgan, Enis and Baker, Dannon and Batut, B{\'e}r{\'e}nice " \
        "and Van Den Beek, Marius and Bouvier, Dave and {\v{C}}ech, Martin and " \
        "Chilton, John and Clements, Dave and Coraor, Nate and Gr{\"u}ning, Bj{\"o}rn " \
        "A and others},\n" \
        "  journal={Nucleic acids research},\n" \
        "  volume={46},\n" \
        "  number={W1},\n" \
        "  pages={W537--W544},\n" \
        "  year={2018},\n" \
        "  publisher={Oxford University Press}\n" \
        "}\n\n" \
        "@article{batut2018community,\n" \
        "  title={Community-driven data analysis training for biology},\n" \
        "  author={Batut, B{\'e}r{\'e}nice and Hiltemann, Saskia and Bagnacani, " \
        "Andrea and Baker, Dannon and Bhardwaj, Vivek and Blank, Clemens and Bretaudeau," \
        " Anthony and Brillet-Gu{\'e}guen, Loraine and {\v{C}}ech, Martin and Chilton, " \
        "John and others},\n" \
        "  journal={Cell systems},\n" \
        "  volume={6},\n" \
        "  number={6},\n" \
        "  pages={752--758},\n" \
        "  year={2018},\n" \
        "  publisher={Elsevier}\n" \
        "}\n"

    with article_ref_fp.open("w") as ref_f:
        ref_f.write(ref)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Format the tutorial file before pandoc')
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument('-t', '--tutorial', help="Path to tutorial directory", required=True)
    args = parser.parse_args()

    # get file paths
    tuto_dp = Path(args.tutorial)
    check_exists(tuto_dp)
    original_tuto_fp =  tuto_dp / "tutorial.md"
    check_exists(original_tuto_fp)
    article_dp = tuto_dp / "article"
    article_dp.mkdir(parents=True, exist_ok=True)
    formatted_tuto_fp = article_dp / "article.md"
    contributor_fp = Path("CONTRIBUTORS.yaml")
    check_exists(contributor_fp)

    # format tutorial
    format_tutorial(original_tuto_fp, formatted_tuto_fp, contributor_fp)

    # add references
    tuto_ref_fp = tuto_dp / "tutorial.bib"
    article_ref_fp = article_dp / "references.bib"
    add_references(article_ref_fp, tuto_ref_fp)

    