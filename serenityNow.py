# -*- coding: utf-8 -*-
# Copyright: (C) 2018 Lovac42
# Support: https://github.com/lovac42/SerenityNow
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Version: 0.0.5


# == User Config =========================================

LOADBAL_DAYS  = 0    #Study n days ahead, 0 to disable.
LOADBAL_IVL   = 365  #Nothing less than x ivl
MAX_PREREVIEW = 5    #Cap pre-reviews

# == End Config ==========================================
##########################################################


from aqt import mw
from anki.hooks import wrap
from anki.sched import Scheduler
from aqt.utils import showWarning, showText
import random


def fillRev(self, _old): #copied and modded from Anki-2.0.52 src
    if self._revQueue:
        return True
    if not self.revCount:
        return False


    # This seem like old comments left behind, and does not affect current versions.
    # Remove these lines for testing
    if self.col.decks.get(self.col.decks.selected(),False)['dyn']:
        # dynamic decks need due order preserved
        return _old(self)


    qc = self.col.conf
    if not qc.get("serenityNow", False):
        return _old(self)
    # print('using serenityNow')


    while self._revDids:
        did = self._revDids[0]
        lim = min(self.queueLimit, self._deckRevLimit(did))
        if lim:

            # fill the queue with the current did
            self._revQueue = self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due = ? limit ?""", did, self.today, lim)


            #Avoid using a loop in case we run out of reviews
            more=lim-len(self._revQueue)
            if more:
                self._revQueue.extend(self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due = ? limit ?""", did, self.today-1, more))


                more=lim-len(self._revQueue)
                if more:
                    self._revQueue.extend(self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due <= ? limit ?""", did, self.today-2, more))


                    # Study ahead to load balance reviews
                    # Shouldn't affect too much with a high enough ivl
                    qsize=lim-len(self._revQueue)
                    if LOADBAL_DAYS and qsize > 0: # Not likely to happend for lazy slackers ;)
                        qsize=min(MAX_PREREVIEW,qsize)
                        self._revQueue.extend(self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due <= ? and ivl >= ? limit ?""",
            did, self.today + LOADBAL_DAYS, LOADBAL_IVL, qsize))


            if self._revQueue:
                # random order for regular reviews
                r = random.Random()
                r.seed(self.today)
                r.shuffle(self._revQueue)
                # is the current did empty?
                if len(self._revQueue) < lim:
                    self._revDids.pop(0)
                return True
        # nothing left in the deck; move to next
        self._revDids.pop(0)
    if self.revCount:
        # if we didn't get a card but the count is non-zero,
        # we need to check again for any cards that were
        # removed from the queue but not buried
        self._resetRev()
        return self._fillRev()


Scheduler._fillRev = wrap(Scheduler._fillRev, fillRev, 'around')


##################################################
#
#  GUI stuff, adds preference menu options
#
#################################################
import aqt
import aqt.preferences
from aqt.qt import *

from anki import version
ANKI21 = version.startswith("2.1.")
if ANKI21:
    from PyQt5 import QtCore, QtGui, QtWidgets
else:
    from PyQt4 import QtCore, QtGui as QtWidgets

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

def setupUi(self, Preferences):
    r=self.gridLayout_4.rowCount()
    self.serenityNow = QtWidgets.QCheckBox(self.tab_1)
    self.serenityNow.setObjectName(_fromUtf8("Serenity Now"))
    self.serenityNow.setText(_('Serenity Now! Prioritize Today, Yest, OD'))
    self.serenityNow.toggled.connect(lambda:toggle(self))
    self.gridLayout_4.addWidget(self.serenityNow, r, 0, 1, 3)

def __init__(self, mw):
    qc = self.mw.col.conf
    cb=qc.get("serenityNow", 0)
    self.form.serenityNow.setCheckState(cb)

def accept(self):
    qc = self.mw.col.conf
    qc['serenityNow']=self.form.serenityNow.checkState()

def toggle(self):
    checked=not self.serenityNow.checkState()==0
    if checked:
        try:
            self.hoochieMama.setCheckState(0)
        except: pass

aqt.forms.preferences.Ui_Preferences.setupUi = wrap(aqt.forms.preferences.Ui_Preferences.setupUi, setupUi, "after")
aqt.preferences.Preferences.__init__ = wrap(aqt.preferences.Preferences.__init__, __init__, "after")
aqt.preferences.Preferences.accept = wrap(aqt.preferences.Preferences.accept, accept, "before")
