# essential frame is <CONTENT>
file_path_BGL = './data/BGL/BGL_2k.log'  # reduced log for test
log_format_BGL = '<TAG><SEQ><DATE><COMPONENT1><TIMESTAMP><COMPONENT2><COMPONENT3><PRIORITY><LEVEL><CONTENT>'

file_path_HDFS = './data/HDFS/HDFS_2k.log'
log_format_HDFS = '<DATE><TIME><PID><LEVEL><COMPONENT><CONTENT>'

file_path = file_path_BGL
log_format = log_format_BGL
log_keywords = 'Blue Gene/L(i.e. BGL)'
