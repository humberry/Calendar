import ui
import calendar
import datetime
import calendar
from  objc_util import *
from ctypes import *
import threading
import time
import console

class CalendarEvents(object):
  def __init__(self):
    self.store = ObjCClass('EKEventStore').alloc().init()

    access_granted = threading.Event()
    def completion(_self, granted, _error):
      access_granted.set()
    completion_block = ObjCBlock(completion, argtypes=[c_void_p, c_bool, c_void_p])
    self.store.requestAccessToEntityType_completion_(0, completion_block)
    access_granted.wait()

  def getTableViewList(self, start, end):
    events = self.getEvents(start, end)

    list = []
    for event in events:
      color = None
      allday = str(event.valueForKey_('allDay'))
      start = str(event.valueForKey_('startDate'))[:19]
      end = str(event.valueForKey_('endDate'))[:19]
      title = str(event.valueForKey_('title'))
      temp = str(event.valueForKey_('calendar'))
      if 'color' in temp:
        i = temp.index('color')
        color = temp[i+8:i+15]

      #start = time.strptime('2018-12-31 23:59:59', '%Y-%m-%d %H:%M:%S')
      start = self.convertDateWithOffset(start)
      end = self.convertDateWithOffset(end)
      list.append([allday, start, end, title, color])
    return list

  def convertDateWithOffset(self, date):
    date = time.strptime(date, '%Y-%m-%d %H:%M:%S')
    dst = time.localtime(time.mktime(date)).tm_isdst #1=y 0=n
    offset = (time.timezone / -3600) if (dst == 0) else (time.altzone / -3600) # timeoffset incl. daylight saving
    date = datetime.datetime(*date[:6])
    offset = datetime.timedelta(hours=offset)
    date += offset
    return date

  def getEvents(self, start, end):
    startDate = ObjCClass('NSDate').dateWithTimeIntervalSince1970_(time.mktime(time.strptime(start, '%Y-%m-%d %H:%M:%S')))
    endDate = ObjCClass('NSDate').dateWithTimeIntervalSince1970_(time.mktime(time.strptime(end, '%Y-%m-%d %H:%M:%S')))

    predicate = self.store.predicateForEventsWithStartDate_endDate_calendars_(startDate, endDate, None)
    events = self.store.eventsMatchingPredicate_(predicate)
    return events

class MyButtonClass(ui.View):
  def __init__(self, x, y, h, w, color, text, align, row):
    self.x = x
    self.y = y
    self.height = h
    self.width = w
    self.label = ui.Label(frame=(0, 0, w, h))
    self.label.text = text
    self.label.text_color = color
    self.label.border_color = color
    self.label.border_width = 1
    self.label.corner_radius = 5
    self.label.alignment = align
    self.label.font = '<System>', 12
    self.label.row = row
    self.add_subview(self.label)

  def touch_began(self, touch):
    self.label.text_color = 'black'
    c.eventview(self.label.row, self.label.text)

class MyTableViewDataSource(object):
  def __init__(self, row_height):
    self.row_height = row_height
    self.width = None

  def tableview_number_of_rows(self, tableview, section):
    return len(tableview.data_source.items)

  def tableview_cell_for_row(self, tableview, section, row):
    self.width, height = ui.get_screen_size()
    cell = ui.TableViewCell()
    cell.bounds = (0, 0, self.width, self.row_height)
    #number of items per row: tableview.data_source.items[row]
    x = 0
    y = row
    for i in range(len(tableview.data_source.items[row])):
      self.make_labels(cell, tableview.data_source.items[row][i][0], i, tableview.data_source.items[row][i][1], row)
    return cell

  def make_labels(self, cell, text, pos, color, row):
    if pos == 0:  # weekday = M, T, W, T, F, S, S
      label = ui.Label(frame=(0, 0, 20, 23))
      label.text = str(text)
      label.alignment = ui.ALIGN_CENTER
      label.frame = (5, 0, 20, self.row_height)
      label.text_color = color
      if text == 'S':
        label.text_color = 'red'
    elif pos == 1:  # day = 1 - 31
      label = ui.Label(frame=(0, 0, 20, 23))
      label.text = str(text)
      label.text_color = color
      label.alignment = ui.ALIGN_CENTER
      label.frame = (30, 0, 25, self.row_height)
    elif pos == 2:  # NEW event
      label = MyButtonClass(60, 0, self.row_height - 1, 40, color, text, ui.ALIGN_CENTER, row)
    elif pos > 2:  # Events
      label = MyButtonClass(160*(pos-3)+105, 0, self.row_height - 1, 155, color, text, ui.ALIGN_LEFT, row)
    cell.content_view.add_subview(label)

