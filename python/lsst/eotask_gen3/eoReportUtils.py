"""This module contains functions make run reports for EO test data.

"""

import sys

import glob

import os

import shutil

import xml.etree.ElementTree as ET

from xml.dom import minidom

import yaml


CORNER_RAFTS = ['R00', 'R04', 'R40', 'R44']
SCIENCE_RAFTS = ['R01', 'R02', 'R03',
                 'R10', 'R11', 'R12', 'R13', 'R14',
                 'R20', 'R21', 'R22', 'R23', 'R24',
                 'R30', 'R31', 'R32', 'R33', 'R34',
                 'R41', 'R42', 'R43']
BOT_RAFTS = SCIENCE_RAFTS + CORNER_RAFTS

# The slots
ALL_SLOTS = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
CORNER_SLOTS = ['SG0', 'SG1', 'SW0', 'SW1']


def getSlotList(raftName):
    if raftName in CORNER_RAFTS:
        return CORNER_SLOTS
    return ALL_SLOTS

def makedir_safe(filepath):
    """Make a directory needed to write a file

    Parameters
    ----------
    filepath : `str`
        The file we are going to write
    """
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError:
        pass

def get_report_config_info(table_tag, **kwargs):
    """Get information about how to configure a report

    Parameters
    ----------
    table_tag : `str`
        The yaml tag to use for the table information

    Keywords
    --------
    template_file : `str` or `None`
        Path to the yaml template file
    css_file : `str` or `None`
        Path to the css style file

    Returns
    -------
    o_dict : `dict`
      cssfile : `str`
        Path to the css style file
      table_desc : `dict`
        Table description
      defaults : `dict`
        CSS style defaults
    """
    yamlfile = kwargs.get('template_file', None)
    if yamlfile is None:
        raise ValueError("You must specify a yaml file with the report template")
    cssfile = kwargs.get('css_file', None)
    if cssfile is None:
        raise ValueError("You must specify a .css style file")

    template_dict = yaml.safe_load(open(yamlfile))
    table_desc = template_dict.get(table_tag, None)
    if table_desc is None:
        table_desc = {}

    return dict(cssfile=cssfile,
                table_desc=table_desc,
                defaults=template_dict['defaults'])


def handle_file(file_name, outdir, action, overwrite=False):
    """Move, copy or link a file to an output directory

    Parameters
    ----------
    file_name : `str`
        The file in question
    outdir : `str`
        The output directory
    action : `str`
        What to do with the file, of `copy`, `move`, or `link`
    overwrite : `bool`
        Overwrite existing files

    Returns
    -------
    basename : `str`
        The basename of the file
    """
    basename = os.path.basename(file_name)
    if outdir is None:
        return basename

    inname = os.path.abspath(file_name)
    outname = os.path.abspath(os.path.join(outdir, basename))

    if overwrite:
        try:
            os.unlink(outname)
        except FileNotFoundError:
            pass
    else:
        if os.path.exists(outname):
            print("File %s exists, skipping" % outname)
            return basename

    makedir_safe(outname)
    if action in ['copy', 'cp']:
        shutil.copyfile(inname, outname)
    elif action in ['move', 'mv']:
        shutil.move(inname, outname)
    elif action in ['link', 'ln']:
        os.symlink(inname, outname)
    else:
        raise ValueError("Unknown action %s" % action)
    return basename




def create_report_header(root, **kwargs):
    """Make the header node for the report

    Parameters
    ----------
    root : `xml.etree.ElementTree.Element`
        The root node

    Keywords
    --------
    title : `str`
        The title for the HTML page
    stylesheet : `str`
        The css style sheet for the page

    Returns
    -------
    head : `xml.etree.ElementTree.SubElement`
        The header node

    """
    title = kwargs.get('title', None)
    stylesheet = kwargs.get('stylesheet', None)

    head = ET.SubElement(root, 'head')

    if title is not None:
        make_child_node(head, 'title', text=title)

    if stylesheet is not None:
        link = make_child_node(head, 'link',
                               href=stylesheet,
                               rel="StyleSheet")
        # This is out here b/c 'type' is a python keyword
        link.set('type', "text/css")

    return head




def make_child_node(parent_node, child_name, **kwargs):
    """Create a row in a table with a description and a plot

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node
    chile_name : `str`
        The name of the child node

    Keywords
    --------
    text : `str`
        The text to write in the node
    node_class : `str`
        The css class to use for this node

    Remaining kwargs are set as attributes in the node

    Returns
    -------
    child_node : `xml.etree.ElementTree.SubElement`
        The child node
    """
    child_node = ET.SubElement(parent_node, child_name)
    for key, val in kwargs.items():
        if val is None:
            continue
        if key == 'text':
            child_node.text = val
        elif key == 'node_class':
            child_node.set('class', val)
        else:
            child_node.set(key, val)
    return child_node


