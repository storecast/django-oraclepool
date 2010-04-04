echo "Extracted from the response time log from Apache use the following conf:"
echo 'LogFormat "%a %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %T/%D" response'
if [ -n "$1" ] 
then
 grep "$1" /usr/local/projects/stureps/apache/logs/response_log > day.log
 grep -E -o '[0-9]+$' day.log > logtime.log
 sed 's/\//\./g' logtime.log > time.log
 lines=`cat time.log | wc -l`
 sum=`awk '{ sum += $1; } END { print sum; }' time.log`
 echo $sum $lines | awk '{ print $1/($2*1000000) }'
 echo "sec/req for $lines responses"
else 
 echo 'Provide a date of the form 17/Nov/2009'
fi
