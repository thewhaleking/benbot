#!/usr/bin/env python3
#
# Uber, Inc. 2019
#
__author__ = 'bhimes@uber.com'

import datetime
import sys
import unittest

from benbot import benbot5


class TestBenbot(unittest.TestCase):

    def test_strip_extra_newlines(self):
        test_string = """
        This is 
        
        a test string
        
        with multiple
        linebreaks
        """
        expected_result = [
            "        This is",
            "        a test string",
            "        with multiple",
            "        linebreaks"
        ]
        actual_result = benbot5.strip_extra_newlines(test_string)
        self.assertEqual(actual_result, expected_result)

    def test_parse_for_day(self):
        test_string = """
        MONDAY ~ 
        06/17
        BEET & GOAT CHEESE SALAD - vegetarian
        (contains nuts & dairy)
        BROWN RICE - vegan
        GYROS
        pita, cucumber dill sauce, lettuce, tomato
        (contains lamb & beef; pita contains gluten)  
        VEGAN "MEATBALL" SUB - vegan
        (contains soy & gluten; bread contains gluten)
        PASSION FRUIT BARS - vegetarian
        (contains dairy, egg, & gluten)
        TUESDAY ~
        06/18
        FRUIT SALAD - vegan
        RANCH SEASONED POTATO CHIPS - vegetarian
        (contains dairy & soy)
        HAMBURGERS & CHEESEBURGERS
        tomato, red onion, lettuce, American cheese
        (contains beef; buns contain sesame & gluten)
        SUPA DE POLLO
        (contains gluten & chicken)
        "THE BEYOND BURGER" - vegan
        lettuce, tomato, red onion, secret sauce
        (buns contain sesame & gluten)
        RED VELVET CUPCAKES - vegetarian
        (contains dairy, egg, & gluten
        """
        expected_result = (
            '06/17\n'
            'BEET & GOAT CHEESE SALAD - vegetarian\n'
            '(contains nuts & dairy)\n'
            'BROWN RICE - vegan\n'
            'GYROS\n'
            'pita, cucumber dill sauce, lettuce, tomato\n'
            '(contains lamb & beef; pita contains gluten)\n'
            'VEGAN "MEATBALL" SUB - vegan\n'
            '(contains soy & gluten; bread contains gluten)\n'
            'PASSION FRUIT BARS - vegetarian\n'
            '(contains dairy, egg, & gluten)\n'
        )

        self.assertEqual(expected_result, benbot5.parse_for_day(test_string, 'MONDAY'))

    def test_parse_meal(self):
        test_string = (
            'MONDAY ~ \n'
            '06/17\n'
            'BEET & GOAT CHEESE SALAD - vegetarian\n'
            '(contains nuts & dairy)\n'
            'BROWN RICE - vegan\n'
            'GYROS\n'
            'pita, cucumber dill sauce, lettuce, tomato\n'
            '(contains lamb & beef; pita contains gluten)  \n'
            'VEGAN "MEATBALL" SUB - vegan\n'
            '(contains soy & gluten; bread contains gluten)\n'
            'PASSION FRUIT BARS - vegetarian\n'
            '(contains dairy, egg, & gluten)\n'
            'TUESDAY ~\n'
            '06/18\n'
            'FRUIT SALAD - vegan\n'
            'RANCH SEASONED POTATO CHIPS - vegetarian\n'
            '(contains dairy & soy)\n'
            'HAMBURGERS & CHEESEBURGERS\n'
            'tomato, red onion, lettuce, American cheese\n'
            '(contains beef; buns contain sesame & gluten)\n'
            'SUPA DE POLLO\n'
            '(contains gluten & chicken)\n'
            '"THE BEYOND BURGER" - vegan\n'
            'lettuce, tomato, red onion, secret sauce\n'
            '(buns contain sesame & gluten)\n'
            'RED VELVET CUPCAKES - vegetarian\n'
            '(contains dairy, egg, & gluten\n'
            '\n'
        )
        expected_result_0 = {'MONDAY':
                                 '*MONDAY*\n06/17\nBEET & GOAT CHEESE SALAD - vegetarian'
                                 '\n(contains nuts & dairy)\nBROWN RICE - vegan\nGYROS\npita, cucumber dill sauce, '
                                 'lettuce, tomato\n(contains lamb & beef; pita contains gluten)\nVEGAN "MEATBALL" '
                                 'SUB - vegan\n(contains soy & gluten; bread contains gluten)\nPASSION FRUIT BARS - '
                                 'vegetarian\n(contains dairy, egg, & gluten)\n',
                             'TUESDAY':
                                 '*TUESDAY*\n06/18\nFRUIT SALAD - vegan\nRANCH SEASONED POTATO CHIPS - '
                                 'vegetarian\n(contains dairy & soy)\nHAMBURGERS & CHEESEBURGERS\ntomato, red onion, '
                                 'lettuce, American cheese\n(contains beef; buns contain sesame & gluten)\nSUPA DE '
                                 'POLLO\n(contains gluten & chicken)\n"THE BEYOND BURGER" - vegan\nlettuce, tomato, '
                                 'red onion, secret sauce\n(buns contain sesame & gluten)\nRED VELVET CUPCAKES - '
                                 'vegetarian\n(contains dairy, egg, & gluten\n',
                             'WEDNESDAY':
                                 '',
                             'THURSDAY':
                                 '',
                             'FRIDAY':
                                 ''}
        test_result = benbot5.parse_meal(test_string)
        self.assertEqual(expected_result_0, test_result[0])
        self.assertIn(datetime.datetime(2019, 6, 17, 0, 0), test_result[1])
        self.assertIn(datetime.datetime(2019, 6, 18, 0, 0), test_result[1])


def suite():
    functions_suite = unittest.TestLoader().loadTestsFromTestCase(TestBenbot)
    return unittest.TestSuite([functions_suite])


if __name__ == "__main__":
    text_test_result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(0 if text_test_result.wasSuccessful() else 1)
