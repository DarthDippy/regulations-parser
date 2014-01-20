import codecs
import logging
import sys

try:
    import requests_cache
    requests_cache.install_cache('fr_cache')
except ImportError:
    pass

from regparser.diff import treediff
from regparser.builder import Builder


logger = logging.getLogger('build_from')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python build_from.py regulation.xml title "
              + "notice_doc_# act_title act_section (Generate diffs? "
              + "True/False)")
        print("  e.g. python build_from.py rege.txt 12 2011-31725 15 1693 "
              + "False")
        exit()

    with codecs.open(sys.argv[1], 'r', 'utf-8') as f:
        reg = f.read()

    doc_number = sys.argv[3]

    #   First, the regulation tree
    reg_tree = Builder.reg_tree(reg)

    builder = Builder(cfr_title=int(sys.argv[2]),
                      cfr_part=reg_tree.label_id(),
                      doc_number=doc_number)

    #  Didn't include the provided version
    if not any(n['document_number'] == doc_number for n in builder.notices):
        print "Could not find notice_doc_#, %s" % doc_number
        exit()

    builder.write_notices()

    #   Always do at least the first reg
    logger.info("Version %s", doc_number)
    builder.write_regulation(reg_tree)
    builder.gen_and_write_layers(reg_tree, sys.argv[4:6])
    if len(sys.argv) < 7 or sys.argv[6].lower() == 'true':
        all_versions = {doc_number: reg_tree}
        for version, old, new_tree, notices in builder.revision_generator(
                reg_tree):
            logger.info("Version %s", version)
            all_versions[version] = new_tree
            builder.doc_number = version
            builder.write_regulation(new_tree)
            builder.gen_and_write_layers(new_tree, sys.argv[4:6], notices)

        # now build diffs - include "empty" diffs comparing a version to itself
        for lhs_version, lhs_tree in all_versions.iteritems():
            for rhs_version, rhs_tree in all_versions.iteritems():
                comparer = treediff.Compare(lhs_tree, rhs_tree)
                comparer.compare()
                builder.writer.diff(
                    reg_tree.label_id(), lhs_version, rhs_version
                ).write(comparer.changes)