class Calendarapp(ui.View):
  def __init__(self):
    self.CE = CalendarEvents()
    self.newEvent = False
    self.alarms = []
    self.recurrences = []
    self.events = []
    self.day_list = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
    self.year = datetime.date.today().year
    self.month = datetime.date.today().month
    self.month_name = calendar.month_name[self.month]
    self.first_weekday, self.last_day = calendar.monthrange(self.year, self.month)
    self.view = ui.load_view('calendarapp')
    self.view['btnToday'].title = self.month_name + ' ' + str(self.year)
    self.view['btnToday'].action = self.btnToday_click
    self.view['btnLeft'].action = self.btnLeft_click
    self.view['btnRight'].action = self.btnRight_click
    self.tv = ui.TableView(frame=(0, 88, 375, 724), flex = 'WH')
    self.tv.allows_selection = False
    self.tv.separator_color = 'white'
    self.tv.row_height = 23
    self.tv.data_source = MyTableViewDataSource(self.tv.row_height)
    self.fill_events()
    self.view.add_subview(self.tv)
    self.view.present('fullscreen')

  def btnToday_click(self, sender):
    self.year = datetime.date.today().year
    self.month = datetime.date.today().month
    self.month_name = calendar.month_name[self.month]
    self.view['btnToday'].title = self.month_name + ' ' + str(self.year)
    self.first_weekday, self.last_day = calendar.monthrange(self.year, self.month)
    self.fill_events()

  def fill_events(self):
    self.events = []
    weekday = self.first_weekday
    today = [datetime.date.today().year, datetime.date.today().month, datetime.date.today().day]
    for i in range(self.last_day):
      if today[2] == i+1 and today[1] == self.month and today[0] == self.year:
        daylist = [[self.day_list[weekday], 'black'], [str(i+1), 'red'], ['NEW', 'darkred']]  #today = red
      else:
        daylist = [[self.day_list[weekday], 'black'], [str(i+1), 'black'], ['NEW', 'darkred']]
      self.events.append(daylist)
      weekday += 1
      if weekday > 6:
        weekday = 0
    ev = self.CE.getTableViewList(str(self.year) + '-' + str(self.month) + '-01 00:00:00', str(self.year) + '-' + str(self.month) + '-' + str(self.last_day) + ' 23:59:59')
    for e in ev:
      #list.append([allday, start, end, title, color])

      if (e[0] == '1' and str(e[1])[:10] == str(e[2])[:10]):  #all day AND start day == end day
        self.events[int(str(e[1])[8:10])-1].append([e[3], e[4]])  
      elif (e[0] == '0' and str(e[1])[:10] == str(e[2])[:10]):  # timespan AND start day == end day
        self.events[int(str(e[1])[8:10])-1].append([str(e[1].time())[:5] + ' ' + e[3], e[4]])
      elif (str(e[1])[:10] != str(e[2])[:10]):  # start day != end day
        first = time.strptime(str(self.year) + '-' + str(self.month) + '-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        last = time.strptime(str(self.year) + '-' + str(self.month) + '-' + str(self.last_day) + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        first = datetime.datetime(*first[:6])  #convert in datetime
        last = datetime.datetime(*last[:6])    #convert in datetime
        start = 1
        end = self.last_day
        if first <= e[1] <= last:  # start day in current month
          start = int(str(e[1])[8:10])
        if first <= e[2] <= last:  # end day in current month
          end = int(str(e[2])[8:10])
        for i in range(start-1, end):
          if e[0] == '1': #all day (no time)
            self.events[i].append([e[3], e[4]])  #[title, color]
          else:   #timespan
            self.events[i].append([str(e[1])[11:16] + ' ' + e[3], e[4]])  #[start time + title, color]
    self.tv.data_source.items = self.events
    self.tv.reload()

  def btnLeft_click(self, sender):
    self.month -= 1
    if self.month < 1:
      self.month = 12
      self.year -= 1
    self.month_name = calendar.month_name[self.month]
    self.view['btnToday'].title = self.month_name + ' ' + str(self.year)
    self.first_weekday, self.last_day = calendar.monthrange(self.year, self.month)
    self.fill_events()

  def btnRight_click(self, sender):
    self.month += 1
    if self.month > 12:
      self.month = 1
      self.year += 1
    self.month_name = calendar.month_name[self.month]
    self.view['btnToday'].title = self.month_name + ' ' + str(self.year)
    self.first_weekday, self.last_day = calendar.monthrange(self.year, self.month)
    self.fill_events()

  def eventview(self, row, text):
    self.viewE = ui.load_view('event')
    self.viewE['sv']['btnSave'].action = self.btnSave_click
    self.viewE['sv']['btnCancel'].action = self.btnCancel_click
    self.viewE['sv']['btnRemove'].action = self.btnRemove_click
    self.viewE['sv']['btnNext'].action = self.btnNext_click
    self.viewE['sv']['btnNext'].enabled = False
    self.viewE['sv']['btnRecurrences'].action = self.btnRecurrences_click
    self.viewE['sv']['btnAlarms'].action = self.btnAlarms_click
    self.viewE['sv']['swAllday'].action = self.swAllday_click
    self.recurrences = []
    self.alarms = []

    if text == 'NEW':
      self.newEvent = True
      self.viewE['sv']['btnRemove'].enabled = False
      #currentTime = str(time.localtime().tm_hour) + ':' + str(time.localtime().tm_min) + ':' + str(time.localtime().tm_sec)
      currentTime = str(time.localtime().tm_hour) + ':00:00'
      selectedDate = time.strptime(str(self.year) + '-' + str(self.month) + '-' + str(row+1) + ' ' + currentTime, '%Y-%m-%d %H:%M:%S')
      selectedDate = datetime.datetime(*selectedDate[:6])  #convert in datetime
      self.viewE['sv']['dpStart'].date = selectedDate
      d = datetime.timedelta(hours=1)
      self.viewE['sv']['dpEnd'].date = selectedDate + d
    else:
      self.newEvent = False
      self.viewE['sv']['btnRemove'].enabled = True
      if text[:2].isdigit() and text[2] == ':' and text[3:5].isdigit():  #starttime
        text = text[6:]
      start = str(self.year) + '-' + str(self.month) + '-' + str(row+1) + ' 00:00:00'
      end = str(self.year) + '-' + str(self.month) + '-' + str(row+1) + ' 23:59:59'
      self.detailedEvents = self.CE.getEvents(start, end)
      if len(self.detailedEvents) > 1:
        self.viewE['sv']['btnNext'].enabled = True
        self.viewE.eventcount = len(self.detailedEvents)
      i = 0
      for i in range(len(self.detailedEvents)):
        title = str(self.detailedEvents[i].valueForKey_('title'))
        if title == text:
          self.viewE.eventnumber = i
          location = str(self.detailedEvents[i].valueForKey_('location'))
          url = str(self.detailedEvents[i].valueForKey_('URL'))
          allday = str(self.detailedEvents[i].valueForKey_('allDay'))
          start = str(self.detailedEvents[i].valueForKey_('startDate'))[:19]
          end = str(self.detailedEvents[i].valueForKey_('endDate'))[:19]
          start = self.CE.convertDateWithOffset(start)
          end = self.CE.convertDateWithOffset(end)
          if self.detailedEvents[i].hasRecurrenceRules():
            self.viewE['sv']['btnRecurrences'].tint_color = 'red'
            recurrences = self.detailedEvents[i].valueForKey_('recurrenceRule')
            frequency = recurrences.valueForKey_('frequency')
            interval = recurrences.valueForKey_('interval')
            count = recurrences.valueForKey_('count')
            enddate = recurrences.valueForKey_('endDate')
            count = int(str(count))
            if enddate is not None:
              enddate = time.strptime(str(enddate)[:19], '%Y-%m-%d %H:%M:%S')
              dst = time.localtime(time.mktime(enddate)).tm_isdst #1=y 0=n
              offset = (time.timezone / -3600) if (dst == 0) else (time.altzone / -3600) # timeoffset incl. daylight saving
              offset = datetime.timedelta(hours=offset)
              enddate = datetime.datetime(*enddate[:6])
              enddate += offset
              self.recurrences = [frequency, interval, enddate]
            else:
              self.recurrences = [frequency, interval, count]
          else:
            self.viewE['sv']['btnRecurrences'].tint_color = 'blue'
          alarms = self.detailedEvents[i].valueForKey_('alarms') # list of objects EKAlarm
          if alarms != None:
            self.viewE['sv']['btnAlarms'].tint_color = 'red'
            for alarm in alarms:
              self.alarms.append(int(alarm.relativeOffset()))
          else:
            self.viewE['sv']['btnAlarms'].tint_color = 'blue'
          #color = None
          #temp = str(self.detailedEvents[i].valueForKey_('calendar'))
          #if 'color' in temp:
            #i = temp.index('color')
            #color = temp[i+8:i+15]
          self.viewE['sv']['tfTitle'].text = title
          self.viewE['sv']['tfLocation'].text = location
          self.viewE['sv']['tfUrl'].text = url
          self.viewE['sv']['dpStart'].date = start
          self.viewE['sv']['dpEnd'].date = end
          if allday == '1':
            self.viewE['sv']['dpStart'].mode = ui.DATE_PICKER_MODE_DATE
            self.viewE['sv']['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE
            self.viewE['sv']['swAllday'].value = True

    self.viewE.present('fullscreen')

  def swAllday_click(self, sender):
    if sender.value:
      self.viewE['sv']['dpStart'].mode = ui.DATE_PICKER_MODE_DATE
      self.viewE['sv']['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE
    else:
      self.viewE['sv']['dpStart'].mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
      self.viewE['sv']['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
    self.viewE.set_needs_display()

  def btnRecurrences_click(self, sender):
    self.viewR = ui.load_view('recurrences')
    self.viewR['tfYear'].text = str(self.year)
    self.viewR['tfYear'].action = self.tfYear_click
    self.viewR['slYear'].action = self.slYear_click
    self.viewR['slFrequency'].action = self.slFrequency_click
    self.viewR['tfFrequency'].action = self.tfFrequency_click
    self.viewR['swDay'].action = self.swDay_click
    self.viewR['swWeek'].action = self.swWeek_click
    self.viewR['swMonth'].action = self.swMonth_click
    self.viewR['swYear'].action = self.swYear_click
    self.viewR['btnOkay'].action = self.btnOkayR_click
    self.viewR['btnCancel'].action = self.btnCancel_click
    if self.newEvent:
      self.recurrences = []
    if len(self.recurrences) > 0:
      frequency = self.recurrences[0]
      interval = self.recurrences[1]
      count_date = self.recurrences[2]
      if type(count_date) == int:
        self.viewR['tfCount'].text = str(count_date)
      else:
        self.viewR['dpEnd'].date = count_date
        self.viewR['tfYear'].text = str(count_date)[:4]
        self.viewR['slYear'].value = (int(self.viewR['tfYear'].text) - datetime.datetime.now().year)/10
      self.viewR['tfFrequency'].text = str(interval)
      self.viewR['slFrequency'].value = int(str(interval))/31
      if int(str(frequency)) == 0:
        self.viewR['swDay'].value = True
      elif int(str(frequency)) == 1:
        self.viewR['swWeek'].value = True
      elif int(str(frequency)) == 2:
        self.viewR['swMonth'].value = True
      elif int(str(frequency)) == 3:
        self.viewR['swYear'].value = True
    self.viewR.present('fullscreen')

  def btnAlarms_click(self, sender):
    self.viewA = ui.load_view('alarms')
    self.viewA['btnNoAlarms'].action = self.btnNoAlarms_click
    self.viewA['btnOkay'].action = self.btnOkayA_click
    self.viewA['btnCancel'].action = self.btnCancel_click
    if len(self.alarms) > 0:
      for a in self.alarms:
        if a == 0:
          self.viewA['sw0min'].value = True
        elif a == (-5*60):
          self.viewA['sw5min'].value = True
        elif a == (-15*60):
          self.viewA['sw15min'].value = True
        elif a == (-30*60):
          self.viewA['sw30min'].value = True
        elif a == (-60*60):
          self.viewA['sw1hour'].value = True
        elif a == (-2*60*60):
          self.viewA['sw2hours'].value = True
        elif a == (-24*60*60):
          self.viewA['sw1day'].value = True
    self.viewA.present('fullscreen')

  @ui.in_background
  def btnSave_click(self, sender):
    span = 0
    event = None
    if self.newEvent:
      event = ObjCClass('EKEvent').eventWithEventStore_(self.CE.store)
      if len(self.recurrences) > 0:  #remove recurrences
        event = self.addRecurrenceRule(event)
        span = 1

      if len(self.alarms) > 0:
        for alarm in self.alarms:
          a = ObjCClass('EKAlarm').alarmWithRelativeOffset_(alarm)
          event.addAlarm_(a)
          
    else:  #change an event
      event = self.detailedEvents[self.viewE.eventnumber]
      if len(self.recurrences) > 0:  #remove recurrences
        if event.hasRecurrenceRules():
          recurrenceRule = event.valueForKey_('recurrenceRule')
          event.removeRecurrenceRule(recurrenceRule)
        event = self.addRecurrenceRule(event)

        choice = console.alert('Event is recurrent', 'Modify this instance only?', 'Yes', 'No', hide_cancel_button=True) #yes=1, no=2, cancel=?
        if choice == 2:
          span = 1
      else:  #remove recurrences
        if len(self.recurrences) == 0:
          if event.hasRecurrenceRules():
            recurrenceRule = self.detailedEvents[self.viewE.eventnumber].valueForKey_('recurrenceRule')
            event.removeRecurrenceRule(recurrenceRule)
            choice = console.alert('Event is recurrent', 'Modify this instance only?', 'Yes', 'No', hide_cancel_button=True) #yes=1, no=2, cancel=?
            if choice == 2:
              span = 1

      if len(self.alarms) > 0:  #add alarms
        if event.hasAlarms():
          alarms = event.valueForKey_('alarms')
          for alarm in alarms:
            event.removeAlarm(alarm)
        for alarm in self.alarms:
          a = ObjCClass('EKAlarm').alarmWithRelativeOffset_(alarm)
          event.addAlarm_(a)
          
      else:  #remove all alarms
        if event.hasAlarms():
          alarms = event.valueForKey_('alarms') # list of objects EKAlarm
          for alarm in alarms:
            event.removeAlarm(alarm)

    event.title = self.viewE['sv']['tfTitle'].text
    event.location = self.viewE['sv']['tfLocation'].text
    event.URL = self.viewE['sv']['tfUrl'].text
    event.allDay = c_bool(self.viewE['sv']['swAllday'].value)
    startDate = ObjCClass('NSDate').dateWithTimeIntervalSince1970_(time.mktime(time.strptime(str(self.viewE['sv']['dpStart'].date), '%Y-%m-%d %H:%M:%S')))
    event.startDate = startDate
    endDate = ObjCClass('NSDate').dateWithTimeIntervalSince1970_(time.mktime(time.strptime(str(self.viewE['sv']['dpEnd'].date), '%Y-%m-%d %H:%M:%S')))
    event.endDate = endDate
    event.setCalendar_(self.CE.store.defaultCalendarForNewEvents())
    LP_c_void_p = POINTER(c_void_p)
    err = LP_c_void_p()
    #recurrence: only this event (span=0) / future events (span=1)
    self.CE.store.saveEvent_span_error_(event, span, err)
    self.fill_events()
    self.viewE.close()
    
  def addRecurrenceRule(self, event):
    recurrenceRule = ObjCClass('EKRecurrenceRule').alloc()
    if type(self.recurrences[2]) == int:  #count
      if self.viewE['sv']['swAllday'].value == True:
        end = ObjCClass('EKRecurrenceEnd').recurrenceEndWithOccurrenceCount_(self.recurrences[2]+1)
      else:
        end = ObjCClass('EKRecurrenceEnd').recurrenceEndWithOccurrenceCount_(self.recurrences[2])
    else:  #date
      endDate = ObjCClass('NSDate').dateWithTimeIntervalSince1970_(time.mktime(time.strptime(str(self.recurrences[2])[:20], '%Y-%m-%d %H:%M:%S')))
      end = ObjCClass('EKRecurrenceEnd').recurrenceEndWithEndDate_(endDate)
    recurrenceRule.initRecurrenceWithFrequency_interval_end_(int(str(self.recurrences[0])),int(str(self.recurrences[1])),end)
    event.addRecurrenceRule_(recurrenceRule)
    return event

  def btnCancel_click(self, sender):
    if sender.superview == self.viewE['sv']:
      self.viewE.close()
    else:
      sender.superview.close()

  @ui.in_background
  def btnRemove_click(self, sender):
    span = 0
    event = self.detailedEvents[self.viewE.eventnumber]
    LP_c_void_p = POINTER(c_void_p)
    err = LP_c_void_p()
    if event.hasRecurrenceRules():
      choice = console.alert('Event is recurrent', 'Modify this instance only?', 'Yes', 'No', hide_cancel_button=True) #yes=1, no=2, cancel=?
      if choice == 2:
        span = 1
    #only this event (span=0) / future events (span=1)
    self.CE.store.removeEvent_span_error_(event, span, err)
    self.fill_events()
    self.viewE.close()

  def btnNext_click(self, sender):
    self.viewE.eventnumber += 1
    if self.viewE.eventnumber == self.viewE.eventcount:
      self.viewE.eventnumber = 0
    i = self.viewE.eventnumber
    title = str(self.detailedEvents[i].valueForKey_('title'))
    location = str(self.detailedEvents[i].valueForKey_('location'))
    url = str(self.detailedEvents[i].valueForKey_('URL'))
    allday = str(self.detailedEvents[i].valueForKey_('allDay'))
    start = str(self.detailedEvents[i].valueForKey_('startDate'))[:19]
    end = str(self.detailedEvents[i].valueForKey_('endDate'))[:19]
    start = self.CE.convertDateWithOffset(start)
    end = self.CE.convertDateWithOffset(end)
    if self.detailedEvents[i].hasRecurrenceRules():
      self.viewE['sv']['btnRecurrences'].tint_color = 'red'
      recurrences = self.detailedEvents[i].valueForKey_('recurrenceRule')
      frequency = recurrences.valueForKey_('frequency')
      interval = recurrences.valueForKey_('interval')
      count = recurrences.valueForKey_('count')
      enddate = recurrences.valueForKey_('endDate')
      if count == 0 and enddate is not None:
        self.recurrences = [frequency, interval, enddate]
      else:
        self.recurrences = [frequency, interval, count]
    else:
      self.recurrences = []
      self.viewE['sv']['btnRecurrences'].tint_color = 'blue'
    alarms = self.detailedEvents[i].valueForKey_('alarms') # list of objects EKAlarm
    if alarms != None:
      self.viewE['sv']['btnAlarms'].tint_color = 'red'
      for alarm in alarms:
        self.alarms.append(int(alarm.relativeOffset()))
    else:
      self.viewE['sv']['btnAlarms'].tint_color = 'blue'
      self.alarms = []
    #color = None
    #temp = str(self.detailedEvents[i].valueForKey_('calendar'))
    #if 'color' in temp:
    #i = temp.index('color')
    #color = temp[i+8:i+15]
    self.viewE['sv']['tfTitle'].text = title
    self.viewE['sv']['tfLocation'].text = location
    self.viewE['sv']['tfUrl'].text = url
    self.viewE['sv']['dpStart'].date = start
    self.viewE['sv']['dpEnd'].date = end
    if allday == '1':
      self.viewE['sv']['dpStart'].mode = ui.DATE_PICKER_MODE_DATE
      self.viewE['sv']['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE
      self.viewE['sv']['swAllday'].value = True
    else:
      self.viewE['sv']['dpStart'].mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
      self.viewE['sv']['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
      self.viewE['sv']['swAllday'].value = False

  def btnNoAlarms_click(self, sender):
    self.viewA['sw0min'].value = False
    self.viewA['sw5min'].value = False
    self.viewA['sw15min'].value = False
    self.viewA['sw30min'].value = False
    self.viewA['sw1hour'].value = False
    self.viewA['sw2hours'].value = False
    self.viewA['sw1day'].value = False

  def btnOkayA_click(self, sender):
    self.alarms = []
    if self.viewA['sw0min'].value == True:
      self.alarms.append(0)
    if self.viewA['sw5min'].value == True:
      self.alarms.append(-5*60)
    if self.viewA['sw15min'].value == True:
      self.alarms.append(-15*60)
    if self.viewA['sw30min'].value == True:
      self.alarms.append(-30*60)
    if self.viewA['sw1hour'].value == True:
      self.alarms.append(-60*60)
    if self.viewA['sw2hours'].value == True:
      self.alarms.append(-2*60*60)
    if self.viewA['sw1day'].value == True:
      self.alarms.append(-24*60*60)
    if len(self.alarms) > 0:
      self.viewE['sv']['btnAlarms'].tint_color = 'red'
    else:
      self.viewE['sv']['btnAlarms'].tint_color = 'blue'
    self.viewA.close()

  def slYear_click(self, sender):
    value = int(sender.value * 10)
    self.viewR['tfYear'].text = str(self.year + value)
    changeYear = time.strptime(str(self.year + value) + '-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    changeYear = datetime.datetime(*changeYear[:6])  #convert in datetime
    self.viewR['dpEnd'].date = changeYear

  def tfYear_click(self, sender):
    value = int(self.viewR['tfYear'].text)
    if value >= 2000 and value <= 2100:
      changeYear = time.strptime(str(value) + '-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
      changeYear = datetime.datetime(*changeYear[:6])  #convert in datetime
      self.viewR['dpEnd'].date = changeYear

  def slFrequency_click(self, sender):
    value = int(sender.value / (1/31))
    self.viewR['tfFrequency'].text = str(value)

  def tfFrequency_click(self, sender):
    value = int(self.viewR['tfFrequency'].text)
    if value < 1 and value > 364:
      self.viewR['tfFrequency'].text = '0'

  def btnOkayR_click(self, sender):
    self.recurrences = []
    self.viewE['sv']['btnRecurrences'].tint_color = 'blue'
    interval = int(self.viewR['tfFrequency'].text)
    if interval > 0:
      frequency = None
      if self.viewR['swDay'].value == True:
        frequency = 0
      elif self.viewR['swWeek'].value == True:
        frequency = 1
      elif self.viewR['swMonth'].value == True:
        frequency = 2
      elif self.viewR['swYear'].value == True:
        frequency = 3
      if frequency is not None:
        count = self.viewR['tfCount'].text
        enddate = self.viewR['dpEnd'].date
        now = datetime.datetime.now()
        if count is not '':
          if int(count) == 0:    #=> continue for ever
            self.recurrences = [frequency, interval, None]
            self.viewE['sv']['btnRecurrences'].tint_color = 'red'
          else:
            self.recurrences = [frequency, interval, int(count)]
            self.viewE['sv']['btnRecurrences'].tint_color = 'red'
        elif enddate > now:
          self.recurrences = [frequency, interval, enddate]
          self.viewE['sv']['btnRecurrences'].tint_color = 'red'
      else:
        self.recurrences = []
    self.viewR.close()

  def swDay_click(self, sender):
    self.viewR['swWeek'].value = False
    self.viewR['swMonth'].value = False
    self.viewR['swYear'].value = False

  def swWeek_click(self, sender):
    self.viewR['swDay'].value = False
    self.viewR['swMonth'].value = False
    self.viewR['swYear'].value = False

  def swMonth_click(self, sender):
    self.viewR['swDay'].value = False
    self.viewR['swWeek'].value = False
    self.viewR['swYear'].value = False

  def swYear_click(self, sender):
    self.viewR['swDay'].value = False
    self.viewR['swWeek'].value = False
    self.viewR['swMonth'].value = False

c = Calendarapp()
