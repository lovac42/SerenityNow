# -*- coding: utf-8 -*-
# Copyright: (C) 2018 Lovac42
# Support: https://github.com/lovac42/SerenityNow
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Version: 0.0.2


#configs:
LOADBAL_DAYS = 3  #Study n days ahead
LOADBAL_IVL = 50  #Nothing less than x ivl


from aqt import mw
from anki.hooks import wrap
from anki.sched import Scheduler
from aqt.reviewer import Reviewer
from aqt.utils import showWarning, showText
import random


def fillRev(self, _old): #copied and modded from Anki-2.0.52 src
    if self._revQueue:
        return True
    if not self.revCount:
        return False
    while self._revDids:
        did = self._revDids[0]
        lim = min(self.queueLimit, self._deckRevLimit(did))
        if lim:

            # fill the queue with the current did
            self._revQueue = self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due = ? limit ?""", did, self.today, lim)


            #Avoid using a loop in case we run out of reviews
            qsize=lim-len(self._revQueue)
            if qsize > 0:
                self._revQueue.extend(self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due = ? limit ?""", did, self.today-1, qsize))


                qsize=lim-len(self._revQueue)
                if qsize > 0:
                    self._revQueue.extend(self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due <= ? limit ?""", did, self.today-2, qsize))


                    # Study ahead to load balance reviews
                    # Shouldn't affect too much with a high enough ivl
                    qsize=lim-len(self._revQueue)
                    if qsize > 0: # Not likely to happend for lazy slackers ;)
                        self._revQueue.extend(self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due <= ? and ivl >= ? limit ?""",
            did, self.today + LOADBAL_DAYS, LOADBAL_IVL, qsize))


            if self._revQueue:
                # ordering
                if self.col.decks.get(did)['dyn']:
                    # dynamic decks need due order preserved
                    self._revQueue.reverse()
                else:
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


#Decrease new card limit for each forgotten review card
def rescheduleLapse(self, card):
    self._updateStats(card, 'new')

#Ensure new cards comes last after review cards
def timeForNewCard(self, _old): return False

Scheduler._timeForNewCard = wrap(Scheduler._timeForNewCard, timeForNewCard, 'around')
Scheduler._fillRev = wrap(Scheduler._fillRev, fillRev, 'around')
Scheduler._rescheduleLapse = wrap(Scheduler._rescheduleLapse, rescheduleLapse, 'after')