def create_plot_table_row(tbody_node, desc, plot_file, outdir, **kwargs):
    """Create a row in a table with a description and a plot

    Parameters
    ----------
    tbody_node : `xml.etree.ElementTree.SubElement`
        The table node
    desc : `str`
        The description of the plot
    plot_file : `str`
        The name of the file with the plot
    outdir : `str`
        The name of the directory the html is being written to

    Keywords
    --------
    plot_report_action : `str`
        What to do with the plot file, of `copy`, `move`, or `link`
    overwrite : `bool`
        Overwrite existing files
    row_class : `str`
        The style class to use for the row node
    col_desc_class : `str`
        The style class to use for the description column node
    col_fig_class : `str`
        The style class to use for the figure column node
    col_img_class : `str`
        The style class to use for the figure image node

    Returns
    -------
    row_node : `xml.etree.ElementTree.SubElement`
        The row node
    """
    plot_files = glob.glob(plot_file)
    if not plot_files:
        sys.stdout.write("Warning, skipping missing plot %s\n" % plot_file)
        return None

    basename = handle_file(plot_files[0], outdir,
                           kwargs.get('action', 'link'),
                           kwargs.get('overwrite', False))

    row_node = make_child_node(tbody_node, 'tr', node_class=kwargs.get('row_class', None))
    make_child_node(row_node, 'td',
                    node_class=kwargs.get('col_desc_class', None),
                    text=desc)
    col_fig_node = make_child_node(row_node, 'td',
                                   node_class=kwargs.get('col_fig_class', None))

    col_fig_ref = make_child_node(col_fig_node, 'a', href=basename)
    make_child_node(col_fig_ref, 'img',
                    node_class=kwargs.get('col_img_class', None),
                    src=basename)

    return row_node


