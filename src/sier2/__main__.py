import argparse
from importlib.metadata import version

from sier2 import Library, Config
from ._library import _find_blocks, _find_dags, run_dag
from ._util import block_doc_text, dag_doc_text

BOLD = '' # '\x1b[1;37m'
NORM = '' # '\x1b[0m'

def _pkg(module):
    return module.split('.')[0]

def blocks_cmd(args):
    """Display the blocks found via plugin entry points."""

    seen = set()
    curr_ep = None
    for entry_point, gi in _find_blocks():
        show = not args.block or gi.key.endswith(args.block)
        if curr_ep is None or entry_point!=curr_ep:
            if show:
                pkg = _pkg(entry_point.module)
                s = f'In {pkg} v{version(pkg)}'
                u = '' # '\n' + '#' * len(s)
                print(f'\n{BOLD}{s}{u}{NORM}')
                # print(f'\x1b[1mIn {entry_point.module} v{version(entry_point.module)}:\x1b[0m')
                curr_ep = entry_point

        if show:
            dup = f' (DUPLICATE)' if gi.key in seen else ''
            print(f'  {BOLD}{gi.key}: {gi.doc}{NORM}{dup}')

            if args.verbose:
                block = Library.get_block(gi.key)
                print(block_doc_text(block))
                print()

            seen.add(gi.key)

def dags_cmd(args):
    """Display the dags found via plugin entry points."""

    seen = set()
    curr_ep = None
    for entry_point, gi in _find_dags():
        show = not args.dag or gi.key.endswith(args.dag)
        if curr_ep is None or entry_point!=curr_ep:
            if show:
                pkg = _pkg(entry_point.module)
                s = f'In {pkg} v{version(pkg)}'
                u = '' # '\n' + '#' * len(s)
                print(f'\n{BOLD}{s}{u}{NORM}')
                curr_ep = entry_point

        if show:
            dup = f' (DUPLICATE)' if gi.key in seen else ''
            print(f'  {BOLD}{gi.key}: {gi.doc}{NORM}{dup}')

            if args.verbose:
                # We have to instantiate the dag to get the documentation.
                #
                dag = Library.get_dag(gi.key)
                print(dag_doc_text(dag))

            seen.add(gi.key)

def run_cmd(args):
    if args.config:
        Config.location = args.config

    if args.update_config:
        # A string of the form "block_name[,arg_string]".
        # `block_name`` must be the name of a block that has an `out_config` param.
        # The `out_config` param must contain a string that is the content of a sier2 ini file.
        # If `arg_string` is specified and the block has an `in_arg` param,
        # `in_arg` is set to `arg_string`.
        #
        # TODO after this works, move it to _config.py.
        #
        args = args.update_config.split(',')
        block_name = args[0]
        block = Library.get_block(block_name)
        if not hasattr(block, 'out_config'):
            raise ValueError('config block does not have out param "out_config"')

        if hasattr(block, 'in_arg'):
            in_arg = ','.join(args[1:])
            block.in_arg = in_arg

        block.execute()
        Config._update(block.out_config)

    run_dag(args.dag)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    run = subparsers.add_parser('run', help='Run a dag')
    run.add_argument('dag', type=str, help='A dag to run')
    run.add_argument('-C', '--config', default=None, help='Use this config file (default to personal config file)')
    run.add_argument('-U', '--update_config', default=None, help='A block that provides a config that updates the personal config file')
    run.set_defaults(func=run_cmd)

    blocks = subparsers.add_parser('blocks', help='Show available blocks')
    blocks.add_argument('-v', '--verbose', action='store_true', help='Show help')
    blocks.add_argument('block', nargs='?', help='Show all blocks ending with this string')
    blocks.set_defaults(func=blocks_cmd)

    dags = subparsers.add_parser('dags', help='Show available dags')
    dags.add_argument('-v', '--verbose', action='store_true', help='Show help')
    dags.add_argument('dag', nargs='?', help='Show all dags ending with this string')
    dags.set_defaults(func=dags_cmd)

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()

if __name__=='__main__':
    main()
