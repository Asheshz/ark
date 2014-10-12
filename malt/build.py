"""
This module handles the main site building process.

"""

import os

from . import site
from . import utils
from . import pages
from . import records
from . import tags


def build(srcdir, dstdir, themedir):
    """ Builds the site. Arguments are directory paths. """

    # Initialize the site model.
    site.init(srcdir, dstdir, themedir)

    # Copy the site's resource files to the destination directory.
    utils.copy_contents(srcdir, dstdir)

    # Copy the theme's resource files to the destination directory.
    if os.path.exists(site.theme('resources')):
        utils.copy_contents(site.theme('resources'), dstdir)

    # Build the individual record pages and directory indexes.
    for dirname, dirpath in utils.subdirs(srcdir):
        if dirname.startswith('@'):
            build_record_pages(dirpath)
            if site.type(dirname)['indexed']:
                build_directory_indexes(dirpath)

    # Build the tag index pages.
    build_tag_indexes()

    # Print a status report.
    status_report()


def build_record_pages(dirpath):
    """ Creates an HTML page for each record in the source directory. """

    for fileinfo in utils.files(dirpath):
        record = records.record(fileinfo.path)
        if record:
            page = pages.RecordPage(record)
            page.render()

    for dirinfo in utils.subdirs(dirpath):
        build_record_pages(dirinfo.path)


def build_directory_indexes(dirpath, recursing=False):
    """ Creates a paged index for each directory of records. """

    # Determine the record type from the directory path.
    typeid = site.type_from_src(dirpath)

    # Assemble a list of records in this directory and any subdirectories.
    index = []

    # Process subdirectories first.
    for dirinfo in utils.subdirs(dirpath):
        index.extend(build_directory_indexes(dirinfo.path, True))

    # Add any records in this directory to the index.
    for fileinfo in utils.files(dirpath):
        record = records.record(fileinfo.path)
        if record and site.type(typeid)['order_by'] in record:
            index.append(record)

    # Are we displaying this index on the homepage?
    if site.type(typeid)['homepage'] and not recursing :
        slugs = []
    else:
        slugs = site.slugs_from_src(dirpath)

    page = pages.IndexPage(
        typeid,
        slugs,
        index,
        site.type(typeid)['per_index']
    )
    page['flags']['is_dir_index'] = True
    page['trail'] = site.trail_from_src(dirpath)
    page.render()

    return index


def build_tag_indexes():
    """ Creates a paged index for each registered tag. """

    for typeid, recmap in tags.records().items():
        for slug, reclist in recmap.items():

            index = []
            for filepath in reclist:
                record = records.record(filepath)
                if site.type(typeid)['order_by'] in record:
                    index.append(record)

            page = pages.IndexPage(
                typeid,
                tags.slugs(typeid, slug),
                index,
                site.type(typeid)['per_tag_index']
            )
            page['tag'] = tags.names()[typeid][slug]
            page['flags']['is_tag_index'] = True
            page['trail'] = [site.type(typeid)['name'], page['tag']]
            page.render()


def status_report():
    """ Prints a status report with stats on the build. """
    pcount = site.page_count()
    btime = site.build_time()
    average = btime / (pcount or 1)
    status = "%s pages rendered in %.2f seconds. %.4f seconds per page."
    print(status % (pcount, btime, average))
