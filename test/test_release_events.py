# -*- coding: utf-8 -*-

import unittest
from picard.album import ReleaseEvent


class ReleaseEventTest(unittest.TestCase):

    def test_cmp(self):
        empty_event = ReleaseEvent()
        early_event = ReleaseEvent()
        early_event.date = '1972-05-12'
        later_event = ReleaseEvent()
        later_event.date = '2010-05-23'
        self.assertEqual(empty_event, empty_event)
        self.assertEqual(early_event, early_event)
        self.assertEqual(later_event, later_event)
        self.assertTrue(early_event < empty_event)
        self.assertTrue(later_event < empty_event)
        self.assertTrue(later_event > early_event)