def create_slot_table(parent_node, raft_name, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node
    raft_name : `str`
        Name of the raft in question


    Keywords
    --------
    header_row_class : `str`
        The style class to use for the header row node
    header_col_class : `str`
        The style class to use for the header column node
    table_row_class : `str`
        The style class to use for the row node
    table_col_class : `str`
        The style class to use for the description column node

    Returns
    -------
    table_node : `xml.etree.ElementTree.SubElement`
        The table node
    """
    kwcopy = kwargs.copy()
    prefix = kwcopy.get('prefix', '')

    html_file = kwargs.get('html_file', None)
    if html_file is not None:
        basedir = os.path.dirname(html_file)
    else:
        basedir = None

    h3_node = make_child_node(parent_node, 'h3', text="List of CCDs")

    table_node = make_child_node(parent_node, 'table')
    tbody_node = make_child_node(table_node, 'tbody')

    header_row_node = make_child_node(tbody_node, 'tr',
                                      node_class=kwcopy.get('header_row_class', None))
    make_child_node(header_row_node, 'td',
                    node_class=kwcopy.get('header_col_class', None),
                    text='CCD')

    nslot = 0
    slots = getSlotList(raft_name)
    for slot in slots:
        if basedir is not None:
            slot_path = os.path.join(basedir, "%s%s.html" % (prefix, slot))
            if not os.path.exists(slot_path):
                continue

        nslot += 1
        row_node = make_child_node(tbody_node, 'tr',
                                   node_class=kwcopy.get('table_row_class', None))
        if row_node is None:
            continue
        col_node = make_child_node(row_node, 'td',
                                   node_class=kwcopy.get('table_col_class', None))
        make_child_node(col_node, 'a',
                        text=slot,
                        href="%s%s.html" % (prefix, slot))

    if not nslot:
        print("No slot data in %s, skipping" % basedir)
        parent_node.remove(h3_node)
        parent_node.remove(table_node)
        return None

    return table_node


def create_raft_table(parent_node, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node

    Keywords
    --------
    header_row_class : `str`
        The style class to use for the header row node
    header_col_class : `str`
        The style class to use for the header column node
    table_row_class : `str`
        The style class to use for the row node
    table_col_class : `str`
        The style class to use for the description column node

    Returns
    -------
    table_node : `xml.etree.ElementTree.SubElement`
        The table node
    """
    kwcopy = kwargs.copy()
    prefix = kwcopy.get('prefix', '')

    html_file = kwargs.get('html_file', None)
    rafts = kwargs.get('rafts', BOT_RAFTS)

    h3_text = kwargs.get('h3_text', 'List of rafts')
    if html_file is not None:
        basedir = os.path.dirname(html_file)
    else:
        basedir = None

    h3_node = make_child_node(parent_node, 'h3', text=h3_text)

    table_node = make_child_node(parent_node, 'table')
    tbody_node = make_child_node(table_node, 'tbody')

    header_row_node = make_child_node(tbody_node, 'tr',
                                      node_class=kwcopy.get('header_row_class', None))
    make_child_node(header_row_node, 'td',
                    node_class=kwcopy.get('header_col_class', None),
                    text='RAFT')

    nraft = 0
    for raft in rafts:
        if basedir is not None:
            raft_path = os.path.join(basedir, raft, "%sindex.html" % prefix)
            if not os.path.exists(raft_path):
                continue

        nraft += 1
        row_node = make_child_node(tbody_node, 'tr',
                                   node_class=kwcopy.get('table_row_class', None))
        if row_node is None:
            continue
        col_node = make_child_node(row_node, 'td',
                                   node_class=kwcopy.get('table_col_class', None))
        make_child_node(col_node, 'a',
                        text=raft,
                        href=os.path.join(raft, "%sindex.html" % prefix))

    if not nraft:
        parent_node.remove(h3_node)
        parent_node.remove(table_node)
        return None

    return table_node



def create_plot_table(parent_node, table_desc, inputdir, outdir, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node
    table_desc : `list`
        A list of dictionaries with the plots and the descriptions
    inpudir : `str`
        The name of the directory with the plots
    outdir : `str`
        The name of the directory the html is being written to

    Keywords
    --------
    kwargs are passed to create_plot_table_row

    Returns
    -------
    table_node : `xml.etree.ElementTree.SubElement`
        The table node
    """
    kwcopy = kwargs.copy()
    dataid = kwcopy.pop('dataid', None)

    table_node = make_child_node(parent_node, 'table')
    tbody_node = make_child_node(table_node, 'tbody')

    header_col_class = kwcopy.get('header_col_class', None)

    header_row_node = make_child_node(tbody_node, 'tr',
                                      node_class=kwcopy.get('header_row_class', None))
    make_child_node(header_row_node, 'td',
                    text="Description",
                    node_class=header_col_class)
    make_child_node(header_row_node, 'td',
                    text="Plot",
                    node_class=header_col_class)

    rowlist = table_desc.get('rows', [])
    nrows = 0
    for row_desc in rowlist:
        plotfile = os.path.join(inputdir, row_desc['figure'].format(**dataid))
        row_node = create_plot_table_row(tbody_node, row_desc['text'],
                                         plotfile, outdir, **kwcopy)
        if row_node is not None:
            nrows += 1
    if nrows == 0:
        sys.stdout.write("Warning, skipping empty table\n")
        parent_node.remove(table_node)
        return None

    return table_node


def create_plot_tables(parent_node, table_dict, inputdir, outdir, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node
    table_dict : `dict`
        A dictionaries with the table descriptions
    inpudir : `str`
        The name of the directory with the plots
    outdir : `str`
        The name of the directory the html is being written to

    Keywords
    --------
    kwargs are passed to create_plot_table_row

    Returns
    -------
    table_node : `xml.etree.ElementTree.SubElement`
        The table node
    """
    ntable = 0
    for _, tdesc in table_dict.items():
        h3_node = make_child_node(parent_node, 'h3', text=tdesc.get('header_text', None))
        tnode = create_plot_table(parent_node, tdesc, inputdir, outdir, **kwargs)
        if tnode is None:
            parent_node.remove(h3_node)
            continue
        ntable += 1
    return ntable




def write_tree_to_html(tree, filepath=None):
    """Write a html file from an element tree

    Parameters
    ----------
    tree : `xml.etree.ElementTree.Element`
        The tree we are writing
    filepath : `str` or `None`
        Where to write the file
    """
    if filepath is None:
        outfile = sys.stdout
    else:
        outfile = open(filepath, 'w')

    rough_str = ET.tostring(tree)
    reparsed = minidom.parseString(rough_str)
    pretty_str = reparsed.toprettyxml(indent="  ")

    outfile.write(pretty_str)

    if filepath is not None:
        print("wrote %s" % filepath)
        outfile.close()


def write_slot_report(dataid, inputbase, outbase, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    dataid : `dict`
        Dictionary with run, raft, slot
    inputbase : `str`
        Input base directory
    outbase : `str` or `None`
        Output directory

    Keywords
    --------
    """
    kwcopy = kwargs.copy()

    sys.stdout.write("Writing report for {run}:{raft}:{slot}\n".format(**dataid))

    config_info = get_report_config_info('slot_plot_tables', **kwcopy)

    kwcopy.update(config_info['defaults'])
    kwcopy['dataid'] = dataid

    if outbase is None:
        outdir = None
        html_file = None
    else:
        outdir = os.path.join(outbase, dataid['run'], dataid['raft'])
        html_file = os.path.join(outdir, '%s.html' % dataid['slot'])

    html_node = ET.Element('html')
    create_report_header(html_node,
                         title="BOT Results for {run}:{raft}:{slot}".format(**dataid),
                         stylesheet=kwcopy.pop('stylesheet', os.path.basename(config_info['cssfile'])))

    body_node = make_child_node(html_node, 'body')

    ntables = create_plot_tables(body_node, config_info['table_desc'], inputbase, outdir, **kwcopy)
    if ntables:
        makedir_safe(html_file)
        _ = handle_file(config_info['cssfile'], outdir, action='copy')
        write_tree_to_html(html_node, html_file)
    else:
        sys.stdout.write("No data, skipping\n")



def write_raft_report(dataid, inputbase, outbase, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    dataid : `dict`
        Dictionary with run, raft
    inputbase : `str`
        Input base directory
    outbase : `str` or `None`
        Output directory

    Keywords
    --------
    """
    kwcopy = kwargs.copy()

    sys.stdout.write("Writing report for {run}:{raft}\n".format(**dataid))

    config_info = get_report_config_info('raft_plot_tables', **kwcopy)

    kwcopy.update(config_info['defaults'])
    kwcopy['dataid'] = dataid

    if outbase is None:
        outdir = None
        html_file = None
    else:
        outdir = os.path.join(outbase, dataid['run'], dataid['raft'])
        html_file = os.path.join(outdir, 'index.html')

    kwcopy['html_file'] = html_file
    html_node = ET.Element('html')
    create_report_header(html_node,
                         title="Results for {run}:{raft}".format(**dataid),
                         stylesheet=kwcopy.pop('stylesheet', os.path.basename(config_info['cssfile'])))

    body_node = make_child_node(html_node, 'body')

    ntables = create_plot_tables(body_node, config_info['table_desc'], inputbase, outdir, **kwcopy)

    slots = getSlotList(dataid['raft'])
    for slot in slots:
        dataid_slot = dataid.copy()
        dataid_slot['slot'] = slot
        kwcopy.pop('dataid', None)
        write_slot_report(dataid_slot, inputbase, outbase, **kwcopy)

    kwcopy['dataid'] = dataid
    slot_table_node = create_slot_table(body_node, dataid['raft'], **kwcopy)

    if ntables or slot_table_node is not None:
        makedir_safe(html_file)
        _ = handle_file(config_info['cssfile'], outdir, action='copy')
        write_tree_to_html(html_node, html_file)
    else:
        sys.stdout.write("No data, skipping raft\n")


def write_run_report(run, inputbase, outbase, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    run : `str`
        Run id
    inputbase : `str`
        Input base directory
    outbase : `str` or `None`
        Output directory

    Keywords
    --------
    """
    kwcopy = kwargs.copy()

    config_info = get_report_config_info('run_plot_tables', **kwcopy)

    kwcopy.update(config_info['defaults'])
    dataid = dict(run=run)
    kwcopy['dataid'] = dataid

    if outbase is None:
        outdir = None
        html_file = None
    else:
        outdir = os.path.join(outbase)
        html_file = os.path.join(outdir, 'index.html')

    kwcopy['html_file'] = html_file
    sys.stdout.write("Writing report for {run}\n".format(**dataid))

    html_node = ET.Element('html')
    create_report_header(html_node,
                         title="Results for {run}".format(**dataid),
                         stylesheet=kwcopy.pop('stylesheet', os.path.basename(config_info['cssfile'])))

    body_node = make_child_node(html_node, 'body')

    ntables = create_plot_tables(body_node, config_info['table_desc'], inputbase, outdir, **kwcopy)

    for raft in BOT_RAFTS:
        dataid_raft = dataid.copy()
        dataid_raft['raft'] = raft
        kwcopy.pop('dataid', None)
        write_raft_report(dataid_raft, inputbase, outbase, **kwcopy)

    kwcopy['dataid'] = dataid
    raft_table_node = create_raft_table(body_node, **kwcopy)

    if ntables or raft_table_node is not None:
        makedir_safe(html_file)
        _ = handle_file(config_info['cssfile'], outdir, action='copy')
        write_tree_to_html(html_node, html_file)
    else:
        sys.stdout.write("No data, skipping raft\n")

