from . command import Command
from .. util import *
from .. log import *
from . file_ops import *

import os
from datetime import datetime
import glob

class Pull(Command):
    @staticmethod
    def add_parser(sp):
        p = sp.add_parser('pull', 
            help='Pull changes from RRF/Duet device')
        p.add_argument('--force', '-f', action='store_true', default=False, 
            help='pull all, regardless of local file status')
        p.add_argument('--yes', '-y', action='store_true', default=False, 
            help='suppress overwrite confirmation')
        p.add_argument('file_patterns', action='store',
            help='File pathspec to pull', nargs='*',
            default=None)
        
    def __init__(self, cfg, args):
        super().__init__(cfg, args)
        self.connect()
        
    def run(self):
        report = build_status_report(self.dwa, self.cfg, self.directories)
        
        pull_files = {}
        if self.args.force or len(self.args.file_patterns) > 0:
            pull_files = report['remote_files']
            if len(self.args.file_patterns) > 0:
                pull_files = filter_by_patterns(pull_files, self.args.file_patterns)
        
        ro = report['remote_only']
        
        rn = list(report['remote_newer'].keys())
        rn.sort()
        ln = list(report['local_newer'].keys())
        ln.sort()
        ds = list(report['diff_size'].keys())
        ds.sort()
            
        if pull_files:
            status('Fetching files from remote...')
            paths = list(pull_files.keys())
            paths.sort()
            for path in paths:
                fo = pull_files[path]
                info(f'- {path}')
                fo.pullFile(self.dwa, self.cfg.dir)
        elif len(ro) > 0 or len(rn) > 0 or len(ln) > 0 or len(ds) > 0:
            if not self.args.yes and (len(ln) > 0 or len(ds) > 0) :
                if len(ln) > 0:
                    error('The following files have newer changes locally.')
                    for path in ln:
                        info(f'- {path}')
                if len(ds) > 0:
                    error('The following files differ only in size.')
                    for path in ds:
                        info(f'- {path}')
                if not yes_or_no('Overwrite local with remote?'):
                    return
            
            status('Fetching files from remote...')
            for path in ro:
                info(f'- {path}')
                report['remote_files'][path].pullFile(self.dwa, self.cfg.dir)
    
            for path, fo in report["remote_newer"].items():
                info(f'- {path}')
                fo.pullFile(self.dwa, self.cfg.dir)
                
            for path in ln:
                fo = report['remote_files'][path]
                info(f'- {path}')
                fo.pullFile(self.dwa, self.cfg.dir)
                
            for path, fo in report["diff_size"].items():
                info(f'- {path}')
                rfo = fo[0]
                rfo.pullFile(self.dwa, self.cfg.dir)
        else:
            success('No changes detected')
        