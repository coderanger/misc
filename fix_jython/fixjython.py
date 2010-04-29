import re

inf = open('svndump', 'rb')
outf = open('svndumpfixed', 'wb')

rev_re = re.compile(r'^Revision-number: (\d+)$')
nodepath_re = re.compile(r'^Node-path: (\w+)/([^/]+)(/.+)?$')
copyfrom_re = re.compile(r'^Node-copyfrom-path:')
copyfrom_extract_re = re.compile(r'^Node-copyfrom-path: (.+)$')

fix = set()
# dont_fix = set(['unlabeled-1.1.2', '2.0', 'newstyle-branch', 'pep302',
#                 'collections-integration', '2.3'])
copyfrom_changed = set()

last_path = None
for line in inf:
    md = nodepath_re.match(line)
    if md:
        if not md.group(3):
            last_path = (md.group(1), md.group(2).strip())
        else:
            last_path = None
    md = rev_re.match(line)
    if md:
        last_path = None
    md = copyfrom_extract_re.match(line)
    if md and last_path:        
        if md.group(1) == 'trunk':
            top = last_path[0]
            if top == 'tags':
                top = 'tag'
            elif top == 'branches':
                top = 'branch'
            print '%s %s is clean'%(top.title(), last_path[1])
        elif md.group(1) == 'trunk/jython':
            fix.add(last_path)
        elif '/' in md.group(1):
            top, branch = md.group(1).split('/', 2)[0:2]
            if (top, branch) in fix:
                print 'Fixing %s/%s because it is copied from %s/%s'%(last_path[0], last_path[1], top, branch)
                fix.add(last_path) 
        last_path = None

inf.seek(0)

fix_copyfrom = False
last_path = None
for line in inf:
    md = rev_re.match(line)
    if md:
        fix_copyfrom = False
        print 'Processing rev %s'%md.group(1)
    md = nodepath_re.match(line)
    if md:
        last_path = (md.group(1), md.group(2).strip())
        if last_path in fix:
            if md.group(3):
                line = 'Node-path: %s/%s/jython%s\n'%(md.group(1), md.group(2), md.group(3) or '')
            else:
                print 'Setting fix_copyfrom on %s/%s'%last_path
                fix_copyfrom = True
    
    md = copyfrom_extract_re.match(line)
    if md:
        if fix_copyfrom:
            if md.group(1) == 'trunk/jython':
                print 'Copyfrom changed on %s/%s to trunk'%last_path
                copyfrom_changed.add(last_path)
                line = 'Node-copyfrom-path: trunk\n'
            fix_copyfrom = False
        if '/' in md.group(1):
            top, branch = md.group(1).split('/', 2)[0:2]
            if (top, branch) in fix:
                base = top+'/'+branch
                if md.group(1)[len(base):]:
                    line = 'Node-copyfrom-path: %s/jython%s\n'%(base, md.group(1)[len(base):])
                    print 'Copyfrom changed on %s/%s to %s/jython%s'%(last_path[0], last_path[1], base, md.group(1)[len(base):])
                    copyfrom_changed.add(last_path)
            
    outf.write(line)

inf.close()
outf.close()

for top, branch in sorted(fix):
    if top == 'tags':
        top = 'tag'
    elif top == 'branches':
        top = 'branch'
    print 'Fixing %s %s'%(top, branch)
    
for top, branch in sorted(copyfrom_changed):
    if top == 'tags':
        top = 'tag'
    elif top == 'branches':
        top = 'branch'
    print 'Changed copyfrom on %s %s'%(top, branch)
