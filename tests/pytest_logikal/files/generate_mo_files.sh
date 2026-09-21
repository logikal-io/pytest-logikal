#!/bin/bash
pybabel compile -i complete.po -o complete.mo

old_date='2026-09-21'
new_date='2026-09-22'
sed -i "s/\\(\"PO-Revision-Date: \\)${old_date}/\\1${new_date}/" outdated.po
pybabel compile -i outdated.po -o outdated_header.mo
sed -i "s/\\(\"PO-Revision-Date: \\)${new_date}/\\1${old_date}/" outdated.po

old_message='translated'
new_message='translated outdated'
sed -i "s/msgstr \"${old_message}\"/msgstr \"${new_message}\"/" outdated.po
pybabel compile -i outdated.po -o outdated_message.mo
sed -i "s/msgstr \"${new_message}\"/msgstr \"${old_message}\"/" outdated.po
