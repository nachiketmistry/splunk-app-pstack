import splunk.Intersplunk as si
from splunk.mining.dcutils import getLogger
import os, re, glob

logger = getLogger()

DEFAULT_SEPARATOR = '.'
DEFAULT_FOI = 1

messages = {}
fields = ['file', 'fileorder', 'threadno', 'threadaddr', 'threadid', 'frameno', 'frameaddr', 'function', 'extra', '_raw']

def parse_pstack_file(pstack_file, separator=DEFAULT_SEPARATOR, fileorderindex=DEFAULT_FOI):
    global messages

    output = []
    linecount = 0

    '''
    frame re
    group 1 (\d+) captures the frame no
    group 2 (0x[0-9a-f]+) captures frome addr
    group 3 ([^(]*) captures class::function name
    group 4 (\([^(]*\)) captures arguments
    group 5 (from )? is ignore
    group 6 ([\w\.\/\(\)]*) captures external library name or arguments
    '''
    frame_re = r'#(\d+)\s+(0x[0-9a-f]+) in ([^(]*)(\([^(]*\))\s(from )?([\w\.\/\(\)]*)'

    # extract fileorder from filename
    fileorder = None
    filename = os.path.basename(pstack_file)
    fileorder = filename.split(separator)[fileorderindex]
    threadno = -1
    thread_addr = -1
    thread_id = 0

    fp = open(pstack_file)
    for line in fp:
        linecount += 1

        if line.startswith("Thread "):
            thread_raw = line
            ig, thread_no, ig, thread_addr, ig, thread_id = line.split()
            thread_id = thread_id.strip("):")
            continue

        frame_raw = line
        match=re.match(frame_re, line)
        if match:
            frame_no, frame_addr, function, extra = match.group(1), match.group(2), '%s %s' % (match.group(3), match.group(4)),  match.group(6)

        else:
            logger.error("Unable to parse line #%d in %s file. '%s'" % (linecount, pstack_file, line)   )
            #si.addWarnMessage(messages, "Unable to parse line #%d in %s file. '%s'" % (linecount, pstack_file, line))
            continue

        row = {
            'file': filename,
            'fileorder': int(fileorder),
            'threadno': int(thread_no),
            'threadaddr': thread_addr,
            'threadid': thread_id,
            'frameno': int(frame_no),
            'frameaddr': frame_addr,
            'function': function,
            'extra': extra,
            '_raw': '%s %s %s' % (pstack_file, thread_raw, frame_raw)
        }


        output.append(row)

    fp.close()

    return output

def parse_pstacks():

    results = []
    keywords, options = si.getKeywordsAndOptions()

    separator = options.get('separator', DEFAULT_SEPARATOR)
    fileorderindex = int(options.get('fileorderindex', DEFAULT_FOI))



    if len(keywords)==0:
        raise Exception("requires path to pstack file(s)")

    gpath = keywords.pop(0)
    gpath = gpath.replace("\\\\", "\\")
    gpath = gpath.replace('\[', '[')
    gpath = gpath.replace('\]', ']')
    # find all files matching
    complete_path = os.path.expanduser(
        os.path.expandvars(gpath))
    glob_matches = glob.glob(complete_path)
    logger.error("complete path: %s" % complete_path)
    logger.error("glob matches: %s" % glob_matches)

    if len(glob_matches)==0:
        logger.error("No file matching %s" % complete_path)
        raise Exception("No files matching %s." % complete_path)


    for pfile in glob_matches:
        logger.error("parsing file: %s" % pfile)
        results += parse_pstack_file(pfile, separator, fileorderindex)


    #return results
    return results

# noinspection PyUnreachableCode
if __name__ == '__main__':
    try:
        si.outputResults(parse_pstacks(), messages, fields)
    except Exception, e:
        import traceback
        stack = traceback.format_exc()
        si.generateErrorResults("Following error occurred while parsing pstack: '%s'." % (e))
        logger.error("%s. %s" % (e, stack))
