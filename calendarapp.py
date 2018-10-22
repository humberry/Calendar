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
      start = time.strptime(start, '%Y-%m-%d %H:%M:%S')
      dst = time.localtime(time.mktime(start)).tm_isdst #1=y 0=n
      offset = (time.timezone / -3600) if (dst == 0) else (time.altzone / -3600) # timeoffset incl. daylight saving
      start = datetime.datetime(*start[:6])
      offset = datetime.timedelta(hours=offset)
      start += offset
      starttime = start.time()
      startdate = start.date()

      if allday == '1':
        list.append([int(str(startdate)[8:10]), title])
      else:
        list.append([int(str(startdate)[8:10]), str(starttime)[:5] + ' ' + title])
    return list

class MyButtonClass(ui.View):
  def __init__(self, x, y, h, w, color, text, align):
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
    self.add_subview(self.label)

  def touch_began(self, touch):
    self.label.text_color = 'black'
    print('tapped ' + str(self.label.text))

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
    for i in range(len(tableview.data_source.items[row])):
        self.make_labels(cell, tableview.data_source.items[row][i], i)
    return cell
  
  def make_labels(self, cell, text, pos):
    if pos == 0:  # M, T, W, T, F, S, S
      label = ui.Label(frame=(0, 0, 20, 23))
      label.text = str(text)
      label.alignment = ui.ALIGN_CENTER
      label.frame = (5, 0, 20, self.row_height)
      if text == 'S':
        label.text_color = 'red'
      else:
        label.text_color = 'black'
    elif pos == 1:  # 1 - 31
      label = ui.Label(frame=(0, 0, 20, 23))
      label.text = str(text)
      label.text_color = 'black'
      label.alignment = ui.ALIGN_CENTER
      label.frame = (30, 0, 25, self.row_height)
    elif pos == 2:  # NEW
      label = MyButtonClass(60, 0, self.row_height - 1, 40, 'darkred', text, ui.ALIGN_CENTER)
    elif pos > 2:  # Events
      label = MyButtonClass(160*(pos-3)+105, 0, self.row_height - 1, 155, 'blue', text, ui.ALIGN_LEFT)
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
    for i in range(self.last_day):
      daylist = [self.day_list[weekday], str(i+1), 'NEW']
      self.events.append(daylist)
      weekday += 1
      if weekday > 6:
        weekday = 0
    ev = self.CE.getEvents(str(self.year) + '-' + str(self.month) + '-01 00:00:01', str(self.year) + '-' + str(self.month) + '-' + str(self.last_day) + ' 23:59:59')
    #print(ev)
    for e in ev:
      self.events[e[0]-1].append(e[1])
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

Calendarapp()
