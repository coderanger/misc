from __future__ import with_statement
import sys
import os.path
import time
from optparse import OptionParser

import twitter
import daemon

class TracTweet(object):
    
    def __init__(self, argv):
        self.password = open('.password').read().strip()
        self.api = twitter.Api(username='TracProject', password=self.password)
        self.last_id = None
        if os.path.exists('.lastid'):
            self.last_id = open('.lastid').read().strip() or None
        parser = OptionParser()
        parser.add_option('-d', '--daemonize', action='store_true',
                          help='Daemonize and run in the background')
        parser.add_option('-t', '--time', metavar='SECONDS', default='180',
                          help='Run a check after the given number of seconds')
        self.options, args = parser.parse_args(argv)

    def check_friends(self):
        for status in self.api.GetFriendsTimeline(count=200, since_id=int(self.last_id or 0)):
            self.last_id = str(status.id)
            if '#trac' in status.text:
                self.post_status(status.text)
    
    def post_status(self, msg):
        open('.lastid', 'w').write(self.last_id)
        msg = msg.replace('#trac', '').strip()
        #print 'Posting "%s"'%msg
        self.api.PostUpdate(msg)
    
    def do_loop(self):
        while True:
            self.check_friends()
            time.sleep(int(self.options.time))
    
    def __call__(self):
        if self.options.daemonize:
            with daemon.DaemonContext():
                self.do_loop()
        else:
            print 'Starting TracTweet bot'
            self.do_loop()

def main():
    app = TracTweet(sys.argv[1:])
    app()

if __name__ == '__main__':
    main()