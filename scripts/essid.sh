#!/usr/bin/env bash
essid=`/sbin/iwconfig wlan0 2>/dev/null | grep "ESSID" | cut -d ":" -f2 | tr -d \"`
if [ -z "$essid" ]
then
    echo "NO"
else

    echo $essid
fi
