#!/usr/bin/env python

import sys
import os
import optparse

import jinja2
from jinja2 import meta


class Configurator(object):
    """
    Usage: %prog TEMPLATE [CONTEXT_VARIABLES]
    Usage: %prog list

    This program takes configuration file templates and renders
    them with the supplied arguments as context variables.

    Run "%prog list" to show a list of the available templates.
    """

    EXIT_VALUES = {
        'OK': 0,
        'NO TEMPLATE PROVIDED': 1,
        'TEMPLATE NOT FOUND': 2,
        'CONTEXT VARIABLE NOT PROVIDED': 3,
    }

    def __init__(self, template_dir):
        self.usage = self.__doc__
        self.usage_pretty = self.usage.replace('%prog', 'configurator.py')

        self.loader = jinja2.FileSystemLoader(template_dir)
        self.env = jinja2.Environment(loader=self.loader, autoescape=False)

    def run(self, args):
        template_name = self.get_template_name(args)
        self.call_other_commands(template_name)
        context = self.get_template_context(template_name, args)
        output = self.render_template(template_name, context)
        print output

    def call_other_commands(self, cmd):
        if cmd == 'list':
            self.show_templates()
        elif cmd == '--help' or cmd == '-h':
            self.show_usage()

    def get_template_name(self, args):
        if len(args) == 0:
            print self.usage_pretty
            print
            print 'ERROR: you must specify a template'
            sys.exit(self.EXIT_VALUES['NO TEMPLATE PROVIDED'])
        return args[0]

    def show_usage(self):
        print self.usage_pretty
        sys.exit(self.EXIT_VALUES['OK'])

    def show_templates(self):
        for searchpath in self.loader.searchpath:
            print 'In %s:' % searchpath
            self.print_path(searchpath, searchpath)
        sys.exit(self.EXIT_VALUES['OK'])

    def print_path(self, path, base):
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                self.print_path(item_path, base)
            else:
                print item_path[len(base) + 1:]

    def get_template_variables(self, template_name):
        try:
            (source, filename, uptodate) = self.loader.get_source(self.env, template_name)
        except jinja2.TemplateNotFound as error:
            print 'ERROR: can not find template "%s"' % template_name
            print 'ERROR: search path was "%s"' % self.loader.searchpath
            sys.exit(self.EXIT_VALUES['TEMPLATE NOT FOUND'])
        ast = self.env.parse(source)
        variables = meta.find_undeclared_variables(ast)
        return variables

    def get_options(self, variables, args):
        parser = optparse.OptionParser(usage=self.usage)

        for var in variables:
            help_text = 'You must provide a value for "%s".' % var
            parser.add_option('--%s' % var, dest=var, help=help_text)

        (options, args) = parser.parse_args(args)
        return options

    def raise_error_on_missing_variables(self, variables, context):
        error =  'ERROR: "%s" is used in the template.\n'
        error += 'ERROR: please provide a value for it by using "--%s=VALUE"'
        for var in variables:
            if context[var] is None:
                print error % (var, var)
                sys.exit(self.EXIT_VALUES['CONTEXT VARIABLE NOT PROVIDED'])

    def get_context_from_options(self, variables, options):
        context = dict()
        for var in variables:
            context[var] = getattr(options, var)
        return context

    def get_template_context(self, template_name, args):
        variables = self.get_template_variables(template_name)

        options = self.get_options(variables, args)

        context = self.get_context_from_options(variables, options)

        self.raise_error_on_missing_variables(variables, context)

        return context

    def render_template(self, template_name, context):
        template = self.env.get_template(template_name)
        return template.render(**context)


if __name__ == '__main__':
    base = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base, 'templates')
    args = sys.argv[1:]

    configurator = Configurator(template_dir)
    configurator.run(args)
