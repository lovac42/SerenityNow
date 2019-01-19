# -*- coding: utf-8 -*-
# Copyright: (C) 2018 Lovac42
# Support: https://github.com/lovac42/SerenityNow
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Version: 0.0.6


from aqt import mw
from anki.hooks import wrap
from anki.sched import Scheduler
from aqt.utils import showWarning, showText
import random


#Turn this on if you are having problems.
def debugInfo(msg):
    # print(msg) #console
    # showText(msg) #Windows
    return



#FROM: Anki sched v1 (src 2.0.52)
#MOD: added priority
def fillRev(self, _old):
    if self._revQueue:
        return True
    if not self.revCount:
        return False

    if self.col.sched.name=="std2":
        return _old(self)


    # This seem like old comments left behind, and does not affect current versions.
    # Remove these lines for testing
    if self.col.decks.get(self.col.decks.selected(),False)['dyn']:
        # dynamic decks need due order preserved
        return _old(self)


    qc = self.col.conf
    if not qc.get("serenityNow",0) or qc.get("hoochieMama",0):
        return _old(self)
    debugInfo('using serenityNow')


    while self._revDids:
        did = self._revDids[0]
        lim = min(self.queueLimit, self._deckRevLimit(did))
        if lim:

            # fill the queue with the current did
            self._revQueue = self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due = ? 
limit ?""", did, self.today, lim)

            if not self._revQueue:
                self._revQueue = self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due = ? 
limit ?""", did, self.today-1 , lim)

            if not self._revQueue:
                self._revQueue = self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due <= ? 
limit ?""", did, self.today-2 , lim)

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


def setupUi(self, Preferences):
    try:
        grid=self.lrnStageGLayout
    except AttributeError:
        self.lrnStage=QtWidgets.QWidget()
        self.tabWidget.addTab(self.lrnStage, "Muffins")
        self.lrnStageGLayout=QtWidgets.QGridLayout()
        self.lrnStageVLayout=QtWidgets.QVBoxLayout(self.lrnStage)
        self.lrnStageVLayout.addLayout(self.lrnStageGLayout)
        spacerItem=QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.lrnStageVLayout.addItem(spacerItem)

    r=self.lrnStageGLayout.rowCount()
    self.serenityNow = QtWidgets.QCheckBox(self.lrnStage)
    self.serenityNow.setText(_('Serenity Now! Prioritize Today, Yest, OD'))
    self.lrnStageGLayout.addWidget(self.serenityNow, r, 0, 1, 3)
    self.serenityNow.toggled.connect(lambda:toggle(self))


def load(self, mw):
    qc = self.mw.col.conf
    cb=qc.get("serenityNow", 0)
    self.form.serenityNow.setCheckState(cb)
    toggle(self.form)


def save(self):
    toggle(self.form)
    qc = self.mw.col.conf
    qc['serenityNow']=self.form.serenityNow.checkState()


def toggle(self):
    checked=self.serenityNow.checkState()
    if checked:
        try:
            self.hoochieMama.setCheckState(0)
        except: pass


aqt.forms.preferences.Ui_Preferences.setupUi = wrap(aqt.forms.preferences.Ui_Preferences.setupUi, setupUi, "after")
aqt.preferences.Preferences.__init__ = wrap(aqt.preferences.Preferences.__init__, load, "after")
aqt.preferences.Preferences.accept = wrap(aqt.preferences.Preferences.accept, save, "before")
