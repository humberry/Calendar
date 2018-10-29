import ui
import calendar
import datetime
import calendar
from  objc_util import *
from ctypes import POINTER
import threading
import time

class CalendarEvents(object):
  def __init__(self):
    self.store = ObjCClass('EKEventStore').alloc().init()

    access_granted = threading.Event()
    def completion(_self, granted, _error):
      access_granted.set()
    completion_block = ObjCBlock(completion, argtypes=[c_void_p, c_bool, c_void_p])
    self.store.requestAccessToEntityType_completion_(0, completion_block)
    access_granted.wait()

  def getEvents(self, start, end):
    startDate = ObjCClass('NSDate').dateWithTimeIntervalSince1970_(time.mktime(time.strptime(start, '%Y-%m-%d %H:%M:%S')))
    endDate = ObjCClass('NSDate').dateWithTimeIntervalSince1970_(time.mktime(time.strptime(end, '%Y-%m-%d %H:%M:%S')))

    predicate = self.store.predicateForEventsWithStartDate_endDate_calendars_(startDate, endDate, None)
    events = self.store.eventsMatchingPredicate_(predicate)

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
      start, end = self.convertDate(start, end)
      list.append([allday, start, end, title, color])
    return list
    
  def convertDate(self, start, end):
    start = time.strptime(start, '%Y-%m-%d %H:%M:%S')
    end = time.strptime(end, '%Y-%m-%d %H:%M:%S')
    dsts = time.localtime(time.mktime(start)).tm_isdst #1=y 0=n
    dste = time.localtime(time.mktime(end)).tm_isdst #1=y 0=n
    offsets = (time.timezone / -3600) if (dsts == 0) else (time.altzone / -3600) # timeoffset incl. daylight saving
    offsete = (time.timezone / -3600) if (dste == 0) else (time.altzone / -3600) # timeoffset incl. daylight saving
    start = datetime.datetime(*start[:6])
    end = datetime.datetime(*end[:6])
    offsets = datetime.timedelta(hours=offsets)
    offsete = datetime.timedelta(hours=offsete)
    start += offsets
    end += offsete
    return [start, end]
    
  def getDetailedEvents(self, start, end):
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
    ev = self.CE.getEvents(str(self.year) + '-' + str(self.month) + '-01 00:00:01', str(self.year) + '-' + str(self.month) + '-' + str(self.last_day) + ' 23:59:59')
    for e in ev:
      #list.append([allday, start, end, title, color])

      if (e[0] == '1' and str(e[1])[:10] == str(e[2])[:10]):
        self.events[int(str(e[1])[8:10])-1].append([e[3], e[4]])  #all day (no time) and start day == end day
      elif (e[0] == '0' and str(e[1])[:10] == str(e[2])[:10]):  # timespan and start day == end day
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
            self.events[i].append([str(e[1])[:5] + ' ' + e[3], e[4]])  #[start time + title, color]
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
    self.view2 = ui.load_view('event')
    self.view2['btnSave'].action = self.btnSave_click
    self.view2['btnSave'].enabled = False
    self.view2['btnCancel'].action = self.btnCancel_click
    self.view2['btnRemove'].action = self.btnRemove_click
    self.view2['btnRemove'].enabled = False
    self.view2['btnNext'].action = self.btnNext_click
    self.view2['btnNext'].enabled = False
    self.view2['swAllday'].action = self.swAllday_click
    self.view2['swYearly'].enabled = False
    self.view2['swMonthly'].enabled = False
    self.view2['swWeekly'].enabled = False
    self.view2['swNone'].enabled = False
    self.view2['sw0min'].enabled = False
    self.view2['sw5min'].enabled = False
    self.view2['sw15min'].enabled = False
    self.view2['sw1hour'].enabled = False
    self.view2['sw1day'].enabled = False

    if text == 'NEW':
      currentTime = str(time.localtime().tm_hour) + ':' + str(time.localtime().tm_min) + ':' + str(time.localtime().tm_sec)
      selectedDate = time.strptime(str(self.year) + '-' + str(self.month) + '-' + str(row+1) + ' ' + currentTime, '%Y-%m-%d %H:%M:%S')
      selectedDate = datetime.datetime(*selectedDate[:6])  #convert in datetime
      self.view2['dpStart'].date = selectedDate
      self.view2['dpEnd'].date = selectedDate
    else:
      if text[:2].isdigit() and text[2] == ':' and text[3:5].isdigit():  #starttime
        text = text[6:]
      start = str(self.year) + '-' + str(self.month) + '-' + str(row+1) + ' 00:00:00'
      end = str(self.year) + '-' + str(self.month) + '-' + str(row+1) + ' 23:59:59'
      self.detailedEvents = self.CE.getDetailedEvents(start, end)
      if len(self.detailedEvents) > 1:
        self.view2['btnNext'].enabled = True
        self.view2.eventcount = len(self.detailedEvents)
      i = 0
      for i in range(len(self.detailedEvents)):
        title = str(self.detailedEvents[i].valueForKey_('title'))
        if title == text:
          self.view2.eventnumber = i
          location = str(self.detailedEvents[i].valueForKey_('location'))
          url = str(self.detailedEvents[i].valueForKey_('URL'))
          allday = str(self.detailedEvents[i].valueForKey_('allDay'))
          start = str(self.detailedEvents[i].valueForKey_('startDate'))[:19]
          end = str(self.detailedEvents[i].valueForKey_('endDate'))[:19]
          start, end = self.CE.convertDate(start, end)
          #recurrence = self.detailedEvents[i].valueForKey_('recurrence')
          #alarms = self.detailedEvents[i].valueForKey_('alarms')
          #color = None
          #temp = str(self.detailedEvents[i].valueForKey_('calendar'))
          #if 'color' in temp:
            #i = temp.index('color')
            #color = temp[i+8:i+15]
          self.view2['tfTitle'].text = title
          self.view2['tfLocation'].text = location
          self.view2['tfUrl'].text = url
          self.view2['dpStart'].date = start
          self.view2['dpEnd'].date = end
          if allday == '1':
            self.view2['dpStart'].mode = ui.DATE_PICKER_MODE_DATE
            self.view2['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE
            self.view2['swAllday'].value = True
          
    self.view2.present('fullscreen')
    
  def swAllday_click(self, sender):
    if sender.value:
      self.view2['dpStart'].mode = ui.DATE_PICKER_MODE_DATE
      self.view2['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE
    else:
      self.view2['dpStart'].mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
      self.view2['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
    
  def btnSave_click(self, sender):
    pass
    
  def btnCancel_click(self, sender):
    self.view2.close()
    
  def btnRemove_click(self, sender):
    pass
    
  def btnNext_click(self, sender):
    self.view2.eventnumber += 1
    if self.view2.eventnumber == self.view2.eventcount:
      self.view2.eventnumber = 0
    i = self.view2.eventnumber
    title = str(self.detailedEvents[i].valueForKey_('title'))
    location = str(self.detailedEvents[i].valueForKey_('location'))
    url = str(self.detailedEvents[i].valueForKey_('URL'))
    allday = str(self.detailedEvents[i].valueForKey_('allDay'))
    start = str(self.detailedEvents[i].valueForKey_('startDate'))[:19]
    end = str(self.detailedEvents[i].valueForKey_('endDate'))[:19]
    start, end = self.CE.convertDate(start, end)
    #recurrence = self.detailedEvents[i].valueForKey_('recurrence')
    #alarms = self.detailedEvents[i].valueForKey_('alarms')
    #color = None
    #temp = str(self.detailedEvents[i].valueForKey_('calendar'))
    #if 'color' in temp:
      #i = temp.index('color')
      #color = temp[i+8:i+15]
    self.view2['tfTitle'].text = title
    self.view2['tfLocation'].text = location
    self.view2['tfUrl'].text = url
    self.view2['dpStart'].date = start
    self.view2['dpEnd'].date = end
    if allday == '1':
      self.view2['dpStart'].mode = ui.DATE_PICKER_MODE_DATE
      self.view2['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE
      self.view2['swAllday'].value = True
    else:
      self.view2['dpStart'].mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
      self.view2['dpEnd'].mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
      self.view2['swAllday'].value = False
    
c = Calendarapp()
