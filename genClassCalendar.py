#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Creates vcalendar HTML for my syllabus every quarter. Coughs up output to stdout.

Here is a sample of the HTML generated:
<li class="vevent"><span class="dtstart">2015-06-22T09:30</span>&ndash;<span class="dtend">2015-06-22T10:55</span>: <span class="summary description"><a class="url" href="http://patrickbrianmooney.nfshost.com/~patrick/ta/m15/">English 10</a> lecture</span>, <span class="location">Girvetz 2127</span></li>

This script is copyright 2016-19 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""


import datetime


start_date_1 = "8/9/2016"       # date of first office hour, in US date format
start_date_2 = "8/11/2016"      # date of second office hour
weeks_in_term = 5               # summer session
time_of_first_OH = "T11:30:00"  # just a string that gets appended
end_of_first_OH = "T12:20:00"   # same
time_of_second_OH = "T15:30:00" # again ...
end_of_second_OH = "T16:30:00"
indent_spaces = 8
course_url = "/~patrick/ta/m16/"
the_location = """<a rel="muse" href="https://www.yelp.com/biz/nicolettis-cafe-isla-vista-2">Nicoletti's Cafe</a> in the University Center"""

def office_hour_string(the_date,the_beginning_time,the_end_time):
	the_string = " " * indent_spaces + "<li class=\"vevent\"><span class=\"dtstart\">" + the_date.strftime('%Y-%m-%d') + the_beginning_time + "</span>&ndash;<span class=\"dtend\">" + the_date.strftime('%m-%d-%Y') + the_end_time + "</span>: <a class=\"url summary description\" href=\"" + course_url + "\">" + "Patrick Mooney's office hours" + "</a>, <span class=\"location\">" + the_location + "</span></li>"
	return the_string

for which_week in range(weeks_in_term):
	print(office_hour_string(datetime.datetime.strptime(start_date_1, '%m/%d/%Y') + datetime.timedelta(weeks=which_week),time_of_first_OH,end_of_first_OH))
	print(office_hour_string(datetime.datetime.strptime(start_date_2, '%m/%d/%Y') + datetime.timedelta(weeks=which_week),time_of_second_OH,end_of_second_OH))
