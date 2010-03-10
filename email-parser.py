#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79

from dateutil import parser
from urlparse import urlparse
from sys import stdin

# example:
# echo "title: test\nd:2010-02-03\nurl:http://w.de" | ./parser.py

# parsers (functions)
parsers = []
def title_parser(text):
    print "TITLE: " + text.strip()
parsers.append(title_parser)
def date_parser(text):
    print "DATE: " + parser.parse(text).strftime("%Y-%m-%d")
parsers.append(date_parser)
def urls_parser(text):
    lines = text.splitlines()
    if len(lines[0].strip()) > 0:
        print "WEB: " + lines[0].strip()
    for line in lines[1:]:
        assert(line[0] == " ")
        line = line.strip()
        pos_colon = line.index(':')
        if pos_colon == -1: raise "The following URL line doesn't contain a colon: " + line
        print "\t" + line
parsers.append(urls_parser)

fields = {'titl':title_parser}
fields['title'] = title_parser
fields['t'] = title_parser
fields['date'] = date_parser
fields['d'] = date_parser
fields['urls'] = urls_parser
fields['web'] = urls_parser
fields['url'] = urls_parser

# TODO: test to ensure bijection with the real data base fields

def parse(lines, line_nr):
    """Parse one or more lines belonging to one field."""
    pos_first_colon = lines.find(':')
    if pos_first_colon == -1 :
        raise "Line " + line_nr + " doesn't contain a semicolon and is not indented"
    field = lines[0:pos_first_colon]
    if not field.isalnum():
        raise "field name at line " + line_nr + " is not alphanumeric"
    if fields.has_key(field):
        fields[field](lines[pos_first_colon+1:])
    else:
        raise "field '" + field + "' is not known"

def process(text, line_nr=1):
    """It processes a text for one or more events, separated by blank lines.

    It raises exceptions with an error message for syntax errors.

    >>> process("title: test\nd:2010-02-03\nurl:http://w.de")
    TITLE: test
    DATE: 2010-02-03
    WEB: http://w.de

    >>> process("title: test\nd:2010-02-03\nurl:http://w.de\n news:http://n.w.de")
    TITLE: test
    DATE: 2010-02-03
    WEB: http://w.de
        news:http://n.w.de
    """
    text = text.expandtabs(2)
    text_to_parse = "" # all text for a field is added hier
    for line in text.splitlines():
        if line.strip() == "":
            next_lines = text.splitlines()[line_nr:]
            if len(next_lines) > 0: process(next_lines, line_nr=line_nr)
            return
        if line[0] == ' ':
            if text_to_parse == "":
                raise "Identation not expected at line " + line_nr
            text_to_parse += "\n" + line
            ++line_nr
            continue
        if text_to_parse == "":
            text_to_parse = line
            ++line_nr
            continue
        parse(text_to_parse, line_nr)
        text_to_parse = line
    parse(text_to_parse, line_nr)

if __name__ == '__main__':
    process(stdin.read())
