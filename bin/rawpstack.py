import splunk.Intersplunk as si
from splunk.mining.dcutils import getLogger
import os, re, glob

logger = getLogger()

DEFAULT_SEPARATOR = '.'
DEFAULT_FOI = 1
DEFAULT_REVERSE = False
DEFAULT_THREADID = ""
DEFAULT_TSI = 2

messages = {}
fields = ['_time','file', 'fileorder', 'threadno', 'threadaddr', 'threadid', 'stack']

def parse_raw_pstack(pstack_file, selected_thread_id=DEFAULT_THREADID, reverse=DEFAULT_REVERSE, separator=DEFAULT_SEPARATOR, fileorderindex=DEFAULT_FOI, tsindex=DEFAULT_TSI):
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
    fts = filename.split(separator)[tsindex] if len(filename.split(separator)) > tsindex else 0
    fts = fts if fts.find('.') == -1 else fts.split('.')[0]
    thread_no = -1
    thread_addr = -1
    thread_id = 0
    stack = []

    selected_thread_id = selected_thread_id.strip('"\' ').split(',')

    fp = open(pstack_file)
    row = {
        '_time': fts,
        'fileorder': int(fileorder)
    }

    for line in fp:
        linecount += 1

        logger.debug("lineno = %d" % linecount)

        if line.startswith("Thread "):
            # First merge stacks and add to row
            if stack:
                logger.debug("there is stack")

                if reverse in ('true', 'True', 1):
                    logger.debug("reversing stack")
                    stack = reversed(stack);

                row[thread_id] = '\n'.join(stack)
                    
                logger.debug("appending row")

            thread_raw = line
            ig, thread_no, ig, thread_addr, ig, thread_id = line.split()
            thread_id = thread_id.strip("):")
            logger.debug("Thread_id: %s" % thread_id)
            # reset stack
            stack = []
            continue

        if thread_id not in selected_thread_id:
            logger.debug("skipping sti=%s threadid=%s" % (selected_thread_id, thread_id))
            continue

        match=re.match(frame_re, line)
        if match:
            logger.debug("line matched frame_re")
            stack.append(line.strip())

        else:
            logger.warn("Unable to parse line #%d in %s file. '%s'" % (linecount, pstack_file, line)   )
            continue

    if stack:
        logger.debug("there is stack")

        if reverse in ('true', 'True', 1):
            logger.debug("reversing stack")
            stack = reversed(stack);

        row[thread_id] = '\n'.join(stack)
            
        logger.debug("appending row")

    output.append(row)
    fp.close()

    return output

def raw_pstack():

    results = []
    keywords, options = si.getKeywordsAndOptions()

    separator = options.get('separator', DEFAULT_SEPARATOR)
    fileorderindex = int(options.get('fileorderindex', DEFAULT_FOI))
    thread_id = options.get('threadid', DEFAULT_THREADID)
    reverse = options.get('reverse', DEFAULT_REVERSE)
    timeorderindex = int(options.get('timeorderindex', DEFAULT_TSI))


    if len(keywords)==0:
        raise Exception("requires path to pstack file(s)")


    gpath = keywords.pop(0).strip()
    logger.error("b4 gpath = %s" % gpath)
    gpath = gpath.replace("\\\\", "\\")
    gpath = gpath.replace("\[", "[")
    gpath = gpath.replace("\]", "]")
    logger.error("gpath = %s" % gpath)
    # find all files matching
    complete_path = os.path.expanduser(
        os.path.expandvars(gpath))
    glob_matches = glob.glob(complete_path)
    logger.debug("complete path: %s" % complete_path)
    logger.debug("glob matches: %s" % glob_matches)

    if len(glob_matches)==0:
        logger.error("No file matching %s" % complete_path)
        raise Exception("No files matching %s." % complete_path)


    for pfile in glob_matches:
        logger.error("parsing file: %s" % pfile)
        results += parse_raw_pstack(pfile, thread_id, reverse, separator, fileorderindex, timeorderindex)


    #return results
    return results

# noinspection PyUnreachableCode
if __name__ == '__main__':
    try:
        si.outputResults(raw_pstack(), messages)
    except Exception, e:
        import traceback
        stack = traceback.format_exc()
        si.generateErrorResults("Following error occurred while parsing pstack: '%s'." % (e))
        logger.error("%s. %s" % (e, stack))
