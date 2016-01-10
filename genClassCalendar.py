#!/usr/bin/env python
"""Creates vcalendar HTML for my syllabus every quarter. Coughs up output to stdout.

Here is a sample of the HTML generated:
<li class="vevent"><span class="dtstart">2015-06-22T09:30</span>&ndash;<span class="dtend">2015-06-22T10:55</span>: <span class="summary description"><a class="url" href="http://patrickbrianmooney.nfshost.com/~patrick/ta/m15/">English 10</a> lecture</span>, <span class="location">Girvetz 2127</span></li>
"""

import datetime

start_date_1 = "1/4/2016" # date of first office hour, in US date format
start_date_2 = "1/7/2016" # date of second office hour
weeks_in_term = 10 # a ten-week quarter
time_of_first_OH = "T14:00:00" # just a string that gets appended
end_of_first_OH = "T15:00:00" # same
time_of_second_OH = "T13:00:00" # again ...
end_of_second_OH = "T14:00:00"
indent_spaces = 6
course_url = "/~patrick/ta/w16/"
the_location = "CCS Office Trailer #1002"

def office_hour_string(the_date,the_beginning_time,the_end_time):
	the_string = " " * indent_spaces + "<li class=\"vevent\"><span class=\"dtstart\">" + the_date.strftime('%Y-%m-%d') + the_beginning_time + "</span>&ndash;<span class=\"dtend\">" + the_date.strftime('%m-%d-%Y') + the_end_time + "</span>: <a class=\"url summary description\" href=\"" + course_url + "\">" + "Patrick Mooney's office hours" + "</a>, <span class=\"location\">" + the_location + "</span></li>"
	return the_string

for which_week in range(weeks_in_term):
	print office_hour_string(datetime.datetime.strptime(start_date_1, '%m/%d/%Y') + datetime.timedelta(weeks=which_week),time_of_first_OH,end_of_first_OH)
	print office_hour_string(datetime.datetime.strptime(start_date_2, '%m/%d/%Y') + datetime.timedelta(weeks=which_week),time_of_second_OH,end_of_second_OH)
