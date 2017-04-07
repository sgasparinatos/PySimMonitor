#!/usr/bin/env bash
iwconfig wlan0 | grep "ESSID" | cut -d ":" -f2 | tr -d \"
